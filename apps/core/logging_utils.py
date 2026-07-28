import json
import logging


class JSONFormatter(logging.Formatter):
    """Log estruturado (uma linha JSON por evento) para produção — pensado
    para ferramentas de agregação de log (CloudWatch, Datadog, etc.) que
    entendem JSON nativamente. Em desenvolvimento local usamos o formato
    "verbose" (texto simples), mais fácil de ler no console."""

    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)
