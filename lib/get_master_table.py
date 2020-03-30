import os
import numpy as np
import glob
import logging
import datetime
import shutil
from astropy.table import Table, vstack, hstack, Column
import astropy.units as units
from astropy.coordinates import SkyCoord

logger = logging.getLogger(__name__)


def get_all_sources_of_cube(output_file_name, cube_dir, taskid=None, cube_nr=None, beam_list=None, src_file="radio_sdss_src_match.csv", alt_src_file="mir_src_sharp.csv", overwrite_master_table=False, create_master_table_backup=True, allow_multiple_source_entries=False):
    """
    Function to collect the information from all sources in one file

    Use the radio-SDSS source file or the source file without SDSS,
    but then add SDSS columns.
    """

    # if the cube number was not given, try to get from the name
    if cube_nr is None:
        cube_nr = os.path.basename(cube_dir).split("_")[-1]

    # if taskid was not given, try to get from the directory
    if taskid is None:
        taskid = os.path.dirname(cube_dir).split("/")[-1]

    logger.info("Collecting source information from beams")

    logger.debug("Processing cube {0} of taskid {1}".format(cube_nr, taskid))

    # get a list of beams
    if beam_list is None:
        beam_list = glob.glob(os.path.join(cube_dir, "??"))
        if len(beam_list) == 0:
            error = "Did not find any beams in {}. Abort".format(cube_dir)
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
                "Could not find source file {} from radio-sdss cross-match by SHARPener.".format(csv_file_name))
            # alternative source file
            alt_csv_file_name = os.path.join(
                cube_dir, "{0}/sharpOut/abs/{1}".format(beam, alt_src_file))
            logger.warning("Checking alternative source file {} and adding emtpy SDSS columns".format(
                alt_csv_file_name))
            if not os.path.exists(alt_csv_file_name):
                logger.error(
                    "Did not find alternative source file. No source information available for beam {}".format(beam))
                continue
            # read in file
            src_data = Table.read(alt_csv_file_name, format="ascii.csv")
            # get number of sources
            n_src = np.size(src_data['ID'])
            # add sdss columns
            src_data['sdss_id'] = Column(np.zeros(n_src), dtype=int)
            src_data['sdss_ra'] = Column(np.zeros(n_src))
            src_data['sdss_dec'] = Column(np.zeros(n_src))
            src_data['sdss_radio_sep'] = Column(np.zeros(n_src))
            src_data['sdss_redshift'] = Column(np.zeros(n_src))
        else:
            # read the data
            src_data = Table.read(csv_file_name, format="ascii.csv")
            # number of sources
            n_src = np.size(src_data['ID'])

        logger.debug("Found {} sources".format(n_src))

        # rename the ID column
        src_data.rename_column('ID', 'Beam_Source_ID')

        # fix the column type
        src_data['FFLAG'] = np.array([str(flag) for flag in src_data['FFLAG']])

        # create a new columns for ID, taskid, beam and cube
        src_id = np.array(["{0}_C{1}_B{2}_{3}_J{4}".format(
            taskid, cube_nr, beam.zfill(2), src_data['Beam_Source_ID'][k], src_data['J2000'][k]) for k in range(n_src)])
        src_beam = np.array([int(beam) for i in range(n_src)])
        src_cube = np.array([int(cube_nr) for i in range(n_src)])

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

    # check if master table already exists
    if os.path.exists(output_file_name):
        logger.info("Master table already exists.")

        # create a copy in the backup directory
        if create_master_table_backup:
            table_backup_dir = os.path.join(
                cube_dir, "master_table_backup")
            if not os.path.exists(table_backup_dir):
                os.mkdir(table_backup_dir)
            table_backup_name = os.path.join(table_backup_dir, os.path.basename(output_file_name).replace(
                ".csv", "_{}.csv".format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))))
            logger.info("Creating a copy of current master table in {}".format(
                table_backup_name))
            shutil.copy2(output_file_name, table_backup_name)

        # overwrite existing master table or add new data
        if overwrite_master_table:
            logger.warning("Existing master table will be overwritten")
        else:
            logger.info("Adding new sources to existing master table")
            # read current master table
            master_table = Table.read(output_file_name, format="ascii.csv")
            # add new sources
            # add without checking if they exists
            if allow_multiple_source_entries:
                logger.warning(
                    "Adding new sources without checking if they already exists. Source ID may not be unique any more.")
                full_list = vstack([master_table, full_list])
            # check for existing entry and remove if found, then add
            else:
                # get list of unique beams from new table
                new_beam_list = np.unique(full_list["Beam"])

                # go through the list of beams
                for new_beam in new_beam_list:
                    new_beam_in_master_indices = np.where(
                        (master_table["Cube"] == int(cube_nr)) & (master_table["Beam"] == new_beam))[0]
                    # remove all entries of this beam from master table
                    if np.size(new_beam_in_master_indices) != 0:
                        logger.warning(
                            "Found data for beam {}. Will be replaced".format(new_beam))
                        master_table.remove_rows(new_beam_in_master_indices)
                    else:
                        continue

                # combine master table with new data
                full_list = vstack([master_table, full_list])

            # sort by source id to easily spot multiple entries
            full_list.sort("Source_ID")

    # save the file if there is something to save
    if np.size(full_list) != 0:
        full_list.write(output_file_name, format="ascii.csv", overwrite=True)
        logger.info("Collecting source information from beams ... Done")
    else:
        error = "Table with all sources is emtpy. Abort"
        logger.error(error)
        logger.error("Collecting source information from beams ... Failed")
        raise RuntimeError(error)
