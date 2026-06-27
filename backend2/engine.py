import random
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from backend2.models import (DocumentRequest, StaffMember)
from backend2.rules import (_soft_cap, _duration_to_schedule, COLLEGE_PRIORITY)
from backend2.roc_utils import (PRIORITY_ROC_WEIGHTS_BASE, PRIORITY_ROC_WEIGHTS_FULL,)

from backend2.config import (
REQUESTER_PRIORITY, 
REQUESTER_PRIORITY_MAX, 
DOCUMENT_COMPLEXITY, 
PRIORITY_SCORE_HALF_LIFE, 
PRIORITY_WEIGHTS, 
COLLEGE_POPULATION, 
REQUESTER_GENERATION_WEIGHTS, 
COLLEGES, 
REQUIREMENTS_COMPLETE_EXTRA_DELAY_HOURS_RANGE, 
REQUIREMENTS_PARTIAL_DELAY_HOURS_RANGE, 
DOCUMENT_REQUESTER_RESTRICTIONS, 
DOCUMENT_PAYMENT_REQUIRED, 
PAYMENT_DELAY_HOURS_RANGE,
)


def calculate_priority(request, current_time, weights, workday_minutes, urgency=False) -> float:
    """Compute weighted priority score for this request at current_time."""

    request.update_status(current_time)

    completeness_norm = max(0.0, min(float(request.completeness_of_requirements), 1.0))

    requester_raw = REQUESTER_PRIORITY.get(request.requester_type, 3)
    requester_norm = requester_raw / max(float(REQUESTER_PRIORITY_MAX), 1.0)

    waiting_minutes = max(
        0.0,
        (current_time - request.submission_time).total_seconds() / 60.0,
    )
    submission_norm = _soft_cap(waiting_minutes, max(float(workday_minutes * 2), 1.0))

    base_duration, _ = _duration_to_schedule(
        DOCUMENT_COMPLEXITY.get(request.document_type, 1)
    )
    complexity_days = max(base_duration.total_seconds() / 86400.0, 1e-6)
    doc_norm = 1.0 / (1.0 + complexity_days)

    college_norm = float(COLLEGE_PRIORITY.get(request.college, 0.5))

    payment_norm = 0.0
    if isinstance(request.payment_status, str):
        status_text = request.payment_status.strip().lower()
        if status_text in {"paid", "settled", "complete", "cleared", "yes", "y", "true", "1"}:
            payment_norm = 1.0
    else:
        payment_norm = 1.0 if bool(request.payment_status) else 0.0

    urgency_norm = float(request.urgency) / 10.0 if urgency else 0.0

    scores = {
        "completeness_of_requirements": completeness_norm,
        "submission_time": submission_norm,
        "document_type": doc_norm,
        "requester_status": requester_norm,
        "college_affiliation": college_norm,
        "payment_status": payment_norm,
        "urgency": urgency_norm
    }

    total_score = 0.0
    for key, weight in weights.items():
        if key == "urgency" and not urgency:
            continue
        total_score += float(weight) * scores.get(key, 0.0)

    request.priority_score = _soft_cap(total_score, PRIORITY_SCORE_HALF_LIFE)
    return request.priority_score

# ============================================================================
# SCHEDULERS (kept for structural clarity)
# ============================================================================

class FCFSScheduler:
    def __init__(self):
        self.queue: List[DocumentRequest] = []

    def add_request(self, request: DocumentRequest):
        self.queue.append(request)

    def get_all_sorted(self) -> List[DocumentRequest]:
        sorted_queue = sorted(self.queue, key=lambda r: r.submission_time)
        self.queue.clear()
        return sorted_queue


class WeightedPriorityScheduler:
    def __init__(self):
        self.pending: List[DocumentRequest] = []

    def add_request(self, request: DocumentRequest):
        self.pending.append(request)

    def remove_request(self, request: DocumentRequest):
        self.pending.remove(request)

    def rank(
        self,
        current_time: datetime,
        weights: Dict[str, float],
        workday_minutes: int,
        urgency: bool = False,
    ) -> List[DocumentRequest]:

        for req in self.pending:
            req.priority_score = calculate_priority(
                req,
                current_time,
                weights,
                workday_minutes,
                urgency,
            )

        return sorted(
            self.pending,
            key=lambda r: (-r.priority_score, r.submission_time),
        )
    

# ============================================================================
# SIMULATION ENGINE
# ============================================================================

