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
from modules.prepare import prepare


def run_apersharp(taskid, sharpener_basedir='', data_basedir=None, data_source='ALTA', steps=None, user=None, output_form="pdf", cubes="0", configfilename=None):
    """
    Main function run apersharp.

    Args:
    taskid (str): Name of the taskid to process
    sharpener_basedir (str): Directory for the directory where the data should be stored for processing
    data_basedir (str): (Remote-)directory where the taskid is located
    data_source (str): Name of remote server to get the data from
    steps (str): List of steps to run through.
    user (str): The username for getting data from Happili
    output_form (str): Choose between "pdf" and "html" for the output plots
    cubes (str): Select the cube to be processed. If "all", all cubes will be processed.
    configfilename (str): Default config file name to run SHARPener. Taken from SHARPener by default
    """

    # get the start time of the function call
    start_time = time()

    # check the output directory
    if sharpener_basedir == '':
        sharpener_basedir = os.path.join(os.getcwd(), taskid)
    else:
        sharpener_basedir = os.path.join(sharpener_basedir, taskid)
    if not os.path.exists(sharpener_basedir):
        os.mkdir(sharpener_basedir)

    # Create logfile
    logfile = os.path.join(sharpener_basedir, "apersharp_main.log")
    setup_logger('DEBUG', logfile=logfile)
    logger = logging.getLogger(__name__)

    # check the steps
    if steps is None:
        steps = ["prepare", "sharpener", "quicklook"]

    logger.info("#### Apersched called with:")
    logger.info("taskid: {}".format(taskid))
    logger.info("basedir: {}".format(sharpener_basedir))
    logger.info("steps: {}".format(str(steps)))
    logger.info("output format: {}".format(output_form))
    logger.info("cubes: {}".format(cubes))
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
        p.configfilename = configfilename

    # now go through the list of cubes
    for cube in cube_list:

        # start time for processing this cube
        start_time_cube = time()

        p = prepare()
        set_params(p)
        p.go()

        abort_function("No further functionality available")

        # get data

        # run sharpener

        # overwrite products


if __name__ == "__main__":

    # Main arguments
    parser = argparse.ArgumentParser(
        description='Run SHARPener on Apercal data')

    # main arguments
    parser.add_argument("taskid", type=str,
                        help='Taskid of the observation')

    parser.add_argument("--sharpener_basedir", type=str, default='',
                        help='Directory for the directory where the data should be stored for processing')

    parser.add_argument("--data_basedir", type=str, default='',
                        help='(Remote-)directory where the taskid is located')

    parser.add_argument("--data_source", type=str, default='ALTA',
                        help='Name of remote server to get the data from')

    parser.add_argument("--steps", type=list, default=None,
                        help='List of steps to run through.')

    parser.add_argument("--user", type=str, default=None,
                        help='The username for getting data from Happili.')

    parser.add_argument("--output_form", type=str, default='pdf',
                        help='Choose between "pdf" and "html" for the output plots')

    parser.add_argument("--cubes", type=str, default='0',
                        help='Select the cube to be processed. If "all", all cubes will be processed.')

    parser.add_argument("--configfilename", type=str, default='',
                        help='Default config file name to run SHARPener. Taken from SHARPener by default')

    args = parser.parse_args()

    run_apersharp(args.taskid, args.sharpener_basedir, data_basedir=args.data_basedir, data_source=args.data_source,
                  steps=args.steps, user=args.user, output_form=args.output_form, cubes=args.cubes, configfilename=args.configfilename)
