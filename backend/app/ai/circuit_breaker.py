from __future__ import annotations

import time
from enum import Enum
from typing import Any, Dict, Optional

from app.core.logging import logger


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_requests: int = 3,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_requests = half_open_max_requests

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float = 0.0
        self.half_open_requests = 0

    def record_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_requests += 1
            if self.half_open_requests >= self.half_open_max_requests:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.half_open_requests = 0
                logger.info("circuit_breaker.closed", name=self.name)
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()

        if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                "circuit_breaker.opened",
                name=self.name,
                failures=self.failure_count,
                timeout=self.recovery_timeout,
            )
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.last_failure_time = time.monotonic()
            logger.warning("circuit_breaker.reopened", name=self.name)

    def allow_request(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if time.monotonic() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_requests = 0
                logger.info("circuit_breaker.half_open", name=self.name)
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return self.half_open_requests < self.half_open_max_requests

        return True

    def get_state_summary(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "time_since_last_failure": time.monotonic() - self.last_failure_time if self.last_failure_time > 0 else None,
        }


class CircuitBreakerRegistry:
    _breakers: Dict[str, CircuitBreaker] = {}

    @classmethod
    def get(cls, name: str) -> CircuitBreaker:
        if name not in cls._breakers:
            cls._breakers[name] = CircuitBreaker(name=name)
        return cls._breakers[name]

    @classmethod
    def get_all_states(cls) -> Dict[str, Dict[str, Any]]:
        return {name: breaker.get_state_summary() for name, breaker in cls._breakers.items()}

    @classmethod
    def reset(cls, name: str) -> None:
        if name in cls._breakers:
            del cls._breakers[name]
