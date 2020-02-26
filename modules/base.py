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

    taskid = None
    user = None
    sharpener_basedir = None
    output_form = None
    data_basedir = None
    data_source = None
    configfilename = None
    cube = None
    cube_dir = None
    beam_list = None
    # continuum_image_list = None
    cont_src_resource = None
    steps = None
    n_cores = None
    do_sdss = False
    NBEAMS = 40
    logfile = None

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

        return os.path.join(self.get_cube_dir(), "{0}_Cube{1}_all_sources.csv".format(self.taskid, self.cube))

    def get_src_csv_file_name_matched(self):
        """
        Function to return the path of CSV file with source information from all beams 
        and sources matched across beams
        """

        return self.get_src_csv_file_name().replace(".csv", "_matched.csv")

    def get_src_csv_file_name_candidates(self):
        """
        Function to return the path of CSV file with source information from all beams 
        and source spectra analysed for candidates of absorption
        """

        return self.get_src_csv_file_name().replace(".csv", "_candidates.csv")
