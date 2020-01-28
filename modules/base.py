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
    continuum_image_list = None
    steps = None
    n_cores = None
    do_sdss = False
    NBEAMS = 40

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
