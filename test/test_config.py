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

import os

import pytest

from gilt.config import Config, ParseError, DEFAULT_BASE_DIR


@pytest.mark.parametrize(
    'gilt_config_file', ['gilt_data'], indirect=['gilt_config_file'])
def test_config(gilt_config_file):
    result = Config.from_file(gilt_config_file)
    os_split = pytest.helpers.os_split

    r = result.overlays[0]
    assert 'https://github.com/retr0h/ansible-etcd.git' == r.git
    assert 'master' == r.version
    assert 'ansible-etcd' == r.name
    assert 'roles/retr0h.ansible-etcd/' == r.dst
    assert 'roles/retr0h.ansible-etcd/' == r.files[0].dst
    assert 1 == len(r.files)

    r = result.overlays[1]
    assert 'https://github.com/lorin/openstack-ansible-modules.git' == r.git
    assert 'master' == r.version
    assert 'openstack-ansible-modules' == r.name
    assert r.dst is None

    f = r.files[0]
    assert f.src == '*_manage'
    assert f.dst == 'library/'


@pytest.fixture()
def missing_git_key_data():
    return [{'foo': 'https://github.com/retr0h/ansible-etcd.git'}]


@pytest.mark.parametrize(
    'gilt_config_file', ['missing_git_key_data'],
    indirect=['gilt_config_file'])
def test_config_missing_git_key(gilt_config_file):
    with pytest.raises(ParseError):
        Config.from_file(gilt_config_file)


@pytest.fixture()
def missing_version_key_data():
    return [{
        'git': 'https://github.com/retr0h/ansible-etcd.git',
        'foo': 'master'
    }]


@pytest.mark.parametrize(
    'gilt_config_file', ['missing_version_key_data'],
    indirect=['gilt_config_file'])
def test_config_missing_version_key(gilt_config_file):
    result = Config.from_file(gilt_config_file)
    assert result.overlays[0].version == 'master'


@pytest.fixture()
def missing_files_src_key_data():
    return [{
        'git': 'https://github.com/lorin/openstack-ansible-modules.git',
        'version': 'master',
        'files': [{
            'foo': '*_manage',
            'dst': 'library/'
        }]
    }]


@pytest.fixture()
def missing_files_dst_key_data():
    return [{
        'git': 'https://github.com/lorin/openstack-ansible-modules.git',
        'version': 'master',
        'files': [{
            'src': '*_manage',
            'foo': 'library/'
        }]
    }]


@pytest.mark.parametrize(
    'gilt_config_file',
    ['missing_files_src_key_data', 'missing_files_dst_key_data'],
    indirect=['gilt_config_file'])
def test_config_missing_files_src_key(gilt_config_file):
    with pytest.raises(ParseError):
        Config.from_file(gilt_config_file)


@pytest.fixture()
def invalid_gilt_data():
    return '{'


@pytest.mark.parametrize(
    'gilt_config_file', ['invalid_gilt_data'], indirect=['gilt_config_file'])
def test_get_config_handles_parse_error(gilt_config_file):
    with pytest.raises(ParseError):
        Config.from_file(gilt_config_file)


def test_autogen_fields():
    config = Config()
    assert [] == config.overlays
    assert DEFAULT_BASE_DIR == config.base_dir
    assert os.path.join(DEFAULT_BASE_DIR, 'lock') == config.lock_file
    assert os.path.join(DEFAULT_BASE_DIR, 'clone') == config.clone_dir
