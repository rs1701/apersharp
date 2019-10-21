#! /usr/bin/python2

"""
Main module to run apersharp
"""

import os
import sys
import logging
import argparse
from lib.setup_logger import setup_logger


def run_apersharp(taskid, sharpener_basedir='', data_basedir=None, steps=None, user=None, output_form="pdf", cubes="0", configfilename=None):
    """
    Main function run apersharp.

    Args:
    taskid (str): Name of the taskid to process
    sharpener_basedir (str): Directory for the directory where the data should be stored for processing
    data_basedir (str): (Remote-)directory where the taskid is located
    steps (str): List of steps to run through.
    user (str): The username for getting data from Happili
    output_form (str): Choose between "pdf" and "html" for the output plots
    cubes (str): Select the cube to be processed. If "all", all cubes will be processed.
    configfilename (str): Default config file name to run SHARPener. Taken from SHARPener by default
    """

    def abort_function(abort_message):
        """
        Simple abort function if non-existing features are triggered
        """
        logger = logging.getLogger(__name__)
        logger.error(abort_message)
        raise RuntimeError(abort_message)

    # Create logfile
    logfile = os.path.join(sharpener_basedir, "test.log")
    setup_logger('DEBUG', logfile=logfile)
    logger = logging.getLogger(__name__)

    abort_function("No further functionality available")

    # Check local directory for available data

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

    parser.add_argument("--steps", type=str, default=None,
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

    run_apersharp(args.taskid, args.sharpener_basedir, data_basedir=args.data_basedir,
                  steps=args.steps, user=args.user, output_form=args.output_form, cubes=args.cubes, configfilename=args.configfilename)
