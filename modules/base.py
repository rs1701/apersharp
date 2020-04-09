import os
from abc import abstractproperty, ABCMeta


class BaseModule:

    """
    Simple base class for Apersched classes
    """

    __metaclass__ = ABCMeta

    @abstractproperty
    def module_name(self):
        pass

    user = None
    output_form = None
    data_basedir = None
    data_source = None
    sharpener_configfilename = None
    cube_list = None
    beam_list = None
    steps_list = None
    n_cores = None

    taskid = None
    sharpener_basedir = None
    cube_dir = None
    # continuum_image_list = None

    # setting that should not be changed
    cont_src_resource = 'image'
    logfile = None
    NBEAMS = 40

    # Name of the csv file with all sources
    all_src_csv_file_name = None
    # Name of the csv file with all sources after matching across beams
    all_src_csv_file_name_matched = None
    # Name of the csv file with all sources after checking for candidates
    all_src_csv_file_name_candidates = None

    def get_cube_dir(self):
        """
        Function to return the directory of the cube for a given beam
        """

        return os.path.join(self.sharpener_basedir, "cube_{0}".format(self.cube))

    def get_cube_beam_dir(self, beam):
        """
        Function to return the directory of the cube for a given beam
        """

        return os.path.join(self.sharpener_basedir, "cube_{0}/{1}".format(self.cube, beam.zfill(2)))

    def get_cube_path(self, beam):
        """
        Function to return the path of the line cube in the sharpener directory for a given beam
        """

        return os.path.join(self.sharpener_basedir, "cube_{0}/{1}/HI_image_cube{0}.fits".format(self.cube, beam.zfill(2)))

    def get_cont_path(self, beam):
        """
        Function to return the path of the continuum image in the sharpener directory for a given beam
        """

        return os.path.join(self.sharpener_basedir, "cube_{0}/{1}/image_mf.fits".format(self.cube, beam.zfill(2)))

    def get_src_csv_file_name(self):
        """
        Function to return the path of CSV file with source information from all beams
        """

        if self.all_src_csv_file_name is None:
            return os.path.join(self.get_cube_dir(), "{0}_cube_{1}_master_table.csv".format(self.taskid, self.cube))
        else:
            return self.all_src_csv_file_name

    def get_src_csv_file_name_matched(self):
        """
        Function to return the path of CSV file with source information from all beams 
        and sources matched across beams
        """

        if self.all_src_csv_file_name_matched is None:
            return self.get_src_csv_file_name().replace(".csv", "_matched.csv")
        else:
            return self.all_src_csv_file_name_matched

    def get_src_csv_file_name_candidates(self):
        """
        Function to return the path of CSV file with source information from all beams 
        and source spectra analysed for candidates of absorption
        """

        if self.all_src_csv_file_name_candidates is None:
            return self.get_src_csv_file_name().replace("_all_sources.csv", "_snr_candidates.csv")
        else:
            return self.all_src_csv_file_name_candidates
