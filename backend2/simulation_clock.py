from datetime import datetime, timedelta

class SimulationClock:
    def __init__(self, start_time: datetime, tick_minutes: int = 1):
        self.current_time = start_time
        self.tick_minutes = tick_minutes
        self.running = False

    def now(self) -> datetime:
        return self.current_time

    def tick(self):
        self.current_time += timedelta(minutes=self.tick_minutes)

    def set_time(self, new_time: datetime):
        self.current_time = new_time

    def start(self):
        self.running = True

    def pause(self):
        self.running = False