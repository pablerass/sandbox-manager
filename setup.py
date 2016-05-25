#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import glob
import os
from setuptools import setup, find_packages

import sandbox_manager

# Get requirements
requirements = [req for req in open('requirements.txt')]

# Get console scripts
commands_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            'sandbox_manager', 'commands')
command_modules = glob.glob(os.path.join(commands_dir, '*.py'))
commands = list(map(lambda x: os.path.splitext(os.path.basename(x))[0],
                    command_modules))
console_scripts = list(map(lambda x: 'sandbox-{cmd} = sandbox_manager.commands.{cmd}:main'.format(cmd=x),
                           commands))

# Setup
setup(
    name='sandbox_manager',
    author='Pablo Muñoz',
    version=sandbox_manager.__version__,
    description='Generate dynamic temporary service instances in IaaS',
    long_description=open('README.md').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
    keywords='',
    platforms='any',
    packages=find_packages(exclude=['test']),
    entry_points={ 'console_scripts': console_scripts },
    zip_safe=False,
    install_requires=requirements,
)