class SimulationEngine:
    def __init__(
        self,
        scheduler_type: str,
        allocator_type: str,
        staff_config: Optional[Dict] = None,
        priority_weights: Optional[Dict[str, float]] = None,
        random_seed: Optional[int] = None,
        work_start: str = "08:00",
        work_end: str = "17:00",
        urgency: bool = False,
    ):
        self.scheduler_type = (scheduler_type or "FCFS").upper().strip()
        self.allocator_type = (allocator_type or "college_based").strip().lower()

        # Record whether urgency is enabled early so normalization can act on it.
        self.urgency = urgency

        # Select default ROC weight set: by default use the base (6 criteria).
        # If the caller explicitly provided `priority_weights`, respect that.
        if priority_weights is None:
            default_weights = PRIORITY_ROC_WEIGHTS_FULL if self.urgency else PRIORITY_ROC_WEIGHTS_BASE
        else:
            default_weights = priority_weights

        # Normalize the chosen weight set (this will also drop 'urgency' if
        # urgency is disabled and an 'urgency' key exists in the provided dict).
        self.priority_weights = self._normalize_weights(default_weights)

        self.work_start_minutes = self._parse_clock_minutes(work_start, 8 * 60)
        self.work_end_minutes = self._parse_clock_minutes(work_end, 17 * 60)
        if self.work_end_minutes <= self.work_start_minutes:
            self.work_start_minutes = 8 * 60
            self.work_end_minutes = 17 * 60
        self.workday_minutes = self.work_end_minutes - self.work_start_minutes

        if random_seed is None:
            random_seed = random.SystemRandom().randint(1, 10**9)
        self.random_seed = int(random_seed)
        self.rng = random.Random(self.random_seed)

        self.staff_config = staff_config or {}
        self.staff_pool = self._generate_staff_pool(
            num_staff=self.staff_config.get("num_staff", 6),
            quota_limit=self.staff_config.get("quota_limit", 20),
        )

        self.scheduler = FCFSScheduler() if self.scheduler_type == "FCFS" else WeightedPriorityScheduler()

        self.start_time = self._default_day_start(datetime.now())
        self.scenario = "baseline"
        self.completed: List[DocumentRequest] = []
        self.waiting_queue: List[DocumentRequest] = []
        self.generated_requests: List[DocumentRequest] = []

        self.event_log: List[Dict] = []
        self._event_seq = 0
        self.absent_staff_ids: List[str] = []
        

# ---------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------

    def _parse_clock_minutes(self, raw_value: str, fallback_minutes: int) -> int:
        if not isinstance(raw_value, str) or ":" not in raw_value:
            return fallback_minutes
        try:
            hour_text, minute_text = raw_value.strip().split(":", 1)
            hour = int(hour_text)
            minute = int(minute_text)
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                return fallback_minutes
            return hour * 60 + minute
        except Exception:
            return fallback_minutes

    def _clock_string(self, total_minutes: int) -> str:
        hour = total_minutes // 60
        minute = total_minutes % 60
        return f"{hour:02d}:{minute:02d}"

    def _default_day_start(self, dt: datetime) -> datetime:
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    def _day_start(self, day: date) -> datetime:
        h = self.work_start_minutes // 60
        m = self.work_start_minutes % 60
        return datetime.combine(day, datetime.min.time()).replace(hour=h, minute=m)

    def _day_end(self, day: date) -> datetime:
        h = self.work_end_minutes // 60
        m = self.work_end_minutes % 60
        return datetime.combine(day, datetime.min.time()).replace(hour=h, minute=m)

    def _next_working_start(self, dt: datetime) -> datetime:
        day_start = self._day_start(dt.date())
        day_end = self._day_end(dt.date())
        if dt < day_start:
            return day_start
        if dt >= day_end:
            return self._day_start(dt.date() + timedelta(days=1))
        return dt

    def _add_processing_with_work_hours(self, start_dt: datetime, duration: timedelta) -> datetime:
        remaining_seconds = max(duration.total_seconds(), 0.0)
        current = self._next_working_start(start_dt)

        while remaining_seconds > 0:
            day_end = self._day_end(current.date())
            available_seconds = max((day_end - current).total_seconds(), 0.0)

            if available_seconds <= 0:
                current = self._day_start(current.date() + timedelta(days=1))
                continue

            chunk = min(available_seconds, remaining_seconds)
            current = current + timedelta(seconds=chunk)
            remaining_seconds -= chunk

            if remaining_seconds > 0:
                current = self._day_start(current.date() + timedelta(days=1))

        return current

