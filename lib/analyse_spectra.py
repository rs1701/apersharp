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
from astropy.table import Table, hstack, vstack

logger = logging.getLogger(__name__)


def get_source_spec_file(src_name, src_nr, beam, cube_dir):
    """
    Function to get the spectrum file for a given source

    Args:
    -----
    src_name (str): Name of the source (J2000 coordinates)
    src_nr (int): Number of the source in the beam
    beam (int): Number of the beam
    cube_dir (int): Directory of the cube that contains the beam and the source

    Return:
    -------
    (str): Path to the spectrum file of the source
    """

    return os.path.join(cube_dir, "{0}/sharpOut/spec/{1}_J{2}.txt".format(str(beam).zfill(2), src_nr, src_name))


def find_candidate(src_data, output_file_name_candidates,  negative_snr_threshold=-5, positive_snr_threshold=5):
    """
    Function to check the snr results for candidates
    """

    # first get all sources with negative SNR entries
    src_data_neg_snr = src_data[np.where(
        src_data['Max_Negative_SNR'] <= negative_snr_threshold)]

    # get the number of sources
    n_src_neg_snr = np.size(src_data_neg_snr['Source_ID'])

    logger.info(
        "Found {} sources exceeding negative SNR threshold".format(n_src_neg_snr))

    # second, get the sources that have no positive SNR entries
    src_data_neg_snr_no_pos_snr = src_data_neg_snr[np.where(
        src_data_neg_snr['Max_Positive_SNR'] >= positive_snr_threshold)]

    # get the number of sources
    n_src_neg_snr_no_pos_snr = np.size(
        src_data_neg_snr_no_pos_snr['Source_ID'])
    n_src_neg_snr_pos_snr = n_src_neg_snr - n_src_neg_snr_no_pos_snr

    logger.info("Disregarding {0} sources out of {1} that exceed positive SNR threshold".format(
        n_src_neg_snr_pos_snr, n_src_neg_snr))

    logger.info("Found {0} candidates for absorption after checking negative and positive SNR thresholds".format(
        n_src_neg_snr_no_pos_snr))

    snr_candidates = src_data_neg_snr_no_pos_snr['Source_ID']

    if n_src_neg_snr_no_pos_snr == 0:
        logger.info("No candidates were found".format(str(snr_candidates)))
    else:
        logger.info("Candidates are: {}".format(str(snr_candidates)))

    # writing file
    logger.info("Writing candidates to file {}".format(
        output_file_name_candidates))
    src_data_neg_snr_no_pos_snr.write(
        output_file_name_candidates, format="ascii.csv", overwrite=True)

    return snr_candidates


def get_max_negative_snr(spec_data, src_name):
    """
    Function to get the maximum negative SNR and supplementary information
    """

    # try to determine the snr
    # after checking that noise is not 0:
    noise_check = np.unique(spec_data["Noise [Jy]"])
    if np.size(noise_check) and noise_check[0] == 0:
        logger.warning(
            "Calculating SNR failed for {0}. No noise information".format(src_name))
        ratio = None
    else:
        ratio = spec_data["Flux [Jy]"] / spec_data["Noise [Jy]"]

    if ratio is None:
        max_negative_snr = 0
        max_negative_snr_ch = 0
        max_negative_snr_freq = 0
    else:
        max_negative_snr = np.nanmin(ratio)
        max_negative_snr_ch = np.where(ratio == max_negative_snr)[0][0]
        max_negative_snr_freq = spec_data['Frequency [Hz]'][max_negative_snr_ch]

    return max_negative_snr, max_negative_snr_ch, max_negative_snr_freq


def get_max_positive_snr(spec_data, src_name):
    """
    Function to get the maximum positive SNR and supplementary information
    """

    # try to determine the snr
    # after checking that noise is not 0:
    noise_check = np.unique(spec_data["Noise [Jy]"])
    if np.size(noise_check) and noise_check[0] == 0:
        logger.warning(
            "Calculating SNR failed for {0}. No noise information".format(src_name))
        ratio = None
    else:
        ratio = spec_data["Flux [Jy]"] / spec_data["Noise [Jy]"]

    if ratio is None:
        max_positive_snr = 0
        max_positive_snr_ch = 0
        max_positive_snr_freq = 0
    else:
        max_positive_snr = np.nanmax(ratio)
        max_positive_snr_ch = np.where(ratio == max_positive_snr)[0][0]
        max_positive_snr_freq = spec_data['Frequency [Hz]'][max_positive_snr_ch]

    return max_positive_snr, max_positive_snr_ch, max_positive_snr_freq


