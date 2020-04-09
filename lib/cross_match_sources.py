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
import astropy.units as units
from astropy.coordinates import SkyCoord

logger = logging.getLogger(__name__)


def get_beam_overlap_matrix():
    """
    Function to create matrix describing the overlap of compound beams
    """

    overlap_matrix = np.identity(40, dtype=np.float64)

    overlap_matrix[0, 17] = 1
    overlap_matrix[0, 24] = 1
    overlap_matrix[0, 18] = 1
    overlap_matrix[0, 23] = 1
    overlap_matrix[1, 2] = 1
    overlap_matrix[1, 8] = 1
    overlap_matrix[2, 3] = 1
    overlap_matrix[2, 8] = 1
    overlap_matrix[2, 9] = 1
    overlap_matrix[3, 4] = 1
    overlap_matrix[3, 9] = 1
    overlap_matrix[3, 10] = 1
    overlap_matrix[4, 5] = 1
    overlap_matrix[4, 10] = 1
    overlap_matrix[4, 11] = 1
    overlap_matrix[5, 6] = 1
    overlap_matrix[5, 11] = 1
    overlap_matrix[5, 12] = 1
    overlap_matrix[6, 7] = 1
    overlap_matrix[6, 12] = 1
    overlap_matrix[6, 13] = 1
    overlap_matrix[7, 13] = 1
    overlap_matrix[7, 14] = 1
    overlap_matrix[8, 9] = 1
    overlap_matrix[8, 15] = 1
    overlap_matrix[9, 10] = 1
    overlap_matrix[9, 15] = 1
    overlap_matrix[9, 16] = 1
    overlap_matrix[10, 11] = 1
    overlap_matrix[10, 16] = 1
    overlap_matrix[10, 17] = 1
    overlap_matrix[11, 12] = 1
    overlap_matrix[11, 17] = 1
    overlap_matrix[11, 18] = 1
    overlap_matrix[12, 13] = 1
    overlap_matrix[12, 18] = 1
    overlap_matrix[12, 19] = 1
    overlap_matrix[13, 14] = 1
    overlap_matrix[13, 19] = 1
    overlap_matrix[13, 20] = 1
    overlap_matrix[14, 20] = 1
    overlap_matrix[15, 16] = 1
    overlap_matrix[15, 21] = 1
    overlap_matrix[15, 22] = 1
    overlap_matrix[16, 17] = 1
    overlap_matrix[16, 22] = 1
    overlap_matrix[16, 23] = 1
    overlap_matrix[17, 18] = 1
    overlap_matrix[17, 23] = 1
    overlap_matrix[17, 24] = 1
    overlap_matrix[18, 19] = 1
    overlap_matrix[18, 24] = 1
    overlap_matrix[18, 25] = 1
    overlap_matrix[19, 20] = 1
    overlap_matrix[19, 25] = 1
    overlap_matrix[19, 26] = 1
    overlap_matrix[20, 26] = 1
    overlap_matrix[21, 22] = 1
    overlap_matrix[21, 27] = 1
    overlap_matrix[22, 23] = 1
    overlap_matrix[22, 27] = 1
    overlap_matrix[22, 28] = 1
    overlap_matrix[23, 24] = 1
    overlap_matrix[23, 28] = 1
    overlap_matrix[23, 29] = 1
    overlap_matrix[24, 25] = 1
    overlap_matrix[24, 29] = 1
    overlap_matrix[24, 30] = 1
    overlap_matrix[25, 26] = 1
    overlap_matrix[25, 30] = 1
    overlap_matrix[25, 31] = 1
    overlap_matrix[26, 31] = 1
    overlap_matrix[26, 32] = 1
    overlap_matrix[27, 28] = 1
    overlap_matrix[27, 33] = 1
    overlap_matrix[27, 34] = 1
    overlap_matrix[28, 29] = 1
    overlap_matrix[28, 34] = 1
    overlap_matrix[28, 35] = 1
    overlap_matrix[29, 30] = 1
    overlap_matrix[29, 35] = 1
    overlap_matrix[29, 36] = 1
    overlap_matrix[30, 31] = 1
    overlap_matrix[30, 36] = 1
    overlap_matrix[30, 37] = 1
    overlap_matrix[31, 32] = 1
    overlap_matrix[31, 37] = 1
    overlap_matrix[31, 38] = 1
    overlap_matrix[32, 38] = 1
    overlap_matrix[32, 39] = 1
    overlap_matrix[33, 34] = 1
    overlap_matrix[34, 35] = 1
    overlap_matrix[35, 36] = 1
    overlap_matrix[36, 37] = 1
    overlap_matrix[37, 38] = 1
    overlap_matrix[38, 39] = 1

    # make symmetric
    overlap_matrix = overlap_matrix + overlap_matrix.T - \
        np.diag(overlap_matrix.diagonal())

    return overlap_matrix


