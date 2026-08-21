import logging
from pythonjsonlogger import jsonlogger


def configure_logging():
    root = logging.getLogger()
    # Avoid adding duplicate handlers in test runs
    if any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        return

    handler = logging.StreamHandler()
    fmt = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(fmt)
    root.addHandler(handler)
    root.setLevel(logging.INFO)