def analyse_spectra(src_cat_file, output_file_name_candidates, cube_dir, snr_threshold=-3):
    """
    Function to run quality check and find candidates for absorption
    """

    logger.info("#### Searching for candidates")

    # get the source data
    if not os.path.exists(src_cat_file):
        error = "Could not find src file {}".format(src_cat_file)
        logger.error(error)
        raise RuntimeError(error)
    else:
        src_data = Table.read(src_cat_file, format="ascii.csv")

    # number of sources
    n_src = np.size(src_data['Source_ID'])
    logger.info("Found {} sources to analyse".format(n_src))

    # get a list of beams
    beam_list = np.unique(src_data['Beam'])

    # new columns
    mean_noise = np.zeros(n_src)
    median_noise = np.zeros(n_src)
    min_flux = np.zeros(n_src)
    max_flux = np.zeros(n_src)
    mean_flux = np.zeros(n_src)
    median_flux = np.zeros(n_src)
    snr_candidates = np.zeros(n_src)
    max_negative_snr = np.zeros(n_src)
    max_negative_snr_ch = np.zeros(n_src)
    max_negative_snr_freq = np.zeros(n_src)
    max_positive_snr = np.zeros(n_src)
    max_positive_snr_ch = np.zeros(n_src)
    max_positive_snr_freq = np.zeros(n_src)

    # go through the each source files
    for src_index in range(n_src):

        src_id = src_data['Source_ID'][src_index]

        logger.info("## Processing {}".format(src_id))

        # get the spectrum file for the source
        src_spec_file = get_source_spec_file(
            src_data['J2000'][src_index], src_data['Beam_Source_ID'][src_index] - 1, src_data['Beam'][src_index], cube_dir)

        if not os.path.exists(src_spec_file):
            logger.warning("Did not find spectrum for source {0} in {1}".format(
                src_id, src_spec_file))
            continue
        else:
            pass

        # read in the file
        spec_data = Table.read(src_spec_file, format="ascii")

        # get mean noise
        mean_noise[src_index] = np.nanmean(spec_data['Noise [Jy]'])

        # get the median noise
        median_noise[src_index] = np.nanmedian(spec_data['Noise [Jy]'])

        # get max flux
        max_flux[src_index] = np.nanmax(spec_data['Flux [Jy]'])

        # get min flux
        min_flux[src_index] = np.nanmin(spec_data['Flux [Jy]'])

        # get mean flux
        mean_flux[src_index] = np.nanmean(spec_data['Flux [Jy]'])

        # get the median flux
        median_flux[src_index] = np.nanmedian(spec_data['Flux [Jy]'])

        # get maximum negative snr values
        max_negative_snr[src_index], max_negative_snr_ch[src_index], max_negative_snr_freq[src_index] = get_max_negative_snr(
            spec_data, src_id)

        # get maximum positive snr values
        max_positive_snr[src_index], max_positive_snr_ch[src_index], max_positive_snr_freq[src_index] = get_max_positive_snr(
            spec_data, src_id)

        # if snr_candidate[src_index] == 1:
        #     logger.debug("Found candidate for absorption (SNR = {0})".format(
        #         max_negative_snr[src_index]))
        # else:
        #     logger.debug("Not a candidate for absorption")

        logger.info("## Processing {} ... Done".format(src_id))

    # for storing new table later
    metrics_table = Table([mean_noise, median_noise, min_flux, max_flux, mean_flux, median_flux, snr_candidates,
                           max_negative_snr, max_negative_snr_ch, max_negative_snr_freq, max_positive_snr, max_positive_snr_ch, max_positive_snr_freq], names=("Mean_Noise", "Median_Noise", "Min_Flux", "Max_Flux", "Mean_Flux", "Median_Flux", "Candidate_SNR", "Max_Negative_SNR", "Max_Negative_SNR_Channel", "Max_Negative_SNR_Frequency", "Max_Positive_SNR", "Max_Positive_SNR_Channel", "Max_Positive_SNR_Frequency"))

    # combine old and new table
    new_data_table = hstack([src_data, metrics_table])

    # get a list of candidates
    src_snr_candidates = find_candidate(
        new_data_table, output_file_name_candidates, max_negative_snr, max_positive_snr)

    # change entries for the candidate
    logger.info("Marking candidates in source catalogue")
    for src in src_snr_candidates:
        new_data_table['Candidate_SNR'][np.where(
            new_data_table['Source_ID']) == src] = 1

    # write out table
    logger.info(
        "Updating source catalogue {}".format(src_cat_file))
    new_data_table.write(src_cat_file, format="ascii.csv", overwrite=True)

    logger.info("#### Searching for candidates ... Done")
