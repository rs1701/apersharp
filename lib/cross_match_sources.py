"""
Functionality to match sources across beams (maybe also cubes)

1. get all the sources from all beams and create dict with source name, RA, DEC, cube and beam
2. Sort by beam
3. Go through the list of sources
    3.0.5 Check if source already has a match
    3.1. Remove sources with beams that do not overlap
    3.2. Remove sources with same beam
    3.3. Calculate distance on sky based on SkyCoord
    3.4. Check whether there is one or more sources with distance < 2 arcsec
        - One beam can overlap with up to 2 other beams for this comparison
        - except beam 00 which could have 3 other beams
    3.5. if match is found add source name, RA, DEC and beam of match to the selected source and its matches

2. determine ratio of flux to noise
3. keep source only if ratio is below -3sigma (assumes good continuum subtraction)
"""

import os
import numpy as np
import glob
import logging
from astropy.table import Table, vstack, hstack

logger = logging.getLogger(__name__)


def get_all_sources_of_cube(output_file_name, cube_dir, taskid=None, cube_nr=None, beam_list=None, src_file="radio_sdss_src_match.csv"):
    """
    Function to collect the information from all sources in one file

    Use the radio-SDSS source file
    """

    # if the cube number was not given, try to get from the name
    if cube_nr is None:
        cube_nr = os.path.basename(cube_dir).split("_")[-1]

    # if taskid was not given, try to get from the directory
    if taskid is None:
        taskid = os.path.dirname(cube_dir).split("/")[-1]

    logger.info("Collecting source information from all beams")

    logger.debug("Processing cube {0} of taskid {1}".format(cube_nr, taskid))

    # get a list of beams
    if beam_list is None:
        beam_list = glob.glob(os.path.join(cube_dir, "??"))
        if len(beam_list) == 0:
            error = "Did not find any beams in . Abort"
            logger.error(error)
            raise RuntimeError(error)
        beam_list.sort()
        beam_list = np.array([os.path.basename(beam) for beam in beam_list])

    # for storing the full list:
    full_list = []

    # go through the list of beams
    for beam in beam_list:

        logger.debug("Processing beam {}".format(beam))

        # set the file name for this beam
        csv_file_name = os.path.join(
            cube_dir, "{0}/sharpOut/abs/{1}".format(beam, src_file))

        # make sure the file exists
        if not os.path.exists(csv_file_name):
            logger.warning(
                "Could not find source file {}".format(csv_file_name))
            continue

        # read the data
        src_data = Table.read(csv_file_name, format="ascii.csv")

        # number of sources
        n_src = np.size(src_data['ID'])
        logger.debug("Found {} sources".format(n_src))

        # rename the ID column
        src_data.rename_column('ID', 'Beam_Source_ID')

        # create a new columns for ID, taskid, beam and cube
        src_id = np.array(["{0}_C{1}_B{2}_{3}".format(
            taskid, cube_nr, beam.zfill(2), src_name) for src_name in src_data['J2000']])
        src_beam = np.array([beam for i in range(n_src)])
        src_cube = np.array([cube_nr for i in range(n_src)])

        # create a new table with these three columns
        new_table = Table([src_id, src_cube, src_beam],
                          names=["Source_ID", "Cube", "Beam"])

        # merge with source table
        new_src_table = hstack([new_table, src_data])

        # merge with full list
        if np.size(full_list) == 0:
            full_list = new_src_table
        else:
            full_list = vstack([full_list, new_src_table])

        logger.debug("Processing beam {} ... Done".format(beam))

    # save the file if there is something to save
    if np.size(full_list) != 0:
        full_list.write(output_file_name, format="ascii.csv")
        logger.info("Collecting source information from all beams ... Done")
    else:
        error = "Table with all sources is emtpy. Abort"
        logger.error(error)
        logger.error("Collecting source information from all beams ... Failed")
        raise RuntimeError(error)
