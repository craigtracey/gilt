# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2016 Cisco Systems, Inc.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

import collections
import errno
import os
import re

import giturlparse
import yaml

from marshmallow import Schema, fields, post_load


class ParseError(Exception):
    """ Error raised when a config can't be loaded properly. """
    pass


DEFAULT_BASE_DIR = '~/.gilt'
DEFAULT_OVERLAY_VERSION = 'master'


class LoadedSchema(Schema):

    @post_load
    def create_instance(self, data):
        cls_name = re.sub('Schema$', '', self.__class__.__name__)
        cls = globals()[cls_name]
        return cls(**data)


class FileTransformConfigSchema(LoadedSchema):

    src = fields.String(required=True)
    dst = fields.String(required=True)


class OverlayConfigSchema(LoadedSchema):

    git = fields.Url(required=True)
    name = fields.String()
    version = fields.String(default=DEFAULT_OVERLAY_VERSION)
    file_transforms = fields.List(fields.Nested(FileTransformConfigSchema()))


class ConfigSchema(LoadedSchema):

    overlays = fields.List(fields.Nested(OverlayConfigSchema()))
    base_dir = fields.String(default=DEFAULT_BASE_DIR)
    lock_file = fields.String()
    clone_dir = fields.String()


class FileTransformConfig(object):

    def __init__(self, src, dst):
        self.src = src
        self.dst = dst


class OverlayConfig(object):

    def __init__(self, git, name=None, version=DEFAULT_OVERLAY_VERSION,
                 file_transforms=[]):
        self.git = git
        self._name = name
        self.version = version
        self.file_transforms = file_transforms

    @property
    def name(self):
        if not self._name:
            self._name = re.sub('.git$', '', os.path.basename(self.git))
        return self._name


class Config(object):

    def __init__(self, overlays=[], base_dir=DEFAULT_BASE_DIR, 
                 lock_file=None, clone_dir=None):
        self.overlays = overlays
        self.base_dir = base_dir
        self._lock_file = lock_file
        self._clone_dir = clone_dir
   
    @property
    def lock_file(self):
        if not self._lock_file:
            self._lock_file = os.path.join(self.base_dir, 'lock')
        return self._lock_file

    @property
    def clone_dir(self):
        if not self._clone_dir:
            self._clone_dir = os.path.join(self.base_dir, 'clone')
        return self._clone_dir

    @staticmethod
    def from_file(filename):
        """
        Parse the provided YAML file and return a dict.clear
        :parse filename: A string containing the path to YAML file.
        :return: Config instance
        """

        data = None
        with open(filename, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
                result = ConfigSchema().load({'overlays': data})
                if result.errors:
                    errs = ", ".join(result.errors)
                    msg = 'Error parsing gilt config: {0}'.format(errs)
                    raise ParseError(msg)
                return result.data
            except yaml.parser.ParserError as e:
                msg = 'Error parsing gilt config: {0}'.format(e)
                raise ParseError(msg)
#
#
#def config(filename):
#    """
#    Construct `Config` object and return a list.
#
#    :parse filename: A string containing the path to YAML file.
#    :return: list
#    """
#    Config = collections.namedtuple(
#        'Config',
#        ['git', 'lock_file', 'version', 'name', 'src', 'dst', 'files'])
#
#    return [Config(**d) for d in _get_config_generator(filename)]
#
#
#def _get_files_config(src_dir, files_list):
#    """
#    Construct `FileConfig` object and return a list.
#
#    :param src_dir: A string containing the source directory.
#    :param files_list: A list of dicts containing the src/dst mapping of files
#     to overlay.
#    :return: list
#    """
#    FilesConfig = collections.namedtuple('FilesConfig', ['src', 'dst'])
#
#    return [
#        FilesConfig(**d) for d in _get_files_generator(src_dir, files_list)
#    ]
#
#
#def _get_config_generator(filename):
#    """
#    A generator which populates and return a dict.
#
#    :parse filename: A string containing the path to YAML file.
#    :return: dict
#    """
#    for d in _get_config(filename):
#        repo = d['git']
#        parsedrepo = giturlparse.parse(repo)
#        name = '{}.{}'.format(parsedrepo.owner, parsedrepo.repo)
#        src_dir = os.path.join(_get_clone_dir(), name)
#        files = d.get('files')
#        dst_dir = None
#        if not files:
#            dst_dir = _get_dst_dir(d['dst'])
#        yield {
#            'git': repo,
#            'lock_file': _get_lock_file(name),
#            'version': d['version'],
#            'name': name,
#            'src': src_dir,
#            'dst': dst_dir,
#            'files': _get_files_config(src_dir, files)
#        }
#
#
#def _get_files_generator(src_dir, files_list):
#    """
#    A generator which populates and return a dict.
#
#    :param src_dir: A string containing the source directory.
#    :param files_list: A list of dicts containing the src/dst mapping of files
#     to overlay.
#    :return: dict
#    """
#    if files_list:
#        for d in files_list:
#            yield {
#                'src': os.path.join(src_dir, d['src']),
#                'dst': _get_dst_dir(d['dst'])
#            }
#
#
#def _get_config(filename):
#    """
#    Parse the provided YAML file and return a dict.
#
#    :parse filename: A string containing the path to YAML file.
#    :return: dict
#    """
#    with open(filename, 'r') as stream:
#        try:
#            return yaml.safe_load(stream)
#        except yaml.parser.ParserError as e:
#            msg = 'Error parsing gilt config: {0}'.format(e)
#            raise ParseError(msg)
#
#
#def _get_dst_dir(dst_dir):
#    """
#    Prefix the provided string with working directory and return a
#    str.
#
#    :param dst_dir: A string to be prefixed with the working dir.
#    :return: str
#    """
#    wd = os.getcwd()
#    _makedirs(dst_dir)
#
#    return os.path.join(wd, dst_dir)
#
#
#def _get_lock_file(name):
#    """ Return the lock file for the given name. """
#    return os.path.join(
#        _get_lock_dir(),
#        name, )
#
#
#def _get_base_dir():
#    """ Return gilt's base working directory. """
#    return os.path.expanduser(BASE_WORKING_DIR)
#
#
#def _get_lock_dir():
#    """
#    Construct gilt's lock directory and return a str.
#
#    :return: str
#    """
#    return os.path.join(
#        _get_base_dir(),
#        'lock', )
#
#
#def _get_clone_dir():
#    """
#    Construct gilt's clone directory and return a str.
#
#    :return: str
#    """
#    return os.path.join(
#        _get_base_dir(),
#        'clone', )
#
#
#def _makedirs(path):
#    """
#    Create a base directory of the provided path and return None.
#
#    :param path: A string containing a path to be deconstructed and basedir
#     created.
#    :return: None
#    """
#    dirname, _ = os.path.split(path)
#    try:
#        os.makedirs(dirname)
#    except OSError as exc:
#        if exc.errno == errno.EEXIST:
#            pass
#        else:
#            raise
