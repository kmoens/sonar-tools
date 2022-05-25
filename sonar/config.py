#!/usr/local/bin/python3
#
# sonar-tools
# Copyright (C) 2022 Olivier Korach
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
"""
    Exports SonarQube platform configuration as JSON
"""
import sys
from sonar import (
    env,
    version,
    settings,
    devops,
    projects,
    qualityprofiles,
    qualitygates,
    portfolios,
    applications,
    permissions,
    users,
    groups,
)
import sonar.utilities as util

"""
def __open_output(file):
    if file is None:
        fd = sys.stdout
        util.logger.info("Dumping report to stdout")
    else:
        fd = open(file, "w", encoding='utf-8')
        util.logger.info("Dumping report to file '%s'", file)
    return fd


def __close_output(file, fd):
    if file is not None:
        fd.close()
        util.logger.info("File '%s' generated", file)
"""

_EVERYTHING = "settings,qp,qg,projects,users,groups,portfolios,apps"

__SETTINGS = "globalSettings"
__QP = "qualityProfiles"
__QG = "qualityGates"
__APPS = "applications"


def __map(k):
    mapping = {"settings": __SETTINGS, "qp": __QP, "qg": __QG, "apps": __APPS}
    return mapping.get(k, k)


def __parse_args(desc):
    parser = util.set_common_args(desc)
    parser = util.set_project_args(parser)
    parser = util.set_output_file_args(parser)
    parser.add_argument(
        "-w",
        "--what",
        required=False,
        default="",
        help="What to export (settings,qp,qg,projects,users,groups,portfolios,apps)",
    )
    args = util.parse_and_check_token(parser)
    util.check_environment(vars(args))
    util.logger.info("sonar-tools version %s", version.PACKAGE_VERSION)
    return args


def __count_settings(what, sq_settings):
    nbr_settings = 0
    for s in what:
        nbr_settings += len(sq_settings.get(__map(s), {}))
    if "settings" in what:
        for categ in settings.CATEGORIES:
            if categ in sq_settings[__SETTINGS]:
                nbr_settings += len(sq_settings[__SETTINGS][categ]) - 1
    return nbr_settings


def main():
    args = __parse_args("Extract SonarQube platform configuration")
    endpoint = env.Environment(some_url=args.url, some_token=args.token)

    what = args.what
    if args.what == "":
        what = _EVERYTHING
    what = util.csv_to_list(what)

    sq_settings = {}
    sq_settings["platform"] = endpoint.basics()
    if "settings" in what:
        sq_settings[__SETTINGS] = endpoint.settings(include_not_set=True)
        sq_settings[__SETTINGS][settings.DEVOPS_INTEGRATION] = list(
            devops.settings(endpoint).values()
        )
        sq_settings[__SETTINGS]["permissions"] = permissions.export(endpoint)
    if "qp" in what:
        sq_settings[__QP] = qualityprofiles.get_list(
            endpoint, include_rules=True, in_hierarchy=True
        )
    if "qg" in what:
        sq_settings[__QG] = qualitygates.get_list(endpoint, as_json=True)
    if "projects" in what:
        project_settings = {}
        for p in projects.get_projects_list(
            str_key_list=None, endpoint=endpoint
        ).values():
            project_settings[p.key] = p.settings()
        sq_settings["projects"] = project_settings
    if "portfolios" in what:
        portfolios_settings = {}
        for k, p in portfolios.search(endpoint=endpoint).items():
            portfolios_settings[k] = p.settings()
        sq_settings["portfolios"] = portfolios_settings
    if "apps" in what:
        apps_settings = {}
        for k, app in applications.search(endpoint=endpoint).items():
            apps_settings[k] = app.settings()
        sq_settings[__APPS] = apps_settings
    if "users" in what:
        sq_settings["users"] = users.get_list(endpoint, as_json=True)
    if "groups" in what:
        sq_settings["groups"] = groups.get_list(endpoint, as_json=True)
    print(util.json_dump(sq_settings))
    util.logger.info("Exported %d items", __count_settings(what, sq_settings))
    sys.exit(0)


if __name__ == "__main__":
    main()