# ---------------------------------------------------------------------
# Core setup helpers
# ---------------------------------------------------------------------

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        # Work on a copy so caller dict isn't mutated
        src = dict(weights or {})

        # If urgency is not enabled for this engine, ignore any supplied
        # 'urgency' key so normalization only covers the active criteria.
        if not getattr(self, "urgency", False) and "urgency" in src:
            src.pop("urgency")

        # Preserve canonical ordering from PRIORITY_WEIGHTS when possible.
        canonical_keys = [k for k in PRIORITY_WEIGHTS.keys() if k in src]
        # Append any non-canonical keys the user provided.
        other_keys = [k for k in src.keys() if k not in canonical_keys]
        keys = canonical_keys + other_keys

        clean: Dict[str, float] = {}
        for key in keys:
            try:
                raw = float(src.get(key, 0.0))
            except Exception:
                raw = 0.0
            clean[key] = max(raw, 0.0)

        total = sum(clean.values())
        if total <= 0:
            # Fallback: use PRIORITY_WEIGHTS but also remove urgency if disabled.
            fallback = dict(PRIORITY_WEIGHTS)
            if not getattr(self, "urgency", False) and "urgency" in fallback:
                fallback.pop("urgency")
            ftotal = sum(float(v) for v in fallback.values())
            if ftotal <= 0:
                return fallback
            return {k: float(v) / ftotal for k, v in fallback.items()}

        return {k: v / total for k, v in clean.items()}

    def _is_request_ready(self, request: DocumentRequest, current_time: datetime) -> bool:
        request.update_status(current_time)
        if request.ready_time is None:
            return True
        return current_time >= request.ready_time

    def _generate_staff_pool(self, num_staff: int, quota_limit: int) -> List[StaffMember]:
        names = [
            "Marco",
            "Liza",
            "Paolo",
            "Nina",
            "Carlo",
            "Ana",
            "Ramon",
            "Elena",
            "Miguel",
            "Sara",
            "Leo",
            "Jade",
            "Ivan",
            "Karla",
        ]

        max_staff = max(len(COLLEGES) * 2, 1)
        count = max(1, min(int(num_staff), max_staff))
        quota = max(1, int(quota_limit))

        pool = []
        for index in range(count):
            pool.append(
                StaffMember(
                    staff_id=f"STAFF{index + 1:03d}",
                    name=names[index % len(names)],
                    college_affiliation=COLLEGES[index % len(COLLEGES)],
                    quota_limit=quota,
                )
            )
        return pool

    def _reset_for_run(self):
        self.completed = []
        self.waiting_queue = []
        self.generated_requests = []
        self.event_log = []
        self._event_seq = 0
        self.absent_staff_ids = []

        workday_start = self._day_start(self.start_time.date())
        for staff in self.staff_pool:
            staff.is_available = True
            staff.reset_for_run(workday_start)

    def _scenario_defaults(self, scenario: str) -> Dict:
        defaults = {
            "baseline": {
                "total_requests": 100,
                "urgency_base": 5,
                "imbalance_factor": 0,
                "num_absent_staff": 0,
            },
            "peak_period": {
                "total_requests": 300,
                "urgency_base": 5,
                "imbalance_factor": 0,
                "num_absent_staff": 0,
            },
            "peak_urgency": {
                "total_requests": 260,
                "urgency_base": 8,
                "imbalance_factor": 10,
                "num_absent_staff": 0,
            },
            "workload_imbalance": {
                "total_requests": 220,
                "urgency_base": 5,
                "imbalance_factor": 70,
                "num_absent_staff": 0,
            },
            "staff_absence": {
                "total_requests": 200,
                "urgency_base": 5,
                "imbalance_factor": 10,
                "num_absent_staff": 1,
            },
        }
        return defaults.get(scenario, defaults["baseline"]).copy()

    def _build_run_config(self, custom_config: Optional[Dict]) -> Dict:
        incoming = custom_config.copy() if isinstance(custom_config, dict) else {}
        scenario = str(incoming.get("scenario", "baseline"))
        defaults = self._scenario_defaults(scenario)

        merged = defaults
        merged.update(incoming)

        merged["total_requests"] = max(1, int(merged.get("total_requests", 200)))
        merged["urgency_base"] = max(1, min(10, int(merged.get("urgency_base", 5))))
        merged["imbalance_factor"] = max(0, min(100, int(merged.get("imbalance_factor", 0))))
        merged["num_absent_staff"] = max(0, int(merged.get("num_absent_staff", 0)))
        merged["scenario"] = scenario
        return merged

    def _apply_staff_absence(self, num_absent_staff: int):
        if num_absent_staff <= 0:
            return

        available_staff = [s for s in self.staff_pool if s.is_available]
        if not available_staff:
            return

        absence_count = min(num_absent_staff, len(available_staff))
        absent_staff = self.rng.sample(available_staff, k=absence_count)

        for staff in absent_staff:
            staff.is_available = False
            self.absent_staff_ids.append(staff.staff_id)

    def _generate_requests(self, config: Dict) -> List[DocumentRequest]:
        total_requests = int(config["total_requests"])
        urgency_base = int(config["urgency_base"])
        imbalance_ratio = float(config["imbalance_factor"]) / 100.0

        colleges = list(COLLEGE_POPULATION.keys())
        weights = list(COLLEGE_POPULATION.values())

        if imbalance_ratio > 0:
            coe_index = colleges.index("COE")
            weights[coe_index] += imbalance_ratio * 0.35
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]

        requester_types = list(REQUESTER_PRIORITY.keys())
        requester_weights = [
            float(REQUESTER_GENERATION_WEIGHTS.get(requester, 0.0))
            for requester in requester_types
        ]
        if sum(requester_weights) <= 0:
            requester_weights = [1.0] * len(requester_types)
        document_types = list(DOCUMENT_COMPLEXITY.keys())
        doc_weights = [1.0] * len(document_types)

        if config.get("scenario") == "peak_period":
            boost_map = {
                "Official Transcript of Records (TOR) and Transfer Credentials (TC)": 3.0,
                "Certification": 2.0,
            }
            doc_weights = [
                float(boost_map.get(doc, 1.0)) for doc in document_types
            ]

        morning_count = int(total_requests * 0.60)
        afternoon_count = int(total_requests * 0.20)
        evening_count = total_requests - morning_count - afternoon_count

        # Generate submissions strictly inside configured working hours.
        start_hour = self.work_start_minutes / 60.0
        end_hour = self.work_end_minutes / 60.0
        effective_end_hour = max(start_hour + (1.0 / 60.0), end_hour - (1.0 / 60.0))
        span = max(effective_end_hour - start_hour, 0.1)

        bucket_1_end = start_hour + (span * 0.40)
        bucket_2_end = start_hour + (span * 0.75)

        def _next_urgency() -> int:
            low = max(1, urgency_base - 2)
            high = min(10, urgency_base + 2)
            value = self.rng.triangular(low, high, urgency_base)
            return int(round(max(1, min(10, value))))

        requests: List[DocumentRequest] = []
        request_counter = 1

        def _add_batch(count: int, hour_min: float, hour_max: float):
            nonlocal request_counter
            for _ in range(count):
                submission_offset_hours = self.rng.uniform(hour_min, hour_max)
                submission_time = self.start_time + timedelta(hours=submission_offset_hours)
                college = self.rng.choices(colleges, weights=weights, k=1)[0]
                document_type = self.rng.choices(document_types, weights=doc_weights, k=1)[0]
                allowed_requesters = DOCUMENT_REQUESTER_RESTRICTIONS.get(document_type)
                if allowed_requesters:
                    allowed = [r for r in requester_types if r in allowed_requesters]
                    if allowed:
                        requester_type = self.rng.choice(allowed)
                    else:
                        requester_type = self.rng.choices(
                            requester_types, weights=requester_weights, k=1
                        )[0]
                else:
                    requester_type = self.rng.choices(requester_types, weights=requester_weights, k=1)[0]
                partial_delay_hours = self.rng.uniform(*REQUIREMENTS_PARTIAL_DELAY_HOURS_RANGE)
                complete_extra_hours = self.rng.uniform(*REQUIREMENTS_COMPLETE_EXTRA_DELAY_HOURS_RANGE)
                requirements_partial_time = submission_time + timedelta(hours=partial_delay_hours)
                requirements_complete_time = requirements_partial_time + timedelta(hours=complete_extra_hours)
                payment_required = DOCUMENT_PAYMENT_REQUIRED.get(document_type, True)
                if payment_required:
                    payment_delay_hours = self.rng.uniform(*PAYMENT_DELAY_HOURS_RANGE)
                    payment_time = submission_time + timedelta(hours=payment_delay_hours)
                    ready_time = max(requirements_complete_time, payment_time)
                    payment_status = "Paid"
                else:
                    payment_time = None
                    ready_time = requirements_complete_time
                    payment_status = "Paid"

                request = DocumentRequest(
                    request_id=f"REQ{request_counter:04d}",
                    college=college,
                    document_type=document_type,
                    urgency=_next_urgency(),
                    requester_type=requester_type,
                    submission_time=submission_time,
                    requirements_partial_time=requirements_partial_time,
                    requirements_complete_time=requirements_complete_time,
                    payment_time=payment_time,
                    ready_time=ready_time,
                    payment_status=payment_status,
                )
                request.update_status(submission_time)
                requests.append(request)
                request_counter += 1

        _add_batch(morning_count, start_hour, bucket_1_end)
        _add_batch(afternoon_count, bucket_1_end, bucket_2_end)
        _add_batch(evening_count, bucket_2_end, effective_end_hour)

        return requests

