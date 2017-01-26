# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2016 Cisco Systems, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import fasteners
import glob
import logging
import os
import signal
import shutil
import uuid

import pbr.version

from gilt import git
from gilt import util

LOG = logging.getLogger(__name__)

try:
    version_info = pbr.version.VersionInfo('gilt')
    __version__ = pbr.version_info.release_string()
except AttributeError:
    __version__ = None

base_clone_dir = None


def _setup_environment(config):
    working_dirs = (
        config.base_dir,
        config.clone_dir, )
    for working_dir in working_dirs:
        if not os.path.exists(working_dir):
            os.makedirs(working_dir)


def _cleanup(signal=None, frame=None):

    if base_clone_dir and os.path.exists(base_clone_dir):
        shutil.rmtree(base_clone_dir)


signal.signal(signal.SIGINT, _cleanup)
signal.signal(signal.SIGTERM, _cleanup)


def overlay(config, output_dir):

    _setup_environment(config)

    global base_clone_dir
    id = str(uuid.uuid4())
    base_clone_dir = os.path.join(config.clone_dir, id)

    with fasteners.InterProcessLock(config.lock_file):
        id = str(uuid.uuid4())

        for overlay in config.overlays:
            util.print_info('{}:'.format(overlay.name))

            clone_dir = os.path.join(config.clone_dir, id,
                                     "%s-%s" % (overlay.name, overlay.version))
            git.clone(overlay.name, overlay.git, clone_dir)
            git.extract(overlay.git, overlay.version)


            for transform in overlay.files:
                src = os.path.join(clone_dir, transform.src)
                dest = os.path.join(output_dir, transform.dst)

                if not os.path.exists(dest) and dest.endswith(os.path.sep):
                    os.makedirs(dest)

                for path in glob.glob(src):
                    LOG.info("Copying %s to %s", path, dest)
                    if os.path.isfile(path):
                        destdir = os.path.dirname(dest)
                        if not os.path.exists(destdir):
                            os.makedirs(destdir)
                        shutil.copy(path, dest)
                    elif os.path.isdir(path):
                        dest = os.path.join(dest, os.path.basename(path))
                        shutil.copytree(path, dest, symlinks=True)

    _cleanup()
