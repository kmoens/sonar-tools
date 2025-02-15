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

""" Test of the issues module and class, as well as changelog """

from datetime import datetime
import utilities as tutil
from sonar import issues
from sonar import utilities as util
from sonar.util import constants as c


ISSUE_WITH_CHANGELOG = "402452b7-fd3a-4487-97cc-1c996697b397"
ISSUE_2 = "a1fddba4-9e70-46c6-ac95-e815104ead59"


def test_issue() -> None:
    """Test issues"""
    issues_d = issues.search_by_project(endpoint=tutil.SQ, project_key=tutil.LIVE_PROJECT)
    assert ISSUE_WITH_CHANGELOG in issues_d
    issue = issues_d[ISSUE_WITH_CHANGELOG]
    assert not issue.is_security_issue()
    assert not issue.is_hotspot()
    assert not issue.is_accepted()
    assert issue.is_code_smell()
    assert not issue.is_bug()
    assert not issue.is_closed()
    assert not issue.is_vulnerability()
    assert not issue.is_wont_fix()
    assert issue.is_false_positive()
    assert issue.refresh()
    assert issue.api_params(c.LIST) == {"issues": ISSUE_WITH_CHANGELOG}
    assert issue.api_params(c.SET_TAGS) == {"issue": ISSUE_WITH_CHANGELOG}
    assert issue.api_params(c.GET_TAGS) == {"issues": ISSUE_WITH_CHANGELOG}

    assert ISSUE_2 in issues_d
    issue2 = issues_d[ISSUE_2]
    assert not issue.almost_identical_to(issue2)


def test_add_comments() -> None:
    """Test issue comments manipulations"""
    issues_d = issues.search_by_project(
        endpoint=tutil.SQ, project_key="pytorch", params={"impactSeverities": "HIGH", "impactSoftwareQualities": "RELIABILITY"}
    )
    issue = list(issues_d.values())[0]
    comment = f"NOW is {str(datetime.now())}"
    assert issue.add_comment(comment)
    issue.refresh()
    issue_comments = [cmt["value"] for cmt in issue.comments().values()]
    assert comment in issue_comments
    issue_wo_comments = list(issues_d.values())[1]
    assert issue_wo_comments.comments() == {}


def test_set_severity() -> None:
    """Test issue severity"""
    issues_d = issues.search_by_project(endpoint=tutil.SQ, project_key="project1")
    issue = list(issues_d.values())[0]
    old_sev = issue.severity
    new_sev = "MINOR" if old_sev == "CRITICAL" else "CRITICAL"
    assert issue.set_severity(new_sev)
    issue.refresh()
    assert issue.severity == new_sev
    assert not issue.set_severity("NON_EXISTING")
    issue.set_severity(old_sev)


def test_add_remove_tag() -> None:
    """test_add_remove_tag"""
    issues_d = issues.search_by_project(endpoint=tutil.SQ, project_key="project1")
    issue = list(issues_d.values())[0]
    tag = "test-tag"
    issue.remove_tag(tag)
    assert tag not in issue.get_tags()
    issue.add_tag(tag)
    assert tag in issue.get_tags(use_cache=False)
    issue.remove_tag(tag)


def test_set_type() -> None:
    """test_set_type"""
    issues_d = issues.search_by_project(endpoint=tutil.SQ, project_key="project1")
    issue = list(issues_d.values())[0]
    old_type = issue.type
    new_type = c.VULN if old_type == c.BUG else c.BUG
    assert issue.set_type(new_type)
    issue.refresh()
    assert issue.type == new_type
    assert not issue.set_type("NON_EXISTING")
    issue.set_type(old_type)


def test_assign() -> None:
    """test_assign"""
    issues_d = issues.search_by_project(endpoint=tutil.SQ, project_key="project1")
    issue = list(issues_d.values())[0]
    old_assignee = issue.assignee
    new_assignee = "olivier" if old_assignee is None or old_assignee != "olivier" else "michal"
    assert issue.assign(new_assignee)
    issue.refresh()
    assert issue.assignee == new_assignee
    issue.assign("michal")


def test_changelog() -> None:
    """Test changelog"""
    issues_d = issues.search_by_project(endpoint=tutil.SQ, project_key=tutil.LIVE_PROJECT)
    assert ISSUE_WITH_CHANGELOG in issues_d
    issue = issues_d[ISSUE_WITH_CHANGELOG]
    assert issue.key == ISSUE_WITH_CHANGELOG
    assert str(issue) == f"Issue key '{ISSUE_WITH_CHANGELOG}'"
    assert issue.is_false_positive()
    changelog_l = list(issue.changelog().values())
    assert len(changelog_l) == 1
    changelog = changelog_l[0]
    assert changelog.is_resolve_as_fp()
    assert not changelog.is_closed()
    assert not changelog.is_resolve_as_wf()
    assert not changelog.is_confirm()
    assert not changelog.is_unconfirm()
    assert not changelog.is_reopen()
    assert not changelog.is_mark_as_safe()
    assert not changelog.is_mark_as_to_review()
    assert not changelog.is_mark_as_fixed()
    assert not changelog.is_mark_as_acknowledged()
    assert not changelog.is_change_severity()
    assert changelog.new_severity() is None
    assert not changelog.is_change_type()
    assert changelog.new_type() is None
    assert not changelog.is_technical_change()
    assert not changelog.is_assignment()
    assert changelog.new_assignee() is None
    assert changelog.old_assignee() is None
    assert datetime(2024, 10, 20) <= util.string_to_date(changelog.date()).replace(tzinfo=None) < datetime(2024, 10, 22)
    assert changelog.author() == "admin"
    assert not changelog.is_tag()
    assert changelog.get_tags() is None
    (t, _) = changelog.changelog_type()
    assert t == "FALSE-POSITIVE"
