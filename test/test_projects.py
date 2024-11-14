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

""" projects tests """

from collections.abc import Generator

import pytest

from sonar import projects, exceptions
from sonar.audit import config

import utilities as util

def test_get_object(get_test_project: callable) -> None:
    """test_get_object"""
    proj = get_test_project
    assert str(proj) == f"project '{util.TEMP_KEY}'"
    with pytest.raises(exceptions.ObjectNotFound):
        projects.Project.get_object(endpoint=util.SQ, key=util.NON_EXISTING_KEY)


def test_refresh(get_test_project: Generator[projects.Project]) -> None:
    """test_refresh"""
    proj = projects.Project.get_object(endpoint=util.SQ, key=util.EXISTING_PROJECT)
    proj.refresh()

    proj = get_test_project
    proj.delete()
    with pytest.raises(exceptions.ObjectNotFound):
        proj.refresh()


def test_create_delete() -> None:
    """test_create_delete"""
    proj = projects.Project.create(endpoint=util.SQ, key=util.TEMP_KEY, name="temp")
    assert proj.key == util.TEMP_KEY
    assert proj.main_branch().name == "main"
    proj.rename_main_branch("foobar")
    assert proj.main_branch().name == "foobar"
    assert proj.delete()
    with pytest.raises(exceptions.ObjectNotFound):
        proj.refresh()


def test_audit() -> None:
    """test_audit"""
    settings = {k: False for k, v in config.load("sonar-audit").items() if isinstance(v, bool)}
    settings["audit.projects"] = True
    assert len(projects.audit(util.SQ, settings)) == 0
    proj = projects.Project.get_object(endpoint=util.SQ, key=util.LIVE_PROJECT)
    settings["audit.projects.utilityLocs"] = True
    assert len(proj.audit_languages(audit_settings=settings)) == 0
    settings["audit.mode"] = "housekeeper"
    assert len(proj.audit_languages(audit_settings=settings)) == 0


def test_revision() -> None:
    """test_revision"""
    proj = projects.Project.get_object(endpoint=util.SQ, key=util.LIVE_PROJECT)
    assert len(proj.revision()) > 8


def test_export_async() -> None:
    """test_export_async"""
    proj = projects.Project.get_object(endpoint=util.SQ, key=util.LIVE_PROJECT)
    assert proj.export_async() is not None


def test_get_findings() -> None:
    """test_get_findings"""
    proj = projects.Project.get_object(endpoint=util.SQ, key=util.LIVE_PROJECT)
    assert len(proj.get_findings(branch="non-existing-branch")) == 0
    assert len(proj.get_findings(branch="develop")) > 0
    assert len(proj.get_findings(pr="1")) == 0


def test_count_third_party_issues() -> None:
    """test_count_third_party_issues"""
    proj = projects.Project.get_object(endpoint=util.SQ, key="checkstyle-issues")
    assert len(proj.count_third_party_issues(filters={"branch": "develop"})) > 0
    assert len(proj.count_third_party_issues(filters={"branch": "non-existing-branch"})) == 0


def test_webhooks() -> None:
    """test_webhooks"""
    proj = projects.Project.get_object(endpoint=util.SQ, key=util.LIVE_PROJECT)
    assert len(proj.webhooks()) == 0


def test_count() -> None:
    """test_count"""
    assert projects.count(util.SQ) > 30


def test_convert_for_yaml() -> None:
    """test_convert_for_yaml"""
    a_json = projects.export(endpoint=util.SQ, export_settings={})
    assert isinstance(projects.convert_for_yaml(a_json), list)


def test_already_exists() -> None:
    """test_convert_for_yaml"""
    with pytest.raises(exceptions.ObjectAlreadyExists):
        projects.Project.create(endpoint=util.SQ, key=util.EXISTING_PROJECT, name="name")


def test_binding() -> None:
    """test_binding"""
    proj = projects.Project.get_object(util.SQ, util.TEST_KEY)
    assert proj.has_binding()
    assert proj.binding() is not None
    assert proj.binding_key().startswith("github:::okorach-org/demo-github-azdo")
    proj = projects.Project.get_object(util.SQ, util.LIVE_PROJECT)
    assert not proj.has_binding()
    assert proj.binding_key() is None


def test_wrong_key(get_test_project: callable) -> None:
    """test_wrong_key"""
    proj = get_test_project
    proj.key = util.NON_EXISTING_KEY
    assert proj.export_async() is None
    res = proj.export_zip()
    assert "error" in res["status"].lower()
    assert not proj.import_zip()


def test_ci(get_test_project: callable) -> None:
    """test_ci"""
    proj = get_test_project
    assert proj.ci() == "unknown"
    proj.key = util.NON_EXISTING_KEY
    assert proj.ci() == "unknown"


def test_set_links(get_test_project: callable) -> None:
    """test_set_links"""
    proj = get_test_project
    proj.set_links({"links": [{"type": "custom", "name": "google", "url": "https://google.com"}]})
    proj.key = util.NON_EXISTING_KEY
    assert not proj.set_links({"links": [{"type": "custom", "name": "yahoo", "url": "https://yahoo.com"}]})


def test_set_tags(get_test_project: callable) -> None:
    """test_set_tags"""
    proj = get_test_project

    assert proj.set_tags(util.TAGS)
    assert proj.get_tags() == sorted(util.TAGS)
    assert proj.set_tags(["foo"])
    assert proj.get_tags() == ["foo"]
    assert proj.set_tags([])
    assert len(proj.get_tags()) == 0
    assert not proj.set_tags(None)


def test_set_quality_gate(get_test_project: callable) -> None:
    """test_set_quality_gate"""
    proj = get_test_project
    assert proj.set_quality_gate(util.EXISTING_QG)
    assert not proj.set_quality_gate(None)
    assert not proj.set_quality_gate(util.NON_EXISTING_KEY)

    proj.key = util.NON_EXISTING_KEY
    assert not proj.set_quality_gate(util.EXISTING_QG)


def test_ai_code_assurance(get_test_project: callable) -> None:
    """test_set_ai_code_assurance"""
    proj = get_test_project
    assert proj.set_ai_code_assurance(True)
    assert proj.get_ai_code_assurance() is True
    assert proj.set_ai_code_assurance(False)
    assert proj.get_ai_code_assurance() is False
    proj.key = util.NON_EXISTING_KEY
    assert not proj.set_ai_code_assurance(True)
    assert proj.get_ai_code_assurance() is None
    assert not proj.set_ai_code_assurance(False)
    assert proj.get_ai_code_assurance() is None


def test_set_quality_profile(get_test_project: callable) -> None:
    """test_set_quality_profile"""
    proj = get_test_project
    assert proj.set_quality_profile(language="py", quality_profile="Olivier Way")
    assert not proj.set_quality_profile(language="py", quality_profile=util.NON_EXISTING_KEY)
    assert not proj.set_quality_profile(language=util.NON_EXISTING_KEY, quality_profile="Olivier Way")
    proj.key = util.NON_EXISTING_KEY
    with pytest.raises(exceptions.ObjectNotFound):
        proj.set_quality_profile(language="py", quality_profile="Olivier Way")


def test_branch_and_pr() -> None:
    """test_branch_and_pr"""
    proj = projects.Project.get_object(util.SQ, util.LIVE_PROJECT)
    assert len(proj.get_branches_and_prs(filters={"branch": "*"})) >= 2
    assert len(proj.get_branches_and_prs(filters={"branch": "foobar"})) == 0
    assert len(proj.get_branches_and_prs(filters={"pullRequest": "*"})) == 2
    assert len(proj.get_branches_and_prs(filters={"pullRequest": "5"})) == 1