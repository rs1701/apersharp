import os
import subprocess
import numpy as np
import logging

from lib.abort_function import abort_function
from apersharp.modules.base import BaseModule

logger = logging.getLogger(__name__)


class prepare(BaseModule):
    """
    Class to handle getting cubes and setting everything up for sharpener
    """

    module_name = "Prepare"

    def __init__(self, file_=None, **kwargs):
        pass

    def go(self):
        """
        Function to call all other function necessary to set things up
        """

        # get the data

        # create the directory structure

        # set things up for sharpener

        abort_function("Nothing here yet")

    def get_data(self):
        """
        Function to get the data depending on the source
        """

        beam_dir = np.arange(self.NBEAMS)

        # some status variables
        get_data_happili = False
        get_data_alta = False
        get_data_local = False

        # go through the different options of where data can come from
        if self.output_source == 'local':
            if not get_data_local:
                # check that the directory exists
                local_basedir = os.path.join(self.data_basedir, self.taskid)
                if os.path.exists(local_basedir):
                    logger.info(
                        "Found local directory for data {}".format(local_basedir))
                    # copy the data
                    abort_function(
                        "Functionality to copy from a local data directory is not yet available")
            else:
                logger.info("Data is already available")
                get_data_local = True
        elif self.output_source == 'ALTA':
            if not get_data_alta:
                abort_function(
                    "Functionality to copy data from ALTA is not yet available")
