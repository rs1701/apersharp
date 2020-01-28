import os
import subprocess
import numpy as np
import logging
import pwd
import glob

from lib.abort_function import abort_function
from apersharp.modules.base import BaseModule

import SHARPener

logger = logging.getLogger(__name__)

FNULL = open(os.devnull, 'w')


class apersharp(BaseModule):
    """
    Class to handle getting cubes, setting everything up for sharpener
    and running sharpener
    """

    module_name = "Apersharp"

    def __init__(self, file_=None, **kwargs):
        pass

    def go(self):
        """
        Function to call all other function necessary to set things up
        """

        if "get_data" in self.steps:
            logger.info("Creating directories and getting data")
            # create the directory structure
            self.set_directories()

            # get the data
            self.get_data()

            logger.info("Creating directories and getting data ... Done")
        else:
            logger.info("Skippting creating directories and getting data")

        # set things up for sharpener
        if "setup_sharpener" in self.steps:
            logger.info("Setting up sharpner")

            abort_function("Nothing here yet")

            logger.info("Setting up sharpner ... Done")
        else:
            logger.info("Skipping setting up sharpener")

        # run sharpener
        if "run_sharpener" in self.steps:
            logger.info("Running sharpener")

            abort_function("Nothing here yet")

            logger.info("Running sharpener ... Done")
        else:
            logger.info("Skipping running sharpener")

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
        if self.data_source != "happili":
            for beam in self.beam_list:
                beam_dir = os.path.join(self.cube_dir, "{:02d}".format(beam))
                if not os.path.exists(beam_dir):
                    try:
                        os.mkdir(beam_dir)
                    except Exception as e:
                        logger.exception(e)
                    else:
                        logger.info(
                            "Cube {0}: Created directory for beam {1}".format(self.cube, beam))

    # +++++++++++++++++++++++++++++++++++++++++++++++++++
    def check_alta_path(self, alta_path):
        """
        Function to quickly check the path exists on ALTA
        """
        alta_cmd = "ils {}".format(alta_path)
        logger.debug(alta_cmd)
        return_msg = subprocess.call(alta_cmd, shell=True,
                                     stdout=self.FNULL, stderr=self.FNULL)
        return return_msg

    # ++++++++++++++++++++++++++++++++++++++++++++++++++
    def getdata_from_alta(self, alta_file_name, output_path):
        """
        Function to get files from ALTA

        Could be done by getdata_alta package, too.
        """

        # set the irod files location
        irods_status_file = os.path.join(
            os.getcwd(), "transfer_{}_img-icat.irods-status".format(os.path.basename(alta_file_name).split(".")[0]))
        irods_status_lf_file = os.path.join(
            os.getcwd(), "transfer_{}_img-icat.lf-irods-status".format(os.path.basename(alta_file_name).split(".")[0]))

        # get the file from alta
        alta_cmd = "iget -rfPIT -X {0} --lfrestart {1} --retries 5 {2} {3}/".format(
            irods_status_file, irods_status_lf_file, alta_file_name, output_path)
        logger.debug(alta_cmd)
        return_msg = subprocess.check_call(
            alta_cmd, shell=True, stdout=self.FNULL, stderr=self.FNULL)

        return return_msg

    # ++++++++++++++++++++++++++++++++++++++++++++++++++
    def get_data(self):
        """
        Function to get the data depending on the source

        """

        beam_dir = np.arange(self.NBEAMS)
        self.continuum_image_list = []

        # Going through the beams to get the data:
        for beam in self.beam_list:

            # check first if they do not already exists
            cube_path = self.get_cube_path(beam)
            if os.path.exists(cube_path):
                logger.info(
                    "Cube {0}: Found cube for beam {1}".format(self.cube, beam))
            else:
                logger.info(
                    "Cube {0}: Getting cube for beam {1}".format(self.cube, beam))

                # go through the different options of where data can come from
                if self.data_source == 'local':
                    # check that the directory exists
                    local_basedir = os.path.join(
                        self.data_basedir, self.taskid)
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
                # look for data in ALTA
                elif self.data_source == 'ALTA':
                    # storing failed beams
                    failed_beams = []
                    # go through the list of beams
                    # but make a copy to be able to remove beams if they are not available
                    for beam in self.beam_list:
                        # /altaZone/archive/apertif_main/visibilities_default/<taskid>_AP_B0XY
                        alta_taskid_beam_dir = "/altaZone/archive/apertif_main/visibilities_default/{0}_AP_B{1}".format(
                            self.taskid, str(beam).zfill(3))

                        # check that the beam is available on ALTA
                        if self.check_alta_path(alta_taskid_beam_dir) == 0:
                            logger.info("Found beam {} of taskid {} on ALTA".format(
                                beam, self.taskid))

                            # look for cube
                            # look for the cube file using try and error
                            cube_name = ''
                            alta_beam_cube_path = ''
                            cube_name = "HI_beam_image_{}.fits".format(
                                self.cube)
                            alta_beam_cube_path = os.path.join(
                                alta_taskid_beam_dir, "cube/{}".format(cube_name))
                            if self.check_alta_path(alta_beam_cube_path) == 0:
                                logger.info("Found cube on ALTA in {}".format(
                                    alta_beam_cube_path))
                            else:
                                # make empty again when no image was found
                                cube_name = ''
                            if cube_name == '':
                                logger.warning(
                                    "No cube {0} found on ALTA for beam {1} of taskid {2}".format(self.cube, beam, self.taskid))
                                failed_beams.append(beam)
                            else:
                                # create directory for beam in the directory
                                cube_beam_dir = os.path.join(
                                    self.cube_dir, str(beam).zfill(2))
                                if not os.path.exists(cube_beam_dir):
                                    logger.debug(
                                        "Creating directory for beam {0} of cube {1}".format(beam, self.cube))
                                    os.mkdir(cube_beam_dir)
                                # check whether file already there:
                                if not os.path.exists(os.path.join(cube_beam_dir, os.path.basename(alta_beam_cube_path))):
                                    # copy the cube to this directory
                                    return_msg = self.getdata_from_alta(
                                        alta_beam_cube_path, cube_beam_dir)
                                    if return_msg == 0:
                                        logger.info("Getting image of beam {0} of taskid {1} ... Done".format(
                                            beam, self.taskid))
                                    else:
                                        logger.warning("Getting image of beam {0} of taskid {1} ... Failed".format(
                                            beam, self.taskid))
                                        failed_beams.append(beam)
                                else:
                                    logger.info("Cube {0} of beam {1} of taskid {2} already on disk".format(
                                        self.cube, beam, self.taskid))
                                    if self.cont_src_resource == "continuum":
                                        # now get the continuum image
                                        # look for the image file ALTA by try and error
                                    continuum_image_name = ''
                                    alta_beam_image_path = ''
                                    for k in range(10):
                                        continuum_image_name = "image_mf_{0:02d}.fits".format(
                                            k)
                                        alta_beam_image_path = os.path.join(
                                            alta_taskid_beam_dir, continuum_image_name)
                                        if self.check_alta_path(alta_beam_image_path) == 0:
                                            break
                                        else:
                                            # make empty again when no image was found
                                            continuum_image_name = ''
                                            continue
                                    # if there is no continuum image, this is a critical error
                                    # This should not happen because the continuum image is necessary
                                    # for the continuum subtraction
                                    if continuum_image_name == '':
                                        error = "No image found on ALTA for beam {0} of taskid {1} but cube {2} exists. This should not happen. Abort".format(
                                            beam, self.taskid, self.cube)
                                        logger.error(error)
                                        raise RuntimeError(error)
                                    else:
                                        logger.info(
                                            "Found continuum image for beam {} on ALTA".format(beam))
                                        # check whether file already there:
                                        if not os.path.exists(os.path.join(cube_dir, os.path.basename(alta_beam_image_path))):
                                            # copy the continuum image to this directory
                                            return_msg = self.getdata_from_alta(
                                                alta_beam_image_path, continuum_image_beam_dir)
                                            if return_msg == 0:
                                                logger.info("Getting image of beam {0} of taskid {1} ... Done".format(
                                                    beam, self.taskid))
                                            else:
                                                error = "Getting image of beam {0} of taskid {1} ... Failed".format(
                                                    beam, self.taskid)
                                                logger.error(error)
                                                raise RuntimeError(error)

                                            continuum_image_list.append(
                                                continuum_image_name)
                                        else:
                                            logger.info("Image of beam {0} of taskid {1} already on disk".format(
                                                beam, self.mosaic_taskid))
                        else:
                            logger.warning("Did not find beam {0} of taskid {1}".format(
                                beam, self.taskid))
                            # remove the beam
                            failed_beams.append(beam)
                elif self.data_source == "happili":
                    # works only within ASTRON network
                    logger.warning(
                        "Cube {}: Assuming that data was transferred from happili keeping pipeline directory structure.".format(self.cube))
                    # get the happili path
                    if self.data_basedir == '':
                        self.data_basedir = self.sharpener_basedir

                    # go through the different beams
                    # check if the cubes and continuum images are there
                    # and link them to working directory
                    for beam in self.beam_list:

                        # for the cubes
                        cube_path = os.path.join(
                            self.data_basedir, "data/{0:02d}/cont/cubes/HI_image_cube{1}.fits".format(beam, self.cube))
                        link_name = os.path.join(
                            self.sharpener_basedir, "cube{0:02d}/HI_image_cube{1}.fits".format(beam, self.cube))
                        # check if link exists
                        if not os.path.exists(link_name):
                            logger.debug("Cube {0}: Creating link {1} to cube {2}".format(
                                self.cube, link_name, cube_path))
                            os.symlink(cube_path, link_name)
                        else:
                            logger.debug("Cube {0}: Cube {1} already exists".format(
                                self.cube, link_name))

                        # for the continuum images
                        link_name = os.path.join(
                            self.sharpener_basedir, "{0:02d}/image_mf.fits".format(beam))
                        # check if link exists
                        if not os.path.exists(link_name):
                            cont_path = os.path.join(
                                self.data_basedir, "{0:02d}/cont/cubes/HI_image_cube{1}.fits".format(beam, self.cube))
                            logger.debug("Cube {0}: Creating link {1} to cube {2}".format(
                                self.cube, link_name, cube_path))
                            os.symlink(cube_path, link_name)
                        else:
                            logger.debug("Cube {0}: Continuum image {1} already exists".format(
                                self.cube, link_name))

                    #data_basedir = os.path.join(self.data_basedir, self.taskid)
                    # happili_path = os.path.join(
                    #     data_basedir, "./[0-3][0-9]/line/cubes/HI_image_cube{}.fits".format(self.cube))
                    # # get the user name
                    # user_name = pwd.getpwuid(os.getuid())[0]

                    # rsync_cmd = 'rsync -Razuve ssh {0}@{1}:"{2}" {3}/'.format(
                    #     user_name, self.data_source, happili_path, self.cube_dir)
                    # logger.debug(rsync_cmd)

                    # try:
                    #     logger.info("Cube {0}: Copying data from {1}".format(
                    #         self.cube, self.data_source))
                    #     subprocess.check_call(
                    #         rsync_cmd, shell=True, stdout=FNULL, stderr=FNULL)
                    # except Exception as e:
                    #     logger.error(
                    #         "Cube {0}:Copying data from {1} ... Failed".format(self.cube, self.data_source))
                    #     logger.exception(e)
                    # else:
                    #     logger.info(
                    #         "Cube {0}:Copying data from {1} ... Done".format(self.cube, self.data_source))
                else:
                    error = "Did not recognize data source. Abort"
                    logger.error(error)
                    raise RuntimeError(error)

        # check the failed beams
        if len(failed_beams) == len(self.beam_list):
            self.abort_module(
                "Did not find cube {0} for all beams.".format(self.cube))
        elif len(failed_beams) != 0:
            logger.warning("Could not find cube {0} for beams {1}. Removing those beams".format(self.cube,
                                                                                                str(failed_beams)))
            for beam in failed_beams:
                self.beam_list.remove(beam)
            logger.warning("Will only process cube {0} for {1} beams ({2})".format(
                self.cube, len(self.beam_list), str(self.beam_list)))
        else:
            logger.info("Found cube {0} for all beams".format(self.cube))

    # ++++++++++++++++++++++++++++++++++++++++++++++++++
    def setup_sharpener(self):
        """
        Function to setup the parameters for sharpener
        """

        # if no template configfile was specified, get the default one
        if self.configfilename == '':
            # the default sharpener configfile is here:
            default_configfile = os.path.join(os.path.dirname(
                SHARPener.__file__), "sharpener_default.yml")
            # make sure it is there
            if os.path.exists(default_configfile):
                logger.info("Getting default sharpener config file from {}".format(
                    default_configfile))
            else:
                self.configfilename = default_configfile
