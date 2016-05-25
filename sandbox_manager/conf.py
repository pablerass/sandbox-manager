"""Manage sandbox_manager module configuration."""
import configparser
import glob
import os

import sandbox_manager


class _Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args,
                                                                  **kwargs)
        return cls._instances[cls]


class SandboxConfig(metaclass=_Singleton):
    """Sandbox manager configuration class."""

    def __init__(self, conf_dir=sandbox_manager.CONF_DIR):
        """Create sandbox config with the content of determined files."""
        self.__conf_dir = conf_dir
        self.__conf = configparser.ConfigParser()
        self.__conf.read(self.__get_config_files())

    def __get_config_files(self):
        return glob.glob(os.path.join(self.__conf_dir, '*.conf'))

    def get(self, section, option):
        """Get string option."""
        return self.__conf.get(section, option)

    def get_boolean(self, section, option):
        """Get boolean option."""
        return self.__conf.getboolean(section, option)

    def get_float(self, section, option):
        """Get float option."""
        return self.__conf.getfloat(section, option)

    def get_int(self, section, option):
        """Get integer option."""
        return self.__conf.getint(section, option)

    def has_option(self, section, option):
        """Return if the specified confi section has an determined option."""
        return self.__conf.has_option(section, option)

    def has_section(self, section):
        """Return if the configuration has a specified section."""
        return self.__conf.has_section(section)

    def options(self, section):
        """Return all section options."""
        return self.__conf.items(section)

    def sections(self):
        """Return all sections."""
        return self.__conf.sections
