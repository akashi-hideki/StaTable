import logging
import sys
from typing import Optional, Callable


class StaTableLogger:
    """StaTable dedicated logger (singleton)"""
    _instance: Optional['StaTableLogger'] = None
    _log_callback: Optional[Callable[[str], None]] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_logger()
        return cls._instance

    def _init_logger(self):
        self.logger = logging.getLogger("StaTable")
        self.logger.setLevel(logging.DEBUG)

        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        console.setFormatter(formatter)
        self.logger.addHandler(console)

        self.trace_handler = _TraceBallHandler()
        self.trace_handler.setLevel(logging.DEBUG)
        self.trace_handler.setFormatter(formatter)
        self.logger.addHandler(self.trace_handler)

    def set_log_callback(self, callback: Callable[[str], None]):
        self._log_callback = callback
        self.trace_handler.set_callback(callback)

    @classmethod
    def get_logger(cls) -> logging.Logger:
        return cls().logger

    @classmethod
    def debug(cls, msg: str, *args, **kwargs):
        cls.get_logger().debug(msg, *args, **kwargs)

    @classmethod
    def info(cls, msg: str, *args, **kwargs):
        cls.get_logger().info(msg, *args, **kwargs)

    @classmethod
    def warning(cls, msg: str, *args, **kwargs):
        cls.get_logger().warning(msg, *args, **kwargs)

    @classmethod
    def error(cls, msg: str, *args, **kwargs):
        cls.get_logger().error(msg, *args, **kwargs)


class _TraceBallHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.callback: Optional[Callable[[str], None]] = None

    def set_callback(self, callback: Optional[Callable[[str], None]]):
        self.callback = callback

    def emit(self, record: logging.LogRecord):
        """Forward the record to the callback (TraceBall widget).

        [v2.3 fix] If the callback target has been deleted by Qt
        (e.g. the TraceBallWidget was destroyed when a MainWindow was
        garbage-collected), the C++ object access raises RuntimeError.
        In that case, clear the callback so subsequent records do not
        keep retrying; a new widget will install a new callback in its
        own __init__.
        """
        if self.callback:
            try:
                msg = self.format(record)
                self.callback(msg)
            except RuntimeError:
                # Target widget was deleted; drop the stale callback.
                self.callback = None