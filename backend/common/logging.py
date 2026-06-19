"""
JSON formatter para logging estructurado (Sentry / ELK).
Sin dependencias externas — usa la stdlib.
"""
import json
import logging
import traceback


class JsonFormatter(logging.Formatter):
    """
    Formatea cada LogRecord como una línea JSON.

    Campos garantizados:
      timestamp, level, logger, message, request_id

    Campos opcionales (si están presentes en el record):
      module, lineno, funcName, exc_info
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            "timestamp":  self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level":      record.levelname,
            "logger":     record.name,
            "message":    record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }

        if record.module:
            log_entry["module"]   = record.module
            log_entry["lineno"]   = record.lineno
            log_entry["funcName"] = record.funcName

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        elif record.exc_text:
            log_entry["exception"] = record.exc_text

        if hasattr(record, "stack_info") and record.stack_info:
            log_entry["stack_info"] = self.formatStack(record.stack_info)

        # Campos extra añadidos via logger.info("msg", extra={...})
        _std_keys = logging.LogRecord.__dict__.keys() | {
            "message", "asctime", "request_id",
        }
        for key, val in record.__dict__.items():
            if key not in _std_keys and not key.startswith("_"):
                try:
                    json.dumps(val)  # verify serializable
                    log_entry[key] = val
                except (TypeError, ValueError):
                    log_entry[key] = str(val)

        return json.dumps(log_entry, ensure_ascii=False)
