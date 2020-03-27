#! /usr/bin/python2

"""
Main module to run apersharp
"""

import os
import sys
import logging
import argparse
from time import time
import numpy as np

from lib.setup_logger import setup_logger
from lib.abort_function import abort_function
from modules.apersharp import apersharp


# def run_apersharp(taskid, sharpener_basedir, data_basedir=None, data_source='ALTA', steps=None, user=None, beams='all', output_form="pdf", cubes="0", cont_src_resource="continuum", configfilename=None, no_sdss=False, n_cores=1):
def run_apersharp(taskid, sharpener_basedir, apersharp_configfilename=None, steps=None, beams=None, cubes=None, n_cores=None):
    """
    Main function run apersharp.

    Description:
    ============
    This function manages retrieving Apertif imaging survey cubes and continuum images and runs
    SHARPener to search for HI absorption.

    If no steps are provided, then all are executed, i.e.,
    steps = ["get_data", "setup_sharpener", "run_sharpener", "collect_results"]

    Args:
    =====
    taskid (str): Name of the taskid to process. Multiple taskids are separated using a comma
    sharpener_basedir (str): Directory for the directory where the data should be stored for processing
    apersharp_configfile (str): Set the config file used by Apersharp
    steps (str): List of steps to run through.
    cubes (str): Select the cube to be processed. If "all", all cubes will be processed.
    n_cores (int): Number of cores for running sharpener in parallel
    """

    start_time = time()

    # get a list of taskids
    taskid_list = taskid.split(",")

    # Check base directory and create it if necessary
    if sharpener_basedir == '':
        sharpener_basedir = os.getcwd()
    else:
        sharpener_basedir = os.path.abspath(sharpener_basedir)
    if not os.path.exists(sharpener_basedir):
        os.mkdir(sharpener_basedir)

    logfile = os.path.join(sharpener_basedir, "apersharp_main.log")
    setup_logger('DEBUG', logfile=logfile)
    logger = logging.getLogger(__name__)

    logger.info("#### Apersharp processing started ####")
    logger.info("Processing taskids: {}".format(str(taskid_list)))
    logger.info("########")

    for taskid in taskid_list:

        # get the start time of the function call
        start_time_taskid = time()

        logger.info("#### Apersharp processing of taskid {}".format(taskid))

        # check the output directory
        # if sharpener_basedir == '':
        #     sharpener_basedir = os.path.join(os.getcwd(), "{}".format(taskid))
        # else:
        sharpener_basedir_taskid = os.path.join(
            sharpener_basedir, "{}".format(taskid))
        if not os.path.exists(sharpener_basedir_taskid):
            os.mkdir(sharpener_basedir_taskid)

        # Create logfile
        # logfile = os.path.join(sharpener_basedir_taskid,
        #                        "{}_apersharp.log".format(taskid))
        # setup_logger('DEBUG', logfile=logfile)
        # logger = logging.getLogger(__name__)

        # check the steps
        # if steps is None:
        #     steps_list = ["get_data", "setup_sharpener",
        #                   "run_sharpener", "collect_results", "clean_up"]
        # else:
        #     steps_list = steps.split(",")

        # if beams is None:
        #     beam_list = np.array(["{}".format(str(beam).zfill(2))
        #                           for beam in np.arange(40)])
        # elif beams == 'all':
        #     beam_list = np.array(["{}".format(str(beam).zfill(2))
        #                           for beam in np.arange(40)])
        # else:
        #     beam_list = np.array(beams.split(","))

        logger.info("##")
        logger.info("# Apersharp called with:")
        logger.info("# taskid: {}".format(taskid))
        logger.info("# basedir: {}".format(sharpener_basedir_taskid))
        # logger.info("# steps: {}".format(str(steps)))
        # logger.info("# output format: {}".format(output_form))
        # logger.info("# cubes: {}".format(cubes))
        # logger.info("# beams: {}".format(str(beam_list)))
        # #logger.info(" ")
        # logger.info("# do_sdss: {}".format(do_sdss))
        # logger.info("# n_cores: {}".format(n_cores))
        logger.info("##")

        def set_params(p):
            """
            Helper to set/overwrite the base parameters for the module
            """

            # overwrite the number of cores
            if n_cores is not None:
                logger.info(
                    "Overwriting default setting for number of cores: {}".format(n_cores))
                p.n_cores = n_cores
            # overwrite the steps
            if steps is not None:
                logger.info(
                    "Overwriting default setting for steps: {}".format(steps))
                p.steps_list = steps.split(",")
            # overwrite beams
            if beams is not None:
                logger.info(
                    "Ovewriting default list of beams: {}".format(beams))
                p.beam_list = np.array([str(beam).zfill(2)
                                        for beam in beams.split(",")])
            elif beams == "all":
                p.beam_list = np.array(["{}".format(str(beam).zfill(2))
                                        for beam in np.arange(40)])
            # overwrite list of cubes
            if cubes is not None:
                logger.info(
                    "Overwriting default settings for list of cubes: {}".format(cubes))
                p.cube_list = cubes.split(",")

            p.taskid = taskid
            p.sharpener_basedir = sharpener_basedir_taskid

            # p.data_basedir = data_basedir
            # p.data_source = data_source
            # p.output_form = output_form
            # p.cube = cube
            # p.steps = steps_list
            # p.do_sdss = do_sdss
            # p.n_cores = n_cores
            # p.cont_src_resource = cont_src_resource
            # p.beam_list = beam_list
            # p.configfilename = configfilename

        logfile_taskid = os.path.join(sharpener_basedir_taskid,
                                      "{}_apersharp.log".format(taskid))
        setup_logger('DEBUG', logfile=logfile_taskid)
        logger = logging.getLogger(__name__)

        # start time for processing this cube
        start_time_cube = time()

        p = apersharp(config_file=apersharp_configfilename)
        set_params(p)
        p.logfile = logfile_taskid
        try:
            p.go()
        except Exception as e:
            setup_logger('DEBUG', logfile=logfile, new_logfile=False)
            logger = logging.getLogger(__name__)
            logger.warning(
                "Processing of taskid {0} ... Failed ({1:.0f}s)".format(taskid, time() - start_time_cube))
            logger.exception(e)
        else:
            setup_logger('DEBUG', logfile=logfile, new_logfile=False)
            logger = logging.getLogger(__name__)
            logger.info(
                "Processing of taskid {0} ... Done ({1:.0f})".format(taskid, time() - start_time_cube))

        logger.info("## Apershap finished processing of taskid {0} after {1:.0f}s".format(
            taskid, time() - start_time_taskid))

    logger.info("#### Apersharp processing finished after {0:.0f}s ####".format(
        time() - start_time))


