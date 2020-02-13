import logging
import os
import subprocess


def setup_logger(level="DEBUG", logfile=None, new_logfile=True):
    """
    Function to create a logging object for apersharp.

    Based on the same function in Apercal (apercal.libs.setup_logger)

    Args:
    -----
        level (str): Logging level. Default "DEBUG"
        logfile (str): Name of logfile. Default Apersched.log
        new_logfile (bool): Set to False if file is continued to avoid printing starting messages

    """

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.handlers = []

    # set up handler
    fh_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : %(message)s',
                                     datefmt='%m/%d/%Y %I:%M:%S %p')

    if logfile is None:
        fh = logging.FileHandler("Apersched.log")
    else:
        fh = logging.FileHandler(logfile)

    fh.setLevel(logging.getLevelName(level))
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)

    # set up output stream to command line
    sh_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : %(message)s',
                                     datefmt='%m/%d/%Y %I:%M:%S %p')
    sh = logging.StreamHandler()
    sh.setLevel(logging.getLevelName(level))
    sh.setFormatter(sh_formatter)
    logger.addHandler(sh)

    if new_logfile:
        logger.info("Logging started")

        logger.info(
            "Logging to file. To see the log in a bash window use the following command:")
        logger.info("tail -n +1 -f {}".format(logfile))

    return logger
