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

import glob
import logging
import os
import re
import shutil
import tempfile

import sh

from gilt import util

LOG = logging.getLogger(__name__)


def clone(name, repository, destination, version):
    """
    Clone the specified repository into a temporary directory and return None.

    :param name: A string containing the name of the repository being cloned.
    :param repository: A string containing the repository to clone.
    :param destination: A string containing the directory to clone the
     repository into.
    :return: None
    """
    temp_dir = tempfile.mkdtemp()
    LOG.info('Cloning %s to %s', name, temp_dir)
    clone_dir = os.path.join(temp_dir, 'clone')
    cmd = sh.git.bake('clone', repository, clone_dir)
    util.run_command(cmd)

    new_dest = None
    with util.saved_cwd():
        os.chdir(clone_dir)
        sha = _get_branch(version)
        new_dest = os.path.join(destination, "%s-%s" % (name, sha))
        shutil.copytree(clone_dir, new_dest, symlinks=True)

    shutil.rmtree(temp_dir)
    return new_dest


#def extract(repository, destination, version, debug=False):
#    """
#    Extract the specified repository/version into the given directory and
#    return None.
#
#    :param repository: A string containing the path to the repository to be
#     extracted.
#    :param destination: A string containing the directory to clone the
#     repository into.  Relative to the directory ``gilt`` is running
#     in. Must end with a '/'.
#    :param version: A string containing the branch/tag/sha to be exported.
#    :param debug: An optional bool to toggle debug output.
#    :return: None
#    """
#    with util.saved_cwd():
#        os.chdir(repository)
#        _get_branch(version, debug)
#        cmd = sh.git.bake(
#            'checkout-index', force=True, all=True, prefix=destination)
#        util.run_command(cmd)
#        msg = '  - extracting ({}) {} to {}'.format(version, repository,
#                                                    destination)
#        util.print_info(msg)
#
#
#def overlay(repository, files, version, debug=False):
#    """
#    Overlay files from the specified repository/version into the given
#    directory and return None.
#
#    :param repository: A string containing the path to the repository to be
#     extracted.
#    :param files: A list of `FileConfig` objects.
#    :param version: A string containing the branch/tag/sha to be exported.
#    :param debug: An optional bool to toggle debug output.
#    :return: None
#    """
#    with util.saved_cwd():
#        os.chdir(repository)
#        _get_branch(version, debug)
#
#        for fc in files:
#            if '*' in fc.src:
#                for filename in glob.glob(fc.src):
#                    util.copy(filename, fc.dst)
#                    msg = '  - copied ({}) {} to {}'.format(version, filename,
#                                                            fc.dst)
#                    util.print_info(msg)
#            else:
#                if os.path.isdir(fc.dst) and os.path.isdir(fc.src):
#                    shutil.rmtree(fc.dst)
#                util.copy(fc.src, fc.dst)
#                msg = '  - copied ({}) {} to {}'.format(version, fc.src,
#                                                        fc.dst)
#                util.print_info(msg)
#

def _get_branch(version, debug=False):
    """
    Handle switching to the specified version and return None.

    1. Fetch the origin.
    2. Checkout the specified version.
    3. Clean the repository before we begin.
    4. Pull the origin when a branch; _not_ a commit id.

    :param version: A string containing the branch/tag/sha to be exported.
    :param debug: An optional bool to toggle debug output.
    :return: None
    """
    cmd = sh.git.bake('fetch')
    util.run_command(cmd)
    cmd = sh.git.bake('checkout', version)
    util.run_command(cmd)
    cmd = sh.git.bake('clean', '-d', '-x', '-f')
    util.run_command(cmd)
    if not re.match(r'\b[0-9a-f]{7,40}\b', str(version)):
        cmd = sh.git.bake('pull', rebase=True, ff_only=True)
        util.run_command(cmd)
    cmd = sh.git.bake('rev-parse', 'HEAD')
    sha = util.run_command(cmd)
    return str(sha)[:6]