def match_sources_of_beams(src_table_file, max_sep=3):
    """
    Function to create a new table with sources match across beams
    """

    logger.info("Matching sources from different beams")

    # get the overlap matrix
    beam_matrix = get_beam_overlap_matrix()

    # reading in file
    src_data = Table.read(src_table_file, format="ascii.csv")

    # try to remove column created by this function
    # in case it was executed already on this table
    new_col_names = ["Matching_Sources"]
    # removes these if they exists
    try:
        src_data.remove_columns(new_col_names)
    except Exception as e:
        pass
    else:
        logger.debug("Removed table entries from previous analysis run")

    # number of sources
    n_src = np.size(src_data['Source_ID'])
    logger.debug("Found {} sources".format(n_src))

    # storing the matches and turning them later into a table
    match_list = []

    # get a list of beams
    beam_list = np.unique(src_data['Beam'])

    # got through each source
    for beam in beam_list:

        logger.debug("Processing sources from beam {}".format(beam))

        # get the sources for this beam
        src_data_beam = src_data[np.where(src_data['Beam'] == beam)]

        # get the beams that overlap
        overlapping_beam_list = np.where(beam_matrix[int(beam)] == 1)[0]

        # just to make sure
        if len(overlapping_beam_list) == 0:
            logger.error("Did not find any overlapping beams. Abort")
            raise RuntimeError("No overlapping beams")
        else:
            # remove the overlapping beam that is the same as the beam
            overlapping_beam_list = overlapping_beam_list[np.where(
                overlapping_beam_list != int(beam))]

        logger.debug("Beam {0} overlaps with beams {1}".format(
            beam, str(overlapping_beam_list)))

        # get the source name and the coordinates for the sources of beams that overlap
        src_ids_overlapping_beam = np.array([])
        src_ra_overlapping_beam = np.array([])
        src_dec_overlapping_beam = np.array([])
        for overlapping_beam in overlapping_beam_list:
            # avoid using the same beam
            src_data_overlapping_beam = src_data[np.where(
                src_data['Beam'] == overlapping_beam)]
            src_ids_overlapping_beam = np.concatenate(
                [src_ids_overlapping_beam, src_data_overlapping_beam['Source_ID']])
            src_ra_overlapping_beam = np.concatenate(
                [src_ra_overlapping_beam, src_data_overlapping_beam['ra']])
            src_dec_overlapping_beam = np.concatenate(
                [src_dec_overlapping_beam, src_data_overlapping_beam['dec']])
        src_coords_overlapping_beam = SkyCoord(
            src_ra_overlapping_beam, src_dec_overlapping_beam, unit=(units.hourangle, units.deg), frame='fk5')
        n_src_overlapping_beams = np.size(src_ids_overlapping_beam)

        # go through the list of sources for this beam
        for src_index in range(np.size(src_data_beam['Source_ID'])):

            src_name = src_data_beam['Source_ID'][src_index]

            logger.debug(
                "Searching for matches for {0} within {1} arcsec".format(src_name, max_sep))

            src_coord = SkyCoord(src_data_beam['ra'][src_index], src_data_beam['dec'][src_index], unit=(
                units.hourangle, units.deg), frame='fk5')

            # to store the sources that match as strings
            matched_src = ""

            # calculate the distance of this source to  through the list of overlapping beams
            src_distance = np.array([src_coord.separation(k).to("arcsec").value
                                     for k in src_coords_overlapping_beam], dtype=SkyCoord)
            # for k in range(n_src_overlapping_beams):

            #     # calculate the distance of the source
            #     src_distance[k] = src_coord.separation(
            #         src_coords_overlapping_beam[k])

            # check if there are sources within the limits
            matched_distance = np.where(
                src_distance < max_sep)[0]
            if len(matched_distance) != 0:
                matched_src = ",".join(
                    src_ids_overlapping_beam[matched_distance])
                logger.debug("Searching for matches for {0} within {1} arcsec: Found the following matches: {2}".format(
                    src_name, max_sep, matched_src))
            else:
                logger.debug(
                    "Searching for matches for {0} within {1} arcsec: Did not find any matches".format(src_name, max_sep))
                matched_src = "-"

            # add to the list of matched sources
            match_list.append(matched_src)

        logger.debug("Processing sources from beam {} ... Done".format(beam))

    # creating a Table for the matched sources and added it to the existing one
    matched_src_table = Table(
        [np.array(match_list)], names=new_col_names)
    src_data_expanded = hstack([src_data, matched_src_table])

    # save the file
    src_data_expanded.write(src_table_file, format="ascii.csv", overwrite=True)