# ---------------------------------------------------------------------
# Allocation helpers
# ---------------------------------------------------------------------

    def _active_staff(self) -> List[StaffMember]:
        return [staff for staff in self.staff_pool if staff.is_available]

    def _same_college_staff(self, college: str) -> List[StaffMember]:
        return [
            staff
            for staff in self.staff_pool
            if staff.is_available and staff.college_affiliation == college
        ]

    def _first_slot_for_staff(
        self,
        staff: StaffMember,
        earliest_time: datetime,
        enforce_quota: bool,
        ignore_staff_availability: bool = False,
    ) -> Optional[datetime]:
        if not staff.is_available:
            return None

        # Quota-based variants model assignment as a daily intake process.
        # They should not be blocked by completion_time of previously assigned requests.
        if enforce_quota or ignore_staff_availability:
            candidate = self._next_working_start(earliest_time)
        else:
            # Quota-free keeps strict per-staff availability sequencing.
            candidate = max(earliest_time, staff.next_available_time or earliest_time)
            candidate = self._next_working_start(candidate)

        # Keep shifting to next workday start while quota is full.
        # Guard with finite loop to avoid accidental infinite loops.
        for _ in range(2000):
            if not enforce_quota:
                return candidate

            assigned_today = staff.assignments_on_day(candidate.date())
            if assigned_today < staff.quota_limit:
                return candidate

            candidate = self._day_start(candidate.date() + timedelta(days=1))
            candidate = self._next_working_start(candidate)

        return None

    def _build_staff_options(
        self,
        request: DocumentRequest,
        staff_group: List[StaffMember],
        earliest_time: datetime,
        enforce_quota: bool,
        exact_time: Optional[datetime] = None,
        ignore_staff_availability: bool = False,
    ) -> List[Tuple[datetime, StaffMember]]:
        options: List[Tuple[datetime, StaffMember]] = []
        for staff in staff_group:
            slot = self._first_slot_for_staff(
                staff,
                earliest_time,
                enforce_quota,
                ignore_staff_availability=ignore_staff_availability,
            )
            if slot is None:
                continue
            if exact_time is not None and slot != exact_time:
                continue
            options.append((slot, staff))
        return options

    def _select_from_options(
        self,
        options: List[Tuple[datetime, StaffMember]],
        mode: str,
    ) -> Optional[Tuple[datetime, StaffMember]]:
        if not options:
            return None

        if mode == "earliest":
            return min(options, key=lambda item: (item[0], item[1].total_assigned, item[1].staff_id))
        if mode == "least_loaded":
            return min(
                options,
                key=lambda item: (
                    item[1].assignments_on_day(item[0].date()),
                    item[0],
                    item[1].staff_id,
                ),
            )
        if mode == "pooled":
            return min(options, key=lambda item: (item[0], item[1].total_assigned, item[1].staff_id))
        return min(options, key=lambda item: (item[0], item[1].staff_id))

    def _select_assignment(
        self,
        request: DocumentRequest,
        reference_time: datetime,
        exact_time: Optional[datetime] = None,
    ) -> Optional[Tuple[StaffMember, datetime, str]]:
        allocator = self.allocator_type
        request_day = request.submission_time.date()
        earliest = max(reference_time, request.submission_time)

        same_college = self._same_college_staff(request.college)
        all_active = self._active_staff()
        other_staff = [s for s in all_active if s.college_affiliation != request.college]

        if allocator == "college_based":
            if not same_college:
                return None
            options = self._build_staff_options(
                request,
                same_college,
                earliest,
                enforce_quota=True,
                exact_time=exact_time,
            )
            chosen = self._select_from_options(options, mode="earliest")
            if not chosen:
                return None
            slot, staff = chosen
            return staff, slot, "same_college"

        if allocator == "quota_free":
            if not same_college:
                return None
            options = self._build_staff_options(
                request,
                same_college,
                earliest,
                enforce_quota=False,
                exact_time=exact_time,
                ignore_staff_availability=True,
            )
            chosen = self._select_from_options(options, mode="earliest")
            if not chosen:
                return None
            slot, staff = chosen
            return staff, slot, "same_college_no_quota"

        if allocator == "pooled":
            options = self._build_staff_options(
                request,
                all_active,
                earliest,
                enforce_quota=True,
                exact_time=exact_time,
            )
            chosen = self._select_from_options(options, mode="pooled")
            if not chosen:
                return None
            slot, staff = chosen
            return staff, slot, "pooled_earliest"

        # workload_based
        target_day = earliest.date()
        same_options = self._build_staff_options(
            request,
            same_college,
            earliest,
            enforce_quota=True,
            exact_time=exact_time,
        )
        same_day_same = [item for item in same_options if item[0].date() == target_day]
        chosen = self._select_from_options(same_day_same, mode="least_loaded")
        if chosen:
            slot, staff = chosen
            return staff, slot, "same_college_least_loaded"

        all_options = self._build_staff_options(
            request,
            all_active,
            earliest,
            enforce_quota=True,
            exact_time=exact_time,
        )
        same_day_any = [item for item in all_options if item[0].date() == target_day]
        chosen = self._select_from_options(same_day_any, mode="least_loaded")
        if chosen:
            slot, staff = chosen
            return staff, slot, "least_loaded_same_day"

        chosen = self._select_from_options(all_options, mode="earliest")
        if not chosen:
            return None
        slot, staff = chosen
        return staff, slot, "next_available_day"