if __name__ == "__main__":

    # Main arguments
    parser = argparse.ArgumentParser(
        description='Run SHARPener on Apercal data')

    # main arguments
    parser.add_argument("taskid", type=str,
                        help='Taskid of the observation. Multiple taskids can be separated using commas.')

    parser.add_argument("sharpener_basedir", type=str,
                        help='Directory for the directory where the data should be stored for processing')

    # parser.add_argument("--data_basedir", type=str, default='',
    #                     help='(Remote-)directory where the taskid is located')

    # parser.add_argument("--data_source", type=str, default='ALTA',
    #                     help='Name of remote server to get the data from')

    parser.add_argument("--steps", type=str, default=None,
                        help='List of steps to run through.')

    # parser.add_argument("--user", type=str, default=None,
    #                     help='The username for getting data from Happili.')

    # parser.add_argument("--output_form", type=str, default='pdf',
    #                     help='Choose between "pdf" and "html" for the output plots')

    parser.add_argument("--beams", type=str, default=None,
                        help='Comma-separated list of beams given as a single string or all. Will overwrite config file setting.')

    parser.add_argument("--cubes", type=str, default=None,
                        help='Comma-separated list of cubes. Will overwrite config file setting.')

    # parser.add_argument("--cont_src_resource", type=str, default='image',
    #                     help='Select the resources to get continuum source for HI absorption source')

    parser.add_argument("--config", type=str, default=None,
                        help='Specify a user-defined config file for Apersharp.')

    parser.add_argument("--n_cores", type=int, default=None,
                        help='Number of cores for running sharpener. Will overwrite config file setting.')

    # parser.add_argument("--no_sdss", action="store_true", default=False,
    #                     help='Enable sdss cross-matching')

    args = parser.parse_args()

    # run_apersharp(args.taskid, args.sharpener_basedir, data_basedir=args.data_basedir, data_source=args.data_source,
    #               steps=args.steps, user=args.user, beams=args.beams, output_form=args.output_form, cubes=args.cubes, cont_src_resource=args.cont_src_resource, configfilename=args.configfilename, no_sdss=args.no_sdss, n_cores=args.n_cores)

    run_apersharp(args.taskid, args.sharpener_basedir, apersharp_configfilename=args.config,
                  steps=args.steps, beams=args.beams, cubes=args.cubes, n_cores=args.n_cores)
