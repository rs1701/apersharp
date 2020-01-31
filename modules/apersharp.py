import os
import subprocess
import numpy as np
import logging
import pwd
import glob
import yaml
import shutil
import zipfile
import io
import multiprocessing as mp
import functools


from lib.abort_function import abort_function
from lib.sharpener_pipeline import sharpener_pipeline
from base import BaseModule

import sharpener
#from sharpener.srun_sharpener_mp import run_sharpener as sharpener_mp

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

            self.setup_sharpener()

            logger.info("Setting up sharpner ... Done")
        else:
            logger.info("Skipping setting up sharpener")

        # run sharpener
        if "run_sharpener" in self.steps:
            logger.info("Running sharpener")

            self.run_sharpener()

            logger.info("Running sharpener ... Done")
        else:
            logger.info("Skipping running sharpener")

        # collect results from sharpener
        if "collect_results" in self.steps:
            logger.info("Collecting results from sharpener")

            self.collect_sharpener_results()

            logger.info("Collecting results from sharpener ... Done")
        else:
            logger.info("Skipping collecting results from sharpener")

        # clean up by removing the images and cubes
        if "clean_up" in self.steps:
            logger.info("Removing cubes and continuum images")

            self.clean_up()

            logger.info("Removing cubes and continuum images ... Done")
        else:
            logger.warning("Did not remove cubes and continuum images. WARNING. Be aware of the disk space used by the fits files")



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
                beam_dir = os.path.join(self.cube_dir, "{}".format(beam))
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
                                     stdout=FNULL, stderr=FNULL)
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
            alta_cmd, shell=True, stdout=FNULL, stderr=FNULL)

        return return_msg

    # ++++++++++++++++++++++++++++++++++++++++++++++++++
    def get_data(self):
        """
        Function to get the HI cubes and continuum images.

        """

        beam_dir = np.arange(self.NBEAMS)
        
        # storing failed beams
        failed_beams = []
        # self.continuum_image_list = []


        # Going through the beams to get the data:
        for beam in self.beam_list:            

            # check first if they do not already exists
            cube_path = self.get_cube_path(beam)
            if os.path.exists(cube_path):
                logger.info(
                    "Cube {0}: Found cube for beam {1}".format(self.cube, beam))

                # check also the continuum image
                continuum_image_path = self.get_cont_path(beam)
                if os.path.exists(continuum_image_path):
                    logger.info("Cube {0}: Found continuum image for beam {1}".format(self.cube, beam))
                    # self.continuum_image_list.append(continuum_image_path)
                else:
                    error = "Did not find continuum image for beam {}".format(beam)
                    logger.error(error)
                    raise RuntimeError(error)

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
                            cube_name = "HI_image_cube{}.fits".format(
                                self.cube)
                            alta_beam_cube_path = os.path.join(
                                alta_taskid_beam_dir, "{}".format(cube_name))
                            # check that path exists on alta
                            if self.check_alta_path(alta_beam_cube_path) == 0:
                                logger.info("Found cube on ALTA in {}".format(
                                    alta_beam_cube_path))
                            else:
                                # make empty again when no image was found
                                cube_name = ''
                            # if there is no cube, do not process it
                            if cube_name == '':
                                logger.warning(
                                    "No cube {0} found on ALTA for beam {1} of taskid {2}".format(self.cube, beam, self.taskid))
                                failed_beams.append(beam)
                            else:
                                # create directory for beam in the directory
                                cube_beam_dir = self.get_cube_beam_dir(beam)
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
                                
                                # getting continuum fits image
                                if self.cont_src_resource == "image":
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
                                        if not os.path.exists(os.path.join(self.get_cube_dir(), os.path.basename(alta_beam_image_path))):
                                            # copy the continuum image to this directory
                                            return_msg = self.getdata_from_alta(
                                                alta_beam_image_path, cube_beam_dir)
                                            if return_msg == 0:
                                                logger.info("Getting image of beam {0} of taskid {1} ... Done".format(
                                                    beam, self.taskid))
                                            else:
                                                error = "Getting image of beam {0} of taskid {1} ... Failed".format(
                                                    beam, self.taskid)
                                                logger.error(error)
                                                raise RuntimeError(error)

                                            # rename the file
                                            original_continuum_image_name = os.path.join(cube_beam_dir, continuum_image_name)
                                            continuum_image_name = os.path.join(cube_beam_dir, "image_mf.fits")
                                            logger.info("Renaming {0} to {1}".format(original_continuum_image_name, continuum_image_name))
                                            os.rename(original_continuum_image_name, continuum_image_name)

                                            # self.continuum_image_list.append(
                                            #     continuum_image_name)
                                        else:
                                            logger.info("Image of beam {0} of taskid {1} already on disk".format(
                                                beam, self.mosaic_taskid))
                        else:
                            logger.warning("Did not find beam {0} of taskid {1}".format(
                                beam, self.taskid))
                            # remove the beam
                            failed_beams.append(beam)
                elif self.data_source == "happili":
                    self.abort_function("Getting data from happili not supported at the moment")

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
                            self.data_basedir, "data/{0}/cont/cubes/HI_image_cube{1}.fits".format(beam, self.cube))
                        link_name = os.path.join(
                            self.sharpener_basedir, "cube{0}/HI_image_cube{1}.fits".format(beam, self.cube))
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
                            self.sharpener_basedir, "{}/image_mf.fits".format(beam))
                        # check if link exists
                        if not os.path.exists(link_name):
                            cont_path = os.path.join(
                                self.data_basedir, "{0}/cont/cubes/HI_image_cube{1}.fits".format(beam, self.cube))
                            logger.debug("Cube {0}: Creating link {1} to cube {2}".format(
                                self.cube, link_name, cube_path))
                            os.symlink(cube_path, link_name)
                        else:
                            logger.debug("Cube {0}: Continuum image {1} already exists".format(
                                self.cube, link_name))

                    # data_basedir = os.path.join(self.data_basedir, self.taskid)
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

        logger.info("Setting up sharpener")

        # if no template configfile was specified, get the default one
        if self.configfilename is None:
            # the default sharpener configfile is here:
            default_configfile = os.path.join(os.path.dirname(
                sharpener.__file__), "sharpener_default.yml")
            # make sure it is there
            if os.path.exists(default_configfile):
                logger.info("Using default sharpener config file from {}".format(
                    default_configfile))
            else:
                error = "Could not find default sharpener config file in {}. Abort".format(
                    self.configfilename)
                logger.error(error)
                raise RuntimeError(error)
            self.configfilename = default_configfile
        else:
            # check that the file exist
            if os.path.exists(self.configfilename):
                logger.info("Using specified config file: {}".format(
                    self.configfilename))
            else:
                error = "Could not find the specificed config file: {}. Abort".format(
                    self.configfilename)
                logger.error(error)
                raise RuntimeError(error)

        # go through the list of beams, copy the config file and adjust the settings
        for beam in self.beam_list:
            logger.info(
                "Cube {0}: Setting up sharpener for beam {0}".format(self.cube, beam))

            # get beam directory for given cube
            cube_beam_dir = self.get_cube_beam_dir(beam)

            # configfile of the beam
            beam_configfilename = os.path.join(
                cube_beam_dir, "beam_{0}_{1}".format(beam.zfill(2), os.path.basename(self.configfilename).replace("default", "settings")))

            # copy the file
            shutil.copy2(self.configfilename, beam_configfilename)

            # open and read the default sharpener setup file
            with open("{0}".format(beam_configfilename)) as stream:
                sharpener_settings = yaml.load(stream)

            # need to cut the work directory because of Miriad string limits
            sharpener_settings['general']['workdir'] = "./"
            # sharpener_settings['general']['workdir'] = "{0:s}/".format(
            #     beam)
            sharpener_settings['general']['contname'] = os.path.basename(self.get_cont_path(beam))
            sharpener_settings['general']['cubename'] = os.path.basename(self.get_cube_path(
                beam))

            # make sure that certain steps are disabled
            sharpener_settings['source_catalog']['enable'] = False
            sharpener_settings['simulate_continuum']['enable'] = False
            sharpener_settings['polynomial_subtraction']['enable'] = False
            sharpener_settings['hanning']['enable'] = False

            sharpener_settings['source_finder']['enable'] = True

            sharpener_settings['source_catalog']['enable'] = False

            sharpener_settings['sdss_match']['enable'] = self.do_sdss
            sharpener_settings['sdss_match']['zunitCube'] = "Hz"
            sharpener_settings['sdss_match']['plot_format'] = "pdf"

            sharpener_settings['spec_ex']['enable'] = True
            sharpener_settings['spec_ex']['chrom_aberration'] = False

            sharpener_settings['abs_plot']['enable'] = True
            sharpener_settings['abs_plot']['fixed_scale'] = False
            sharpener_settings['abs_plot']['plot_contImage'] = True
            # for the detailed plots, 3 rows
            sharpener_settings['abs_plot']['channels_per_plot'] = 406

            with io.open(beam_configfilename, 'w', encoding='utf8') as outfile:
                yaml.dump(sharpener_settings, outfile,
                          default_flow_style=False, allow_unicode=True)

            logger.info(
                "Cube {0}: Setting up sharpener for beam {0} ... Done".format(self.cube, beam))

        logger.info("Setting up sharpener ... Done")

    # ++++++++++++++++++++++++++++++++++++++++++++++++++
    def run_sharpener(self):
        """
        Function to run sharpener in parallel
        """

        logger.info("Cube {0}: Running sharpener".format(self.cube))

        beam_directory_list = np.array([
            self.get_cube_beam_dir(beam) for beam in self.beam_list])

        # index array for pool based on the number of files
        beam_count = np.arange(np.size(beam_directory_list))

        # create pool object with number of processes
        pool = mp.Pool(processes=self.n_cores)

        # create function iterater to provide additional arguments
        fct_partial = functools.partial(
            sharpener_pipeline, beam_directory_list, True, True, True, self.do_sdss)

        # create and run map
        pool.map(fct_partial, beam_count)
        pool.close()
        pool.join()

        logger.info("Cube {0}: Running sharpener ... Done".format(
            self.cube, str(self.beam_list)))

    # ++++++++++++++++++++++++++++++++++++++++++++++++++
    def collect_sharpener_results(self):
        """
        Function to combine the results
        """

        logger.info(
            "Cube {0}: Collecting the results from sharpener".format(self.cube))

        # Create a zip file with all the plots
        # ++++++++++++++++++++++++++++++++++++

        logger.info("Creating zip files for plots")

        cube_beam_dir_pattern = self.get_cube_beam_dir("??")

        # list of plots
        plot_list = glob.glob(os.path.join(
            cube_beam_dir_pattern, "sharpOut/plot/*all_plots*.pdf"))

        if len(plot_list) != 0:

            plot_list.sort()

            with zipfile.ZipFile(os.path.join(self.get_cube_dir(), "cube_{}_all_plots.zip".format(self.cube)), 'w') as myzip:

                for plot in plot_list:
                    myzip.write(plot, os.path.basename(plot))

            logger.info("Creating zip files for plots ... Done")
        else:
            logger.warning("No files to zip.")

        logger.info("Creating zip files for source list")

        csv_list = glob.glob(os.path.join(
            cube_beam_dir_pattern, "sharpOut/abs/mir_src_sharpener.csv"))
        csv_sdss_list = glob.glob(os.path.join(
            cube_beam_dir_pattern, "sharpOut/abs/beam??_sdss_src.csv"))
        csv_sdss_radio_list = glob.glob(os.path.join(
            cube_beam_dir_pattern, "sharpOut/abs/beam??_radio_sdss_src.csv"))
        karma_list = glob.glob(os.path.join(
            cube_beam_dir_pattern, "sharpOut/abs/karma_src_sharpener.ann"))

        # do not create if there are no source at all
        if len(csv_list) != 0:

            with zipfile.ZipFile(os.path.join(self.get_cube_dir(), "cube_{}_all_sources.zip".format(self.cube)), 'w') as myzip:

                if len(csv_list) != 0:
                    csv_list.sort()
                    for csv in csv_list:
                        myzip.write(csv, "beam_{0:s}_{1:s}".format(csv.replace(
                            os.path.dirname(cube_beam_dir_pattern), "").split("/")[0], os.path.basename(csv)))

                if len(csv_sdss_list) != 0:
                    csv_sdss_list.sort()
                    for csv in csv_sdss_list:
                        myzip.write(csv, os.path.basename(csv))

                if len(csv_sdss_radio_list) != 0:
                    csv_sdss_radio_list.sort()
                    for csv in csv_sdss_radio_list:
                        myzip.write(csv, os.path.basename(csv))

                if len(karma_list) != 0:
                    karma_list.sort()
                    for karma in karma_list:
                        myzip.write(karma, "beam_{0:s}_{1:s}".format(karma.replace(
                            os.path.dirname(cube_beam_dir_pattern), "").split("/")[0], os.path.basename(karma)))

            logger.info("Creating zip files for source list ... Done")
        else:
            logger.warning("No files to zip.")

        logger.info(
            "Cube {0}: Collecting the results from sharpener".format(self.cube))

    # ++++++++++++++++++++++++++++++++++++++++++++++++++
    def clean_up(self):
        """
        Function to remove cubes and continuum fits files
        """

        logger.info("Cube {}: Removing cubes and continuum fits files".format(self.cube))

        for beam in self.beam_list:

            # get the path to the cube
            cube_file = self.get_cube_path(beam)
            # remove cube
            os.remove(cube_file)

            # get the path to the continuum image
            continuum_file = self.get_cont_path(beam)
            # removing continum image
            os.remove(continuum_file)

        logger.info(
            "Cube {}: Removing cubes and continuum fits files ... Done".format(self.cube))
