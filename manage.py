#!/usr/bin/env python
# -*- coding:utf8 -*-
import sys
sys.path.append('Tools')

import os
import random

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

@pm.command(names=dict(type=str, nargs='*', help="이름 리스트"))
def lot(names):
    random.shuffle(names)
    for index, name in enumerate(names):
        print '%d:%s' % (index + 1, name)
        raw_input()


@pm.command()
def div():
    pages = [int(line.split()[-1]) for line in open('pages.txt').read().splitlines()]
    first_chapter_page = pages[0]
    next_chapter_page = pages[-1] 
    page_count = next_chapter_page - first_chapter_page
    names = open('members.txt').read().splitlines()
    random.shuffle(names)

    page_step = page_count / len(names)
    error_count = page_count - page_step * len(names)
    error_steps = [1] * error_count + [0] * (len(names) - error_count)
    random.shuffle(error_steps)

    cur_page = first_chapter_page
    for index, name in enumerate(names):
        error_step = error_steps[index]
        cur_step = page_step + error_step 
        print '%d:%s:%d~%d' % (index + 1, name, cur_page, cur_page + cur_step - 1)
        cur_page += cur_step
        raw_input()

if __name__ == '__main__':
    pm.run_command(sys.argv[1:])
