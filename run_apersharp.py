#! /usr/bin/python2

"""
Main module to run apersharp
"""

import os
import sys
import logging
import argparse
from time import time

from lib.setup_logger import setup_logger
from lib.abort_function import abort_function
from modules.apersharp import apersharp


def run_apersharp(taskid, sharpener_basedir='', data_basedir=None, data_source='ALTA', steps=None, user=None, beams='all', output_form="pdf", cubes="0", cont_src_resource="continuum", configfilename=None, do_sdss=False, n_cores=1):
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
    taskid (str): Name of the taskid to process
    sharpener_basedir (str): Directory for the directory where the data should be stored for processing
    data_basedir (str): (Remote-)directory where the taskid is located
    data_source (str): Name of remote server to get the data from
    steps (str): List of steps to run through.
    user (str): The username for getting data from Happili
    output_form (str): Choose between "pdf" and "html" for the output plots
    cubes (str): Select the cube to be processed. If "all", all cubes will be processed.
    cont_src_resource (str): Select what should be used for continuum source counterparts.
    configfilename (str): Default config file name to run SHARPener. Taken from SHARPener by default
    do_sdss (bool): Enable/Disable SDSS cross-matching of radio continuum sources
    n_cores (int): Number of cores for running sharpener in parallel
    """

    # get the start time of the function call
    start_time = time()

    # check the output directory
    if sharpener_basedir == '':
        sharpener_basedir = os.path.join(os.getcwd(), "{}".format(taskid))
    else:
        sharpener_basedir = os.path.join(
            sharpener_basedir, "{}".format(taskid))
    if not os.path.exists(sharpener_basedir):
        os.mkdir(sharpener_basedir)

    # Create logfile
    logfile = os.path.join(sharpener_basedir, "apersharp_main.log")
    setup_logger('DEBUG', logfile=logfile)
    logger = logging.getLogger(__name__)

    logger.info("Apersharp processing of taskid {}".format(taskid))

    # check the steps
    if steps is None:
        steps = ["get_data", "setup_sharpener",
                 "run_sharpener", "collect_results", "clean_up"]
    else:
        steps = steps.split(",")

    logger.info("#### Aperscharp called with:")
    logger.info("taskid: {}".format(taskid))
    logger.info("basedir: {}".format(sharpener_basedir))
    logger.info("steps: {}".format(str(steps)))
    logger.info("output format: {}".format(output_form))
    logger.info("cubes: {}".format(cubes))
    #logger.info(" ")
    logger.info("do_sdss: {}".format(do_sdss))
    logger.info("####")

    # get a list of cubes
    cube_list = cubes.split(",")

    def set_params(p):
        """
        Helper to set the base parameters for the module
        """

        p.taskid = taskid
        p.sharpener_basedir = sharpener_basedir
        p.data_basedir = data_basedir
        p.data_source = data_source
        p.output_form = output_form
        p.cube = cube
        p.steps = steps
        p.do_sdss = do_sdss
        p.n_cores = n_cores
        p.cont_src_resource = cont_src_resource
        if beams is None:
            p.beam_list = np.array("{}".format(str(beam).zfill(2))
                                   for beam in np.arange(p.NBEAMS))
        else:
            p.beam_list = beams.split(",")
        p.configfilename = configfilename

    # now go through the list of cubes
    for cube in cube_list:

        # start time for processing this cube
        start_time_cube = time()

        logger.info(
            "Processing cube {0} of taskid {1} with SHARPener".format(cube, taskid))

        p = apersharp()
        set_params(p)
        try:
            p.go()
        except Exception as e:
            logger.warning(
                "Processing cube {0} of taskid {1} with SHARPener ... Failed ({2:.0f}s)".format(cube, taskid, time() - start_time))
            logger.exception(e)
        else:
            logger.info(
                "Processing cube {0} of taskid {1} with SHARPener ... Done ({2:.0f})".format(cube, taskid, time() - start_time))

    logger.info("Apershap finished processing of taskid {0} after {1:.0f}s".format(
        taskid, time() - start_time))


if __name__ == "__main__":

    # Main arguments
    parser = argparse.ArgumentParser(
        description='Run SHARPener on Apercal data')

    # main arguments
    parser.add_argument("taskid", type=int,
                        help='Taskid of the observation')

    parser.add_argument("--sharpener_basedir", type=str, default='',
                        help='Directory for the directory where the data should be stored for processing')

    parser.add_argument("--data_basedir", type=str, default='',
                        help='(Remote-)directory where the taskid is located')

    parser.add_argument("--data_source", type=str, default='ALTA',
                        help='Name of remote server to get the data from')

    parser.add_argument("--steps", type=str, default=None,
                        help='List of steps to run through.')

    parser.add_argument("--user", type=str, default=None,
                        help='The username for getting data from Happili.')

    parser.add_argument("--output_form", type=str, default='pdf',
                        help='Choose between "pdf" and "html" for the output plots')

    parser.add_argument("--beams", type=str, default='all',
                        help='Comma-separated list of beams given as a single string or all.')

    parser.add_argument("--cubes", type=str, default='0',
                        help='Select the cube to be processed. If "all", all cubes will be processed.')

    parser.add_argument("--cont_src_resource", type=str, default='image',
                        help='Select the resources to get continuum source for HI absorption source')

    parser.add_argument("--configfilename", type=str, default=None,
                        help='Default config file name to run SHARPener. Taken from SHARPener by default')

    parser.add_argument("--n_cores", type=int, default=1,
                        help='Number of cores for running sharpener')

    parser.add_argument("--do_sdss", action="store_true", default=False,
                        help='Enable sdss cross-matching')

    args = parser.parse_args()

    run_apersharp(args.taskid, args.sharpener_basedir, data_basedir=args.data_basedir, data_source=args.data_source,
                  steps=args.steps, user=args.user, beams=args.beams, output_form=args.output_form, cubes=args.cubes, cont_src_resource=args.cont_src_resource, configfilename=args.configfilename, do_sdss=args.do_sdss, n_cores=args.n_cores)
