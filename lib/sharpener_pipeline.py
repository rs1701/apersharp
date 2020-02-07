import os
import numpy as np
import imp
import multiprocessing as mp
# import cont_src as cont_src
# import spec_ex as spec_ex
import time
# import absorption_plot as abs_pl
import glob
from PyPDF2 import PdfFileMerger
import zipfile
import logging
from setup_logger import setup_logger


def sharpener_pipeline(beam_directory_list, do_source_finding, do_spectra_extraction, do_plots, do_sdss, beam_count):
    import sharpener as sharpy
    from sharp_modules import cont_src as cont_src
    from sharp_modules import spec_ex as spec_ex
    from sharp_modules import absorption_plot as abs_pl
    from sharp_modules import sdss_match
    imp.reload(sharpy)

    logger = logging.getLogger(__name__)

    """Function to run sharpener
    """
    time_start_run = time.time()

    # get process
    proc = os.getpid()
    proc_name = mp.current_process().name

    # get beam
    beam_name = os.path.basename(beam_directory_list[beam_count])

    logfile = os.path.join(
        beam_directory_list[beam_count], "apersharp_beam_{}.log".format(beam_name))
    setup_logger('INFO', logfile=logfile)
    logger = logging.getLogger(__name__)

    # get the current working directory
    cwd = os.getcwd()

    logger.info("PID {0:d}: Changing working directory to {1}".format(
        proc, beam_directory_list[beam_count]))
    os.chdir(beam_directory_list[beam_count])

    logger.info(
        "(Pid {0:d}) #### Running sharpener for beam {1:s}".format(proc, beam_name))

    # Load parameter file
    # +++++++++++++++++++

    parameter_file = "{0:s}/beam_{1}_sharpener_settings.yml".format(
        beam_directory_list[beam_count], beam_name)

    if not os.path.exists(parameter_file):
        logger.info("(Pid {0:d}) ERROR: File {1:s} not found. Abort".format(
            proc, parameter_file))
        # sys.exit(1)

    spar = sharpy.sharpener(parameter_file)

    # continue only if all files are available
    if os.path.exists(spar.cfg_par['general']['contname']) and os.path.exists(spar.cfg_par['general']['cubename']):

        # Find continuum sources
        # ++++++++++++++++++++++
        if do_source_finding:

            logger.info("(Pid {0:d}) ## Find continuum sources".format(proc))

            # get sources in continuum image
            sources = cont_src.find_src_imsad(spar.cfg_par)

            logger.info(
                "(Pid {0:d}) ## Find continuum sources ... Done".format(proc))

        # Find sdss sources
        # ++++++++++++++++++++++
        if do_sdss:

            logger.info("(Pid {0:d}) ## Find SDSS sources".format(proc))

            # get sources in continuum image
            sdss_match.get_sdss_sources(spar.cfg_par)

            logger.info(
                "(Pid {0:d}) ## Find SDSS sources ... Done".format(proc))

        # Extract spectra
        # +++++++++++++++
        if do_spectra_extraction:

            logger.info(
                "(Pid {0:d}) ## Extract HI spectra from cube".format(proc))

            spectra = spec_ex.abs_ex(spar.cfg_par)

            logger.info(
                "##(Pid {0:d}) Extract HI spectra from cube ... Done".format(proc))

        # Plot spectra
        # ++++++++++++
        if do_plots:

            logger.info("(Pid {0:d}) ## Plotting spectra".format(proc))

            # spar.cfg_par['general']['specdir'] = os.path.join(
            #     beam_directory_list[beam_count], "sharpOut/spec/")
            # spar.cfg_par['general']['plotdir'] = os.path.join(
            #     beam_directory_list[beam_count], "sharpOut/plot/")
            # spar.cfg_par['general']['contname'] = os.path.join(
            #     beam_directory_list[beam_count], os.path.basename(spar.cfg_par['general']['contname']))
            # spar.cfg_par['general']['cubename'] = os.path.join(
            #     beam_directory_list[beam_count], os.path.basename(spar.cfg_par['general']['cubename']))

            abs_pl.create_all_abs_plots(spar.cfg_par)

            logger.info(
                "(Pid {0:d}) ## Plotting spectra ... Done".format(proc))

        # Merge plots:
        # ++++++++++++
        if spar.cfg_par['abs_plot']['plot_format'] == "pdf":

            logger.info("(Pid {0:d}) ## Merging plots".format(proc))

            # Merge the detailed plots
            # ++++++++++++++++++++++++
            plot_list = glob.glob(
                "{0:s}/*J*_detailed.pdf".format(spar.cfg_par['general']['plotdir']))

            if len(plot_list) != 0:

                plot_list.sort()

                # continuum plot only with radio sources
                cont_plot_name = "{0:s}{1:s}_continuum.pdf".format(
                    spar.cfg_par['general']['plotdir'], spar.cfg_par['general']['label'])

                # continuum plot with radio and sdss sources
                cont_sdss_plot_name = "{0:s}{1:s}_continuum_and_sdss.pdf".format(
                    spar.cfg_par['general']['plotdir'], spar.cfg_par['general']['label'])

                if os.path.exists(cont_sdss_plot_name):

                    plot_list.insert(0, cont_sdss_plot_name)

                if os.path.exists(cont_plot_name):

                    plot_list.insert(0, cont_plot_name)

                pdf_merger = PdfFileMerger()

                for files in plot_list:
                    pdf_merger.append(files)

                plot_name = "{0:s}{1:s}_all_plots_detailed.pdf".format(
                    spar.cfg_par['general']['plotdir'], spar.cfg_par['general']['label'])

                pdf_merger.write(plot_name)
            else:
                logger.info(
                    "(Pid {0:d}) No detailed plots found. Continue".format(proc))

            # Merge compact plots
            # +++++++++++++++++++
            plot_list = glob.glob(
                "{0:s}/*J*_compact.pdf".format(spar.cfg_par['general']['plotdir']))

            if len(plot_list) != 0:

                plot_list.sort()

                # continuum plot only with radio sources
                cont_plot_name = "{0:s}{1:s}_continuum.pdf".format(
                    spar.cfg_par['general']['plotdir'], spar.cfg_par['general']['label'])

                # continuum plot with radio and sdss sources
                cont_sdss_plot_name = "{0:s}{1:s}_continuum_and_sdss.pdf".format(
                    spar.cfg_par['general']['plotdir'], spar.cfg_par['general']['label'])

                if os.path.exists(cont_sdss_plot_name):

                    plot_list.insert(0, cont_sdss_plot_name)

                if os.path.exists(cont_plot_name):

                    plot_list.insert(0, cont_plot_name)

                pdf_merger = PdfFileMerger()

                for files in plot_list:
                    pdf_merger.append(files)

                plot_name = "{0:s}{1:s}_all_plots_compact.pdf".format(
                    spar.cfg_par['general']['plotdir'], spar.cfg_par['general']['label'])

                pdf_merger.write(plot_name)
            else:
                logger.info(
                    "(Pid {0:d}) No plots found. Continue".format(proc))

            logger.info("(Pid {0:d}) ## Merging plots ... Done".format(proc))

            logger.info("(Pid {0:d}) #### Finished SHRAPener for beam {1:s} ({2:.2f}s)".format(
                proc, beam_name, time.time() - time_start_run))
        else:
            logger.info("(Pid {0:d}) #### ERROR: Could not find all files. Finished SHRAPener for {1:s} ({2:.2f}s)".format(
                proc, beam_name, time.time() - time_start_run))

    logger.info("PID {0:d}: Changing working directory back to {1}".format(
        proc, cwd))
    os.chdir(cwd)
