import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class TaskTimer:
    task_id: str
    task_name: str
    is_google_task: bool
    estimated_seconds: Optional[int] = None
    start_time: Optional[float] = None
    elapsed_seconds: float = 0.0
    is_running: bool = False
    
    def start(self):
        if not self.is_running:
            self.start_time = time.time()
            self.is_running = True
            
    def pause(self):
        if self.is_running and self.start_time is not None:
            self.elapsed_seconds += time.time() - self.start_time
            self.is_running = False
            self.start_time = None
            
    def get_current_elapsed(self) -> float:
        if self.is_running and self.start_time is not None:
            return self.elapsed_seconds + (time.time() - self.start_time)
        return self.elapsed_seconds
        
    def format_time(self, seconds: float) -> str:
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"
