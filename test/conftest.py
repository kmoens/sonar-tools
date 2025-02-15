#!/usr/bin/env python3
#
# sonar-tools tests
# Copyright (C) 2024 Olivier Korach
# mailto:olivier.korach AT gmail DOT com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

""" Test fixtures """

import os
from collections.abc import Generator
import pytest

import utilities as util
from sonar import projects, applications, portfolios, exceptions, logging, issues, users

TEMP_FILE_ROOT = f"temp.{os.getpid()}"
CSV_FILE = f"{TEMP_FILE_ROOT}.csv"
JSON_FILE = f"{TEMP_FILE_ROOT}.json"
YAML_FILE = f"{TEMP_FILE_ROOT}.yaml"

TEST_ISSUE = "a1fddba4-9e70-46c6-ac95-e815104ead59"


def create_test_object(a_class: type, key: str) -> any:
    """Creates a SonarQube test object of a given class"""
    util.start_logging()
    try:
        o = a_class.get_object(endpoint=util.SQ, key=key)
    except exceptions.ObjectNotFound:
        o = a_class.create(endpoint=util.SQ, key=key, name=key)
    return o


@pytest.fixture
def get_test_project() -> Generator[projects.Project]:
    """setup of tests"""
    o = create_test_object(projects.Project, key=util.TEMP_KEY)
    yield o
    # Teardown: Clean up resources (if any) after the test
    o.key = util.TEMP_KEY
    try:
        o.delete()
    except exceptions.ObjectNotFound:
        pass


@pytest.fixture
def get_test_app() -> Generator[applications.Application]:
    """setup of tests"""
    o = create_test_object(applications.Application, key=util.TEMP_KEY)
    yield o
    o.key = util.TEMP_KEY
    try:
        o.delete()
    except exceptions.ObjectNotFound:
        pass


@pytest.fixture
def get_test_portfolio() -> Generator[portfolios.Portfolio]:
    """setup of tests"""
    o = create_test_object(portfolios.Portfolio, key=util.TEMP_KEY)
    yield o
    o.key = util.TEMP_KEY
    try:
        o.delete()
    except exceptions.ObjectNotFound:
        pass


@pytest.fixture
def get_test_portfolio_2() -> Generator[portfolios.Portfolio]:
    """setup of tests"""
    o = create_test_object(portfolios.Portfolio, key=util.TEMP_KEY_2)
    yield o
    o.key = util.TEMP_KEY_2
    try:
        o.delete()
    except exceptions.ObjectNotFound:
        pass


@pytest.fixture
def get_test_subportfolio() -> Generator[portfolios.Portfolio]:
    """setup of tests"""
    parent = create_test_object(portfolios.Portfolio, key=util.TEMP_KEY)
    subp = parent.add_standard_subportfolio(key=util.TEMP_KEY_3, name=util.TEMP_KEY_3)
    yield subp
    subp.key = util.TEMP_KEY_3
    try:
        subp.delete()
    except exceptions.ObjectNotFound:
        pass
    parent.key = util.TEMP_KEY
    try:
        parent.delete()
    except exceptions.ObjectNotFound:
        pass


@pytest.fixture
def get_test_issue() -> Generator[issues.Issue]:
    """setup of tests"""
    issues_d = issues.search_by_project(endpoint=util.SQ, project_key=util.LIVE_PROJECT)
    yield issues_d[TEST_ISSUE]
    # Teardown: Clean up resources (if any) after the test - Nothing in that case


@pytest.fixture
def get_test_user() -> Generator[users.User]:
    """setup of tests"""
    logging.set_logger(util.TEST_LOGFILE)
    logging.set_debug_level("DEBUG")
    try:
        o = users.User.get_object(endpoint=util.SQ, login=util.TEMP_KEY)
    except exceptions.ObjectNotFound:
        o = users.User.create(endpoint=util.SQ, login=util.TEMP_KEY, name=f"User name {util.TEMP_KEY}")
    _ = [o.remove_from_group(g) for g in o.groups() if g != "sonar-users"]
    yield o
    _ = [o.remove_from_group(g) for g in o.groups() if g != "sonar-users"]


def rm(file: str) -> None:
    """Removes a file if exists"""
    try:
        os.remove(file)
    except FileNotFoundError:
        pass


def get_temp_filename(ext: str) -> str:
    """Returns a temp output file for tests"""
    logging.set_logger("pytest.log")
    logging.set_debug_level("DEBUG")
    file = f"{TEMP_FILE_ROOT}.{ext}"
    rm(file)
    return file


@pytest.fixture
def get_csv_file() -> Generator[str]:
    """setup of tests"""
    file = get_temp_filename("csv")
    yield file
    rm(file)


@pytest.fixture
def get_json_file() -> Generator[str]:
    """setup of tests"""
    file = get_temp_filename("json")
    yield file
    rm(file)


@pytest.fixture
def get_yaml_file() -> Generator[str]:
    """setup of tests"""
    file = get_temp_filename("yaml")
    rm(file)
    yield file
    rm(file)


@pytest.fixture
def get_sarif_file() -> Generator[str]:
    """setup of tests"""
    file = get_temp_filename("sarif")
    yield file
    rm(file)
