from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SimulationContext:
    engine: Any = None
    results: Dict[str, Any] = None
    config: Dict[str, Any] = None

    def is_ready(self) -> bool:
        return self.engine is not None and self.results is not None