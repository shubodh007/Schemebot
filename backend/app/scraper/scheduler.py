from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


class ScrapingScheduler:
    schedules: List[Dict[str, Any]] = [
        {
            "source": "myscheme",
            "cron_hour": 6,
            "cron_minute": 0,
            "interval_hours": 24,
            "type": "delta",
            "priority": 1,
        },
        {
            "source": "india_gov",
            "cron_hour": 8,
            "cron_minute": 0,
            "interval_hours": 168,
            "type": "full_refresh",
            "priority": 2,
        },
        {
            "source": "ap_portal",
            "cron_hour": 10,
            "cron_minute": 0,
            "interval_hours": 168,
            "type": "full_refresh",
            "priority": 3,
        },
        {
            "source": "telangana_portal",
            "cron_hour": 12,
            "cron_minute": 0,
            "interval_hours": 168,
            "type": "full_refresh",
            "priority": 3,
        },
    ]

    def should_run(self, schedule: Dict[str, Any], last_run: datetime | None = None) -> bool:
        if last_run is None:
            return True

        now = datetime.now(timezone.utc)
        elapsed = (now - last_run).total_seconds()
        interval = schedule.get("interval_hours", 24) * 3600
        return elapsed >= interval

    def get_due_sources(self, last_runs: Dict[str, datetime | None]) -> List[str]:
        due = []
        for schedule in self.schedules:
            source = schedule["source"]
            if self.should_run(schedule, last_runs.get(source)):
                due.append(source)
        return due

    def get_schedule_for_source(self, source: str) -> Dict[str, Any] | None:
        for s in self.schedules:
            if s["source"] == source:
                return s
        return None
