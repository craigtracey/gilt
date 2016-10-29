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
import os
import re
import shutil

import sh

from gilt import util


def clone(name, repo, destination, debug=False):
    """
    Clone the specified repository into a temporary directory.

    :param name: A string containing the name of the repository being cloned.
    :param repo: A string containing the repository to clone.
    :param destination: A string containing the directory to clone the
     repository into.
    :param debug: An optional bool to toggle debug output.
    :return: None
    """
    msg = '  - cloning {} to {}'.format(name, destination)
    util.print_info(msg)
    cmd = sh.git.bake('clone', repo, destination)
    util.run_command(cmd, debug=debug)


def extract(repo, destination, version, debug=False):
    """
    Extract the specified repository/version into the given directory.

    :param repo: A string containing the path to the repository to be
     extracted.
    :param destination: A string containing the directory to clone the
     repository into.  Relative to the directory ``gilt`` is running
     in. Must end with a '/'.
    :param version: A string containing the branch/tag/sha to be exported.
    :param debug: An optional bool to toggle debug output.
    :return: None
    """
    with util.saved_cwd():
        os.chdir(repo)
        _get_branch(version, debug)
        cmd = sh.git.bake(
            'checkout-index', force=True, all=True, prefix=destination)
        util.run_command(cmd, debug=debug)
        msg = '  - extracting ({}) {} to {}'.format(version, repo, destination)
        util.print_info(msg)


def overlay(repo, files, version, debug=False):
    """
    Overlay files from the specified repository/version into the given
    directory.

    :param repo: A string containing the path to the repository to be
     extracted.
    :param files: A list of `FileConfig` objects.
    :param version: A string containing the branch/tag/sha to be exported.
    :param debug: An optional bool to toggle debug output.
    :return: None
    """
    with util.saved_cwd():
        os.chdir(repo)
        _get_branch(version, debug)

        for fc in files:
            if '*' in fc.src:
                for filename in glob.glob(fc.src):
                    util.copy(filename, fc.dst)
                    msg = '  - copied ({}) {} to {}'.format(version, filename,
                                                            fc.dst)
                    util.print_info(msg)
            else:
                if os.path.isdir(fc.dst) and os.path.isdir(fc.src):
                    shutil.rmtree(fc.dst)
                util.copy(fc.src, fc.dst)
                msg = '  - copied ({}) {} to {}'.format(version, fc.src,
                                                        fc.dst)
                util.print_info(msg)


def _get_branch(version, debug=False):
    cmd = sh.git.bake('clean', '-d', '-x', '-f')
    util.run_command(cmd, debug=debug)
    cmd = sh.git.bake('fetch')
    util.run_command(cmd, debug=debug)
    cmd = sh.git.bake('checkout', version)
    util.run_command(cmd, debug=debug)
    if not re.match(r'\b[0-9a-f]{7,40}\b', version):
        cmd = sh.git.bake('pull', rebase=True, ff_only=True)
        util.run_command(cmd, debug=debug)