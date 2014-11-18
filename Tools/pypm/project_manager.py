# -*- coding:utf8 -*-
import os
import re
import code
import shutil
import argparse
import functools

from fnmatch import fnmatch

from codecs import BOM_UTF8

class DirectoryContext(object):
    def __init__(self, dir_path):
        self.target_dir_path = dir_path
        self.prev_dir_path = None
 
    def __enter__(self):
        print 'push_directory:', self.target_dir_path
        self.prev_dir_path = os.getcwd()
        os.chdir(self.target_dir_path)
        return self
 
    def __exit__(self, type, value, tb):
        print 'pop_directory:', self.prev_dir_path
        os.chdir(self.prev_dir_path)

class FilterPattern(object):
    RECURSIVE_DIR_PATTERN = '...'

    def __init__(self, patterns):
        self.patterns = [
                re.compile(pattern.replace('...', '[\w\/]+') + '$') 
                if '...' in pattern else pattern 
                for pattern in patterns]

    def __call__(self, text):
        for pattern in self.patterns:
            if isinstance(pattern, str):
                return fnmatch(text, pattern)
            else:
                return pattern.match(text)

class ProjectManager(object):
    class ExitCode(object):
        EMPTY_ARGUMENTS = -1
        WRONG_PROCESS = -2

    class Error(Exception):
        pass

    class ArgumentError(Error):
        pass

    def __init__(self):
        self.main_parser = argparse.ArgumentParser()
        self.sub_parsers = self.main_parser.add_subparsers()

    def command(self, **option_table):
        def handler(func):
            option_names = func.func_code\
                               .co_varnames[:func.func_code.co_argcount]

            @functools.wraps(func)
            def wrapper(ns):
                kwargs = dict()
                for option_name in option_names:
                    option_info_dict = option_table[option_name]
                    option_nargs = option_info_dict.get('nargs', None)
                    if option_nargs == 1:
                        kwargs[option_name] = getattr(ns, option_name)[0]
                    else:
                        kwargs[option_name] = getattr(ns, option_name)

                return func(**kwargs)

            def create_sub_parser(func_name, func_doc):
                new_sub_parser = self.sub_parsers.add_parser(
                    func_name, help=func_doc)

                for option_name in option_names:
                    option_info_dict = option_table[option_name]
                    option_flag = option_info_dict.get('flag', None)
                    if option_flag:
                        del option_info_dict['flag']
                        new_sub_parser.add_argument(
                            option_flag, '--' + option_name, **option_info_dict)
                    else:
                        new_sub_parser.add_argument(
                            option_name, **option_info_dict)

                return new_sub_parser

            sub_parser = create_sub_parser(func.func_name, func.func_doc)
            sub_parser.set_defaults(func=wrapper)
        return handler

    def add_common_argument(self, *args, **kwargs):
        self.main_parser.add_argument(*args, **kwargs) 
    
    def run_command(self, cmd_args):
        if cmd_args is None or len(cmd_args) == 0:
            self.main_parser.print_help()
            return self.ExitCode.EMPTY_ARGUMENTS

        ns = self.main_parser.parse_args(cmd_args)
        try:
            return ns.func(ns)
        except self.Error as e:
            print ''
            print str(e)
            return self.ExitCode.WRONG_PROCESS

    @staticmethod
    def run_system_command(exec_path, exec_args, is_verbose=True):
        cmd_line = '%s %s' % (exec_path, ' '.join(exec_args))
        if is_verbose:
            print '$ %s' % cmd_line
        return os.system(cmd_line)

    @staticmethod
    def run_python_shell(title, local_dict):
        code.interact(title, local=local_dict)

    @staticmethod
    def push_directory(dir_path):
        return DirectoryContext(os.path.realpath(dir_path))

    @staticmethod
    def access_directory(dir_path):
        return os.access(dir_path, os.R_OK)

    @staticmethod
    def access_file(file_path):
        return os.access(file_path, os.R_OK)

    @staticmethod
    def find_dir_path_iter(
            base_dir_path='.',
            path_patterns=None,
            filter_dir_name=None,
            is_all_dirs=False,
            is_real_path=True):

        filter_path_pattern = FilterPattern(path_patterns) if path_patterns else None

        for parent_dir_path, dir_names, file_names in os.walk(base_dir_path):
            if filter_path_pattern is None or filter_path_pattern(parent_dir_path[len(base_dir_path) + 1:]):
                yield os.path.realpath(parent_dir_path) if is_real_path else parent_dir_path

            if not is_all_dirs:
                for dir_name in list(dir_names):
                    if dir_name[0] == '.':
                        dir_names.remove(dir_name)

            if filter_dir_name:
                for dir_name in list(dir_names):
                    if not filter_dir_name(dir_name):
                        dir_names.remove(dir_name)

    @classmethod
    def smart_find_file_path_iter(cls, hint, base_dir_path='.'):
        real_file_path = os.path.realpath(os.path.expandvars(hint))
        if os.access(real_file_path, os.R_OK):
            yield real_file_path

        file_name_pattern = hint + '*'
        for found_file_path in cls.find_file_path_iter(base_dir_path, filter_file_name=FilterPattern([file_name_pattern])):
            yield found_file_path

    @classmethod
    def smart_find_file_path(cls, hint, base_dir_path='.'):
        for found_file_path in cls.smart_find_file_path_iter(hint, base_dir_path):
            return found_file_path
        else:           
            raise cls.Error('NOT_FOUND_FILE_IN_DIR_PATH:' + base_dir_path + ' HINT:' + hint)

    @staticmethod
    def find_file_path_iter(
            base_dir_path='.',
            path_patterns=None,
            filter_dir_name=None,
            filter_file_name=None,
            filter_file_ext=None,
            filter_file_path=None,
            is_all_files=False,
            is_real_path=True):

        filter_path_pattern = FilterPattern(path_patterns) if path_patterns else None

        for parent_dir_path, dir_names, file_names in os.walk(base_dir_path):
            if not is_all_files:
                for dir_name in list(dir_names):
                    if dir_name[0] == '.':
                        dir_names.remove(dir_name)

            if filter_dir_name:
                for dir_name in list(dir_names):
                    if not filter_dir_name(dir_name):
                        dir_names.remove(dir_name)
            
            for file_name in file_names:
                if not is_all_files:
                    if file_name[0] == '.':
                        continue

                if filter_file_name is None or filter_file_name(file_name):
                    file_ext = os.path.splitext(file_name)[1].lower()
                    if filter_file_ext is None or filter_file_ext(file_ext):
                        file_path = os.path.join(parent_dir_path, file_name)
                        if filter_file_path is None or filter_file_path(file_path):
                            if filter_path_pattern is None or filter_path_pattern(file_path[len(base_dir_path) + 1:]):
                                yield os.path.realpath(file_path) if is_real_path else file_path

    @staticmethod
    def add_utf8_bom(file_path):
        file_bom = open(file_path, 'rb').read(len(BOM_UTF8))
        if file_bom != BOM_UTF8:
            file_data = open(file_path, 'rb').read()
            open(file_path, 'wb').write(BOM_UTF8 + file_data)

    @staticmethod
    def remove_utf8_bom(file_path):
        file_bom = open(file_path, 'rb').read(len(BOM_UTF8))
        if file_bom == BOM_UTF8:
            file_data = open(file_path, 'rb').read()
            open(file_path, 'wb').write(file_data[len(BOM_UTF8):])

    @staticmethod
    def remove_symbolic_link(link_path, is_testing=True):
        real_link_path = os.path.abspath(link_path)
        if is_testing:
            print 'test_remove_symbolic_link:', real_link_path
        else:
            print 'remove_symbolic_link:', real_link_path
            os.unlink(real_link_path)

    @staticmethod
    def remove_file(file_path, is_testing=True):
        real_file_path = os.path.realpath(file_path)
        if is_testing:
            print 'test_remove_file:', real_file_path
        else:
            print 'remove_file:', real_file_path
            os.remove(real_file_path)

    @staticmethod
    def remove_tree(dir_path, is_testing=True):
        real_dir_path = os.path.realpath(dir_path)
        if is_testing:
            print 'test_remove_tree:', real_dir_path
        else:
            print 'remove_tree:', real_dir_path
            shutil.rmtree(real_dir_path)

    @classmethod
    def remove_trees_by_patterns(cls, path_patterns, base_dir_path='.', is_testing=True, is_verbose=True):
        real_dir_paths = [os.path.realpath(dir_path)
                for dir_path in cls.find_dir_path_iter(
                    base_dir_path, path_patterns, is_all_dirs=True)]
        
        for real_dir_path in reversed(real_dir_paths):
            if is_testing:
                print 'test_remove_tree:', real_dir_path, 'path_patterns:', path_patterns
            else:
                if is_verbose:
                    print 'remove_tree:', real_dir_path, 'path_patterns:', path_patterns
                shutil.rmtree(real_dir_path)

    @classmethod
    def remove_files_by_patterns(cls, path_patterns, base_dir_path='.', is_testing=True, is_verbose=True):
        real_file_paths = [os.path.realpath(file_path)
                for file_path in cls.find_file_path_iter(
                    base_dir_path, path_patterns, is_all_files=True)]
        
        for real_file_path in real_file_paths:
            if is_testing:
                print 'test_remove_file:', real_file_path, 'path_patterns:', path_patterns
            else:
                if is_verbose:
                    print 'remove_file:', real_file_path, 'path_patterns:', path_patterns
                os.remove(real_file_path)

    @classmethod
    def make_symbolic_link(cls, source_path, target_path):
        real_source_path = os.path.realpath(source_path)
        real_target_path = os.path.realpath(target_path)
        print 'make_symbolic_link_source:', real_source_path, 'target:', real_target_path
        os.symlink(real_source_path, real_target_path)

    @staticmethod
    def make_directory(dir_path):
        real_dir_path = os.path.realpath(dir_path)
        if os.access(real_dir_path, os.R_OK):
            print 'already_made_directory:', real_dir_path
            return False

        print 'make_directory:', real_dir_path
        os.makedirs(real_dir_path)
        return True

    @staticmethod
    def touch_file(file_path):
        real_file_path = os.path.realpath(file_path)
        if os.access(real_file_path, os.R_OK):
            print 'touch_file:', real_file_path
            file_data = open(file_path, "rb").read()
        else:
            print 'make_touch_file:', real_file_path
            file_data = ""

        open(real_file_path, "wb").write(file_data)


if __name__ == '__main__':
    FILE_PATH = os.path.realpath(__file__)
    MODULE_PATH = os.path.dirname(FILE_PATH)
    PROJECT_PATH = os.path.dirname(MODULE_PATH)

    pm = ProjectManager()

    @pm.command(messages=dict(type=str, nargs='+'))
    def echo(messages):
        print messages

    pm.run_command(['echo', 'haha'])
