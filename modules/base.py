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
    NBEAMS = 40
