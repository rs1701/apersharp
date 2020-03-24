import logging
import os
from ConfigParser import ConfigParser

logger = logging.getLogger(__name__)


def load_config(config_object, config_file=None):
    """
    Function to load the config file.

    Adapted from Apercal

    Args:
    -----
    config_object (object): Class object
    config_file (str): Name with path of the config file

    Return:
    ------
    Settings of class object based on config
    """

    config = ConfigParser()  # Initialise the config parser
    if config_file is not None:
        if not os.path.exists(config_file):
            error = "User-specified configuration file {} was not found".format(
                config_file)
            raise RuntimeError(error)
        else:
            logger.info(
                'Reading user-specified configuration file {}'.format(config_file))
            config.readfp(open(config_file))
    else:
        logger.info(
            'Reading default configuration file')
        default_cfg = os.path.join(os.path.basename(
            __file__), "../apersharp_config/apersharp_default.cfg")
        config.readfp(open(default_cfg))

    for sect in config.sections():

        for item in config.items(sect):
            setattr(config_object, item[0], eval(item[1]))

    logger.info(
        'Reading configuration file ... Done'.format(config_file))
    return config
