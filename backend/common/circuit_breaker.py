"""
Circuit breaker simple para llamadas HTTP a gateways externos.

Estados:
  CLOSED    — operación normal; cada fallo incrementa el contador
  OPEN      — fallas superan el umbral; todas las llamadas se rechazan sin intentarlas
  HALF_OPEN — tras el timeout de recuperación, se permite un intento de prueba

Uso:
    _bancard_cb = CircuitBreaker(name="bancard", failure_threshold=5, recovery_timeout=60)

    with _bancard_cb:
        resp = requests.post(url, ...)

Si el circuito está OPEN, lanza CircuitBreakerOpen inmediatamente (sin hacer el request).
"""

import logging
import threading
import time
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    """El circuito está abierto; la llamada fue rechazada sin ejecutarse."""


class _State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self._state = _State.CLOSED
        self._failure_count = 0
        self._opened_at: float | None = None
        self._lock = threading.Lock()

    # ── Contexto ──────────────────────────────────────────────────────────────

    def __enter__(self):
        self._before_call()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._on_success()
        elif issubclass(exc_type, self.expected_exception):
            self._on_failure(exc_val)
        return False  # no suprime la excepción

    # ── Transiciones ──────────────────────────────────────────────────────────

    def _before_call(self):
        with self._lock:
            if self._state is _State.CLOSED:
                return
            if self._state is _State.OPEN:
                if self._opened_at and (time.monotonic() - self._opened_at) >= self.recovery_timeout:
                    self._state = _State.HALF_OPEN
                    logger.info("CircuitBreaker[%s]: HALF_OPEN — intentando recuperación", self.name)
                else:
                    raise CircuitBreakerOpen(
                        f"CircuitBreaker '{self.name}' está OPEN. "
                        f"Reintentando en {self._seconds_until_recovery():.0f}s."
                    )
            # HALF_OPEN: dejar pasar el intento

    def _on_success(self):
        with self._lock:
            if self._state is _State.HALF_OPEN:
                logger.info("CircuitBreaker[%s]: CLOSED (recuperado)", self.name)
            self._state = _State.CLOSED
            self._failure_count = 0
            self._opened_at = None

    def _on_failure(self, exc: Exception):
        with self._lock:
            self._failure_count += 1
            if self._state is _State.HALF_OPEN or self._failure_count >= self.failure_threshold:
                self._state = _State.OPEN
                self._opened_at = time.monotonic()
                logger.error(
                    "CircuitBreaker[%s]: OPEN tras %d fallos consecutivos. Último error: %s",
                    self.name,
                    self._failure_count,
                    exc,
                )
                try:
                    import sentry_sdk
                    sentry_sdk.capture_message(
                        f"CircuitBreaker '{self.name}' OPEN — {self._failure_count} fallos: {exc}",
                        level="error",
                    )
                except Exception:
                    pass

    def _seconds_until_recovery(self) -> float:
        if self._opened_at is None:
            return 0.0
        elapsed = time.monotonic() - self._opened_at
        return max(0.0, self.recovery_timeout - elapsed)

    # ── Introspección ─────────────────────────────────────────────────────────

    @property
    def state(self) -> str:
        return self._state.value

    @property
    def failure_count(self) -> int:
        return self._failure_count
