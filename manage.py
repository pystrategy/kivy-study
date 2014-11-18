#!/usr/bin/env python
# -*- coding:utf8 -*-
import sys
sys.path.append('Tools')

import os

from pypm import ProjectManager

PROJECT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))

pm = ProjectManager()

@pm.command()
def update_pypm():
    """
    pypm 업데이트
    """
    pm.run_system_command('rm', ['-rf', 'Tools/pypm*'])
    pm.run_system_command(
        'pip', [
            'install',
            'git+https://github.com/moonrabbit/pypm',
            '--target', os.path.join(PROJECT_DIR_PATH, 'Tools')])

if __name__ == '__main__':
    pm.run_command(sys.argv[1:])