# ---------------------------------------------------------------------
# Event logging helpers
# ---------------------------------------------------------------------

    def _log_event(
        self,
        event_time: datetime,
        event_type: str,
        request: Optional[DocumentRequest] = None,
        staff: Optional[StaffMember] = None,
        details: str = "",
        extra: Optional[Dict] = None,
    ):
        self._event_seq += 1
        payload = {
            "sequence": self._event_seq,
            "time": event_time,
            "event_type": event_type,
            "request_id": request.request_id if request else None,
            "college": request.college if request else None,
            "document_type": request.document_type if request else None,
            "staff_id": staff.staff_id if staff else None,
            "details": details,
        }
        if request is not None:
            payload["priority_score"] = round(request.priority_score, 4)
        if extra:
            payload.update(extra)
        self.event_log.append(payload)

    def _finalize_event_log(self):
        priority = {
            "ARRIVAL": 0,
            "PRIORITY": 1,
            "ASSIGN": 2,
            "WAITING": 3,
            "COMPLETE": 4,
            "INFO": 5,
        }
        self.event_log.sort(
            key=lambda ev: (
                ev["time"],
                priority.get(ev["event_type"], 99),
                ev["sequence"],
            )
        )
        for index, event in enumerate(self.event_log):
            event["frame"] = index

    def _serialize_event(self, event: Dict) -> Dict:
        result = event.copy()
        result["time"] = result["time"].isoformat()
        return result

