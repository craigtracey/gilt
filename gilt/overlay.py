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
import sys

from gilt import git

LOG = logging.getLogger(__name__)


class OverlayEngine(object):
    def __init__(self, config, cleanup=True):
        self.config = config
        self.cleanup = cleanup
        self._working_dir = None

        signal.signal(signal.SIGINT, self._cleanup)
        signal.signal(signal.SIGTERM, self._cleanup)

    def _setup_environment(self):
        working_dirs = (
            self.config.base_dir,
            self.config.clone_dir, )
        for working_dir in working_dirs:
            if not os.path.exists(working_dir):
                os.makedirs(working_dir)

    def _cleanup(self, signal=None, frame=None):
        LOG.debug("Handling signal %s / %s", signal, locals())
        if not self.cleanup:
            LOG.info("Not cleaning up as specified on CLI")
            return

        LOG.info("Cleaning up %s", self._working_dir)
        if self._working_dir and os.path.exists(self._working_dir):
            shutil.rmtree(self._working_dir)

        if signal:
            sys.exit(-1)

    def overlay(self, output_dir):
        self._setup_environment()

        self._working_dir = self.config.base_dir
        clone_dir = os.path.join(self._working_dir, 'clone')

        with fasteners.InterProcessLock(self.config.lock_file):
            LOG.debug("Using lock file: %s", self.config.lock_file)

            for overlay in self.config.overlays:
                LOG.info("Cloning %s:%s", overlay.name, overlay.version)
                repo_dir = git.clone(overlay.name, overlay.git, clone_dir,
                                     overlay.version)

                LOG.info("Cloned to %s", repo_dir)
                for transform in overlay.files:
                    src = os.path.join(repo_dir, transform.src)
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

        self._cleanup()
