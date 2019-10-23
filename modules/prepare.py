import os
import subprocess
import numpy as np
import logging
import pwd

from lib.abort_function import abort_function
from apersharp.modules.base import BaseModule

logger = logging.getLogger(__name__)

FNULL = open(os.devnull, 'w')


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

        # create the directory structure
        self.set_directories()

        # get the data
        self.get_data()

        # set things up for sharpener

        abort_function("Nothing here yet")

    def set_directories(self):
        """
        Function to create the directory structure
        """

        # Create the cube directory
        cube_subdir = "cube_{}".format(self.cube)
        self.cube_dir = os.path.join(self.sharpener_basedir, cube_subdir)
        if not os.path.exists(self.cube_dir):
            try:
                os.mkdir(self.cube_dir)
            except Exception as e:
                logger.exception(e)
            else:
                logger.info(
                    "Cube {}: Created directory for cube".format(self.cube))

        # Create beam directories if data is not coming from happili
        if self.data_source != "happili-01" and self.data_source != "happili-02" and self.data_source != "happili-03" and self.data_source != "happili-04" and self.data_source != "happili-05":
            for beam in range(self.NBEAMS):
                beam_dir = os.path.join(self.cube_dir, "{:02d}".format(beam))
                if not os.path.exists(beam_dir):
                    try:
                        os.mkdir(beam_dir)
                    except Exception as e:
                        logger.exception(e)
                    else:
                        logger.info(
                            "Cube {0}: Created directory for beam {1}".format(self.cube, beam))

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
        if self.data_source == 'local':
            if not get_data_local:
                # check that the directory exists
                local_basedir = os.path.join(self.data_basedir, self.taskid)
                if os.path.exists(local_basedir):
                    logger.info(
                        "Found local directory for data {}".format(local_basedir))
                    if local_basedir == self.sharpener_basedir:
                        logger.info(
                            "Data is already in the working directory.")
                        get_data_local = True
                    else:
                        # copy the data
                        abort_function(
                            "Functionality to copy from a local data directory is not yet available")
            else:
                logger.info("Data is already available")
        elif self.data_source == 'ALTA':
            if not get_data_alta:
                # default path /altaZone/archive/apertif_main/visibilities_default/190409015_AP_B000
                abort_function(
                    "Functionality to copy data from ALTA is not yet available")
            else:
                logger.info("Data is already available")
        elif self.data_source != "happili-01" or self.data_source != "happili-02" or self.data_source != "happili-03" or self.data_source != "happili-04" or self.data_source != "happili-05":
            if not get_data_happili:
                # works only within ASTRON network
                logger.warning(
                    "Cube {}: Getting data from happili only works from within the ASTRON network".format(self.cube))
                # get the happili path
                if self.data_basedir == '':
                    self.data_basedir = "/data/apertif"
                data_basedir = os.path.join(self.data_basedir, self.taskid)
                happili_path = os.path.join(
                    data_basedir, "./[0-3][0-9]/line/cubes/HI_image_cube{}.fits".format(self.cube))
                # get the user name
                user_name = pwd.getpwuid(os.getuid())[0]

                rsync_cmd = 'rsync -Razuve ssh {0}@{1}:"{2}" {3}/'.format(
                    user_name, self.data_source, happili_path, self.cube_dir)
                logger.debug(rsync_cmd)

                try:
                    logger.info("Cube {0}: Copying data from {1}".format(
                        self.cube, self.data_source))
                    subprocess.check_call(
                        rsync_cmd, shell=True, stdout=FNULL, stderr=FNULL)
                except Exception as e:
                    logger.error(
                        "Cube {0}:Copying data from {1} ... Failed".format(self.cube, self.data_source))
                    logger.exception(e)
                else:
                    logger.info(
                        "Cube {0}:Copying data from {1} ... Done".format(self.cube, self.data_source))

            else:
                logger.info("Data is already available")
        else:
            error = "Did not recognize data source. Abort"
            logger.error(error)
            raise RuntimeError(error)

        # store status parameters
