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

import os
import re
import uuid

import yaml

from marshmallow import Schema, fields, post_load


class ParseError(Exception):
    """ Error raised when a config can't be loaded properly. """
    pass


DEFAULT_BASE_DIR = os.path.expanduser('~/.gilt')
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
    dst = fields.String()
    files = fields.List(fields.Nested(FileTransformConfigSchema()))


class ConfigSchema(LoadedSchema):

    overlays = fields.List(fields.Nested(OverlayConfigSchema()))
    base_dir = fields.String()
    lock_file = fields.String()
    clone_dir = fields.String()


class FileTransformConfig(object):
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst


class OverlayConfig(object):
    def __init__(self,
                 git,
                 name=None,
                 version=DEFAULT_OVERLAY_VERSION,
                 dst=None,
                 files=[]):
        self.git = git
        self._name = name
        self.version = version
        self.dst = dst
        self._files = files

    @property
    def name(self):
        if not self._name:
            self._name = re.sub('.git$', '', os.path.basename(self.git))
        return self._name

    @property
    def files(self):
        files = []
        if self.dst:
            files.append(FileTransformConfig('*', self.dst))
        if self._files:
            files += self._files
        return files


class Config(object):
    def __init__(self,
                 overlays=[],
                 base_dir=None,
                 lock_file=None,
                 clone_dir=None):
        self.overlays = overlays
        self._base_dir = base_dir
        self._lock_file = lock_file
        self._clone_dir = clone_dir

    @property
    def base_dir(self):
        if not self._base_dir:
            self._base_dir = os.path.join(DEFAULT_BASE_DIR, str(uuid.uuid4()))
        return self._base_dir

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
