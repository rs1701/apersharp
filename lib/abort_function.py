import logging
import os


def abort_function(abort_message):
    """
    Simple abort function if non-existing features are triggered
    """
    logger = logging.getLogger(__name__)
    logger.error(abort_message)
    logger.error("Abort")
    raise RuntimeError(abort_message)
