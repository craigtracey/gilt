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
import logging
import sys

import click

import gilt
from gilt.config import Config
from gilt.overlay import OverlayEngine

LOG = logging.getLogger(__name__)


def _setup_logger(level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(level)
    log_handler = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter(
        fmt='%(asctime)s %(name)s '
        '%(levelname)s: %(message)s',
        datefmt='%F %H:%M:%S')
    log_handler.setFormatter(fmt)
    logger.addHandler(log_handler)


class NotFoundError(Exception):
    """ Error raised when a config can not be found. """
    pass


def main():
    """ gilt - A GIT layering tool. """
    cli(obj={})


@click.group()
@click.option(
    '--debug/--no-debug',
    default=False,
    help='Enable or disable debug mode. Default is disabled.')
@click.version_option(version=gilt.__version__)
@click.pass_context
def cli(ctx, debug):  # pragma: no cover
    level = logging.INFO
    if debug:
        level = logging.DEBUG
    _setup_logger(level)


@click.command()
@click.option(
    '--config',
    'configfile',
    default='gilt.yml',
    help='Path to config file. Default: gilt.yml')
@click.option('--output-dir', default=os.getcwd(), help='Output path')
@click.option(
    '--cleanup/--no-cleanup', default=True, help="Don't cleanup at completion")
@click.pass_context
def overlay(ctx, configfile, output_dir, cleanup):  # pragma: no cover
    """ Install gilt dependencies """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    config = Config.from_file(configfile)
    engine = OverlayEngine(config, cleanup)
    engine.overlay(output_dir)


cli.add_command(overlay)