# ---------------------------------------------------------------------
# Assignment + processing helpers
# ---------------------------------------------------------------------

    def _processing_duration(self, request: DocumentRequest) -> Tuple[timedelta, bool]:
        base_duration, use_work_hours = _duration_to_schedule(
            DOCUMENT_COMPLEXITY.get(request.document_type, 1)
        )
        if use_work_hours:
            per_request_rng = random.Random(f"{self.random_seed}:{request.request_id}:proc")
            multiplier = per_request_rng.uniform(0.8, 1.2)
        else:
            multiplier = 1.0
        scaled = timedelta(seconds=base_duration.total_seconds() * multiplier)
        return scaled, use_work_hours

    def _assign_request(
        self,
        request: DocumentRequest,
        staff: StaffMember,
        assignment_time: datetime,
        assignment_mode: str,
    ):
        request.update_status(assignment_time)
        processing_duration, use_work_hours = self._processing_duration(request)
        if use_work_hours:
            completion_time = self._add_processing_with_work_hours(assignment_time, processing_duration)
        else:
            completion_time = assignment_time + processing_duration

        request.assignment_time = assignment_time
        request.completion_time = completion_time
        request.assigned_staff = staff.staff_id

        staff.total_assigned += 1
        staff.increment_day_quota(assignment_time.date())

        # Assignment availability is not completion-blocked in current intake model.
        staff.next_available_time = assignment_time

        self.completed.append(request)

        wait_hours = (assignment_time - request.submission_time).total_seconds() / 3600.0
        self._log_event(
            assignment_time,
            "ASSIGN",
            request=request,
            staff=staff,
            details=assignment_mode,
            extra={
                "queue_wait_hours": round(wait_hours, 2),
                "processing_hours": round(processing_duration.total_seconds() / 3600.0, 2),
            },
        )
        self._log_event(
            completion_time,
            "COMPLETE",
            request=request,
            staff=staff,
            details="request_completed",
        )

# ---------------------------------------------------------------------
# Scheduler execution
# ---------------------------------------------------------------------

    def _run_fcfs(self, requests: List[DocumentRequest]):
        arrivals = sorted(requests, key=lambda r: r.submission_time)
        pending: List[DocumentRequest] = []
        not_ready: List[DocumentRequest] = []
        index = 0

        if arrivals:
            current_time = arrivals[0].submission_time
        else:
            current_time = self._day_start(self.start_time.date())

        current_time = self._next_working_start(current_time)

        while index < len(arrivals) or pending or not_ready:
            while index < len(arrivals) and arrivals[index].submission_time <= current_time:
                req = arrivals[index]
                self._log_event(req.submission_time, "ARRIVAL", request=req, details="request_arrived")
                if self._is_request_ready(req, current_time):
                    pending.append(req)
                else:
                    not_ready.append(req)
                    self._log_event(
                        req.submission_time,
                        "WAITING",
                        request=req,
                        details="pending_requirements_or_payment",
                    )
                index += 1

            ready_now = [req for req in not_ready if self._is_request_ready(req, current_time)]
            for req in ready_now:
                not_ready.remove(req)
                pending.append(req)

            if not pending:
                next_arrival_time = arrivals[index].submission_time if index < len(arrivals) else None
                next_ready_time = min(
                    (req.ready_time for req in not_ready if req.ready_time),
                    default=None,
                )
                if next_arrival_time is None and next_ready_time is None:
                    break
                candidate_times = [t for t in [next_arrival_time, next_ready_time] if t is not None]
                current_time = min(candidate_times)
                current_time = self._next_working_start(current_time)
                continue

            next_req = min(
                pending,
                key=lambda r: (r.submission_time, r.ready_time or r.submission_time),
            )
            pending.remove(next_req)
            reference_time = max(current_time, next_req.ready_time or next_req.submission_time)
            selected = self._select_assignment(next_req, reference_time=reference_time)
            if selected is None:
                self.waiting_queue.append(next_req)
                self._log_event(
                    reference_time,
                    "WAITING",
                    request=next_req,
                    details="no_eligible_staff",
                )
                continue

            staff, assignment_time, mode = selected
            self._assign_request(next_req, staff, assignment_time, mode)
            current_time = max(current_time, assignment_time)

    def _run_weighted(self, requests: List[DocumentRequest]):
        arrivals = sorted(requests, key=lambda r: r.submission_time)
        pending: List[DocumentRequest] = []
        not_ready: List[DocumentRequest] = []
        index = 0

        if arrivals:
            current_time = arrivals[0].submission_time
        else:
            current_time = self._day_start(self.start_time.date())

        current_time = self._next_working_start(current_time)

        while index < len(arrivals) or pending or not_ready:
            if not pending and not_ready and index < len(arrivals):
                current_time = max(current_time, arrivals[index].submission_time)

            while index < len(arrivals) and arrivals[index].submission_time <= current_time:
                req = arrivals[index]
                self._log_event(req.submission_time, "ARRIVAL", request=req, details="request_arrived")
                if self._is_request_ready(req, current_time):
                    pending.append(req)
                    self.scheduler.add_request(req)
                else:
                    not_ready.append(req)
                    self._log_event(
                        req.submission_time,
                        "WAITING",
                        request=req,
                        details="pending_requirements_or_payment",
                    )
                index += 1

            ready_now = [req for req in not_ready if self._is_request_ready(req, current_time)]
            for req in ready_now:
                not_ready.remove(req)
                pending.append(req)
                self.scheduler.add_request(req)

            if not pending:
                next_arrival_time = arrivals[index].submission_time if index < len(arrivals) else None
                next_ready_time = min(
                    (req.ready_time for req in not_ready if req.ready_time),
                    default=None,
                )
                if next_arrival_time is None and next_ready_time is None:
                    break
                candidate_times = [t for t in [next_arrival_time, next_ready_time] if t is not None]
                current_time = min(candidate_times)
                current_time = self._next_working_start(current_time)
                continue

            ranked = self.scheduler.rank(
                current_time=current_time,
                weights=self.priority_weights,
                workday_minutes=self.workday_minutes,
                urgency=self.urgency,
            )

            top_preview = [
                f"{item.request_id}:{item.priority_score:.3f}" for item in ranked[:3]
            ]
            self._log_event(
                current_time,
                "PRIORITY",
                details="top_pending=" + ", ".join(top_preview),
                extra={"pending_count": len(ranked)},
            )

            selected_tuple: Optional[Tuple[DocumentRequest, StaffMember, datetime, str]] = None

            # Pick highest-priority request that is assignable right now.
            for req in ranked:
                candidate = self._select_assignment(req, reference_time=current_time, exact_time=current_time)
                if candidate is None:
                    continue
                staff, assignment_time, mode = candidate
                selected_tuple = (req, staff, assignment_time, mode)
                break

            if selected_tuple is not None:
                req, staff, assignment_time, mode = selected_tuple
                self.scheduler.remove_request(req)
                pending.remove(req)
                self._assign_request(req, staff, assignment_time, mode)
                continue

            # Nothing assignable now. Advance to next event (arrival, readiness, or future slot).
            next_arrival_time = arrivals[index].submission_time if index < len(arrivals) else None
            next_ready_time = min(
                (req.ready_time for req in not_ready if req.ready_time),
                default=None,
            )
            next_slot_time: Optional[datetime] = None

            for req in ranked:
                candidate = self._select_assignment(req, reference_time=current_time)
                if candidate is None:
                    continue
                _, slot_time, _ = candidate
                if next_slot_time is None or slot_time < next_slot_time:
                    next_slot_time = slot_time

            if next_arrival_time is None and next_ready_time is None and next_slot_time is None:
                # Remaining pending requests are impossible to route.
                for req in pending:
                    self.scheduler.remove_request(req)
                    self.waiting_queue.append(req)
                    self._log_event(
                        current_time,
                        "WAITING",
                        request=req,
                        details="no_eligible_staff",
                    )
                for req in not_ready:
                    self.waiting_queue.append(req)
                    self._log_event(
                        current_time,
                        "WAITING",
                        request=req,
                        details="pending_requirements_or_payment",
                    )
                pending.clear()
                not_ready.clear()
                break

            candidate_times = [
                t for t in [next_arrival_time, next_ready_time, next_slot_time] if t is not None
            ]
            current_time = min(candidate_times)
            current_time = self._next_working_start(current_time)

