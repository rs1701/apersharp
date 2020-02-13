"""
Functionality to identify candidates for hi absorption

1. get all the sources from all beams 
and for each source
2. determine ratio of flux to noise
3. keep source only if ratio is below -3sigma (assumes good continuum subtraction)
"""

import os
import numpy as np
import glob
import logging
from astropy.table import Table

logger = logging.getLogger(__name__)


def get_source_spec_files(beam_list):
    """
    Function to get the spectrum files for all sources

    Args:
    -----
    beam_list (list(str)): List of directories of the beams of this cube

    Return:
    -------
    file_list (list(str)): List of file names with full path
    """

    logger.info("Getting spectra of sources")

    file_list = []

    for beam in beam_list:
        spec_files = glob.glob(os.path.join(beam, "sharpOut/spec/*txt"))
        if len(spec_files) == 0:
            logger.warning("No spectra found for beam {}".format(
                os.path.basename(beam)))
        else:
            spec_files.sort
            file_list.append(spec_files)

    logger.info("Getting spectra of sources ... Done")

    return file_list


def find_candidate(cube, beam_list):
    """
    Function to find candidates for absotion
    """

    # get a list of source files
    # ++++++++++++++++++++++++++
    file_list = get_source_spec_files(beam_list)

    # information to keep about sources that were found
    src_beam = []
    src_file_name = []

    # get the base directory of the cube
    basedir_cube = os.path.dirname(beam_list[0])

    # go through the source files
    for src_file in file_list:

        logger.info("Processing {}".format(src_file.split(basedir_cube)[-1]))

        # get the src name
        src_name = os.path.basename(src_file)

        # read the file
        src_data = Table.read(src_file, format="ascii")

        # try to determine the
        try:
            ratio = src_data["Flux [Jy]"] / src_data["Noise [Jy]"]
        except RuntimeWarning as rw:
            logger.warning("Calculating ratio failed. Ignoring source")
            logger.exception(rw)
