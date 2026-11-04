"""
FarmGuard AI - Centralized Structured Logger with Windows UTF-8 Safe Handler.
"""
import logging
import sys

class SafeEncodingStreamHandler(logging.StreamHandler):
    """StreamHandler that encodes Unicode and emojis safely for Windows consoles."""
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Encode with replacement if console stream encoding cannot represent the char
            enc = getattr(stream, "encoding", "utf-8") or "utf-8"
            safe_msg = msg.encode(enc, errors="backslashreplace").decode(enc)
            stream.write(safe_msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

def get_logger(name: str = "FarmGuardAI") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = SafeEncodingStreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger

logger = get_logger("FarmGuardAI")