# ---------------------------------------------------------------------
# Metrics and public run API
# ---------------------------------------------------------------------

    def _calculate_metrics(self) -> Dict:
        if not self.completed:
            return {
                "avg_waiting_time_hours": 0.0,
                "avg_turnaround_days": 0.0,
                "total_days_elapsed": 0.0,
                "throughput_req_per_day": 0.0,
                "total_processed": 0,
                "staff_load": {staff.staff_id: 0 for staff in self.staff_pool},
                "scenario": self.scenario,
            }

        waiting_hours = [req.get_waiting_time_minutes() / 60.0 for req in self.completed]
        turnaround_days = [req.get_turnaround_time_minutes() / 1440.0 for req in self.completed]

        first_submission = min(req.submission_time for req in self.completed)
        last_completion = max(req.completion_time for req in self.completed if req.completion_time)
        total_days_elapsed = max((last_completion - first_submission).total_seconds() / 86400.0, 0.0)

        throughput = len(self.completed) / max(total_days_elapsed, 1.0)

        staff_load = {staff.staff_id: 0 for staff in self.staff_pool}
        for req in self.completed:
            if req.assigned_staff in staff_load:
                staff_load[req.assigned_staff] += 1

        return {
            "avg_waiting_time_hours": round(sum(waiting_hours) / len(waiting_hours), 2),
            "avg_turnaround_days": round(sum(turnaround_days) / len(turnaround_days), 2),
            "total_days_elapsed": round(total_days_elapsed, 2),
            "throughput_req_per_day": round(throughput, 2),
            "total_processed": len(self.completed),
            "staff_load": staff_load,
            "scenario": self.scenario,
        }

    def run(self, custom_config: Optional[Dict] = None) -> Dict:
        config = self._build_run_config(custom_config)
        self.scenario = config["scenario"]

        self.start_time = self._default_day_start(datetime.now())
        self._reset_for_run()
        self._apply_staff_absence(config["num_absent_staff"])

        requests = self._generate_requests(config)
        self.generated_requests = requests

        if self.scheduler_type == "FCFS":
            self._run_fcfs(requests)
        elif self.scheduler_type == "WEIGHTED":
            self._run_weighted(requests)
        else:
            raise ValueError(f"Unsupported scheduler_type: {self.scheduler_type}")

        self._finalize_event_log()
        metrics = self._calculate_metrics()

        metrics.update(
            {
                "scheduler_type": self.scheduler_type,
                "allocator_type": self.allocator_type,
                "seed_used": self.random_seed,
                "run_config": config,
                "priority_weights": self.priority_weights,
                "work_hours": {
                    "start": self._clock_string(self.work_start_minutes),
                    "end": self._clock_string(self.work_end_minutes),
                },
                "waiting_queue_count": len(self.waiting_queue),
                "waiting_queue": [req.to_dict() for req in self.waiting_queue],
                "completed_requests": [req.to_dict() for req in self.completed],
                "generated_requests": [req.to_dict() for req in self.generated_requests],
                "event_log": [self._serialize_event(event) for event in self.event_log],
                "absent_staff": self.absent_staff_ids,
            }
        )

        return metrics


# Backward-compatible alias
SimulationEngine1 = SimulationEngine
