#!/usr/local/bin/python3
#
# sonar-tools
# Copyright (C) 2021 Olivier Korach
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
'''
    Exports LoC per projects
'''
import json
import sys
from sonarqube import projects, env, version
import sonarqube.utilities as util

sep = ','


def __deduct_format(fmt, file):
    if fmt is not None:
        return fmt
    if file is not None:
        ext = file.split('.').pop(-1).lower()
        if ext == 'json':
            return ext
    return 'csv'


def __csv_line(project, with_name=False, with_analysis=False):

    line = f"{project.key}"
    if with_name:
        line += f"{sep}{project.name}"
    line += f"{sep}{project.ncloc(include_branches=True)}"
    if with_analysis:
        line += f"{sep}{project.last_analysis_date(include_branches=True)}"
    return line

def __dump_loc(project_list, file, file_format, **kwargs):
    if file is None:
        fd = sys.stdout
        util.logger.info("Dumping LoC report to stdout")
    else:
        fd = open(file, "w", encoding='utf-8')
        util.logger.info("Dumping LoC report to file '%s'", file)

    with_name = kwargs['projectName']
    with_last = kwargs['lastAnalysis']
    if file_format != 'json':
        print("# Project Key", end='', file=fd)
        if with_name:
            print(f"{sep}Project Name", end='', file=fd)
        print(f"{sep}LoC", end='', file=fd)
        if with_last:
            print(f"{sep}Last Analysis", end='', file=fd)
        print('', file=fd)
    nb_loc = 0
    nb_projects = 0
    loc_list = []
    for _, p in project_list.items():
        project_loc = p.ncloc(include_branches=True)
        if file_format == 'json':
            data = {'projectKey': p.key, 'ncloc': project_loc}
            if with_name:
                data['projectName'] = p.name
            if with_last:
                data['last_analysis'] = p.last_analysis_date(include_branches=True)
            loc_list.append(data)
        else:
            print(__csv_line(p, with_name, with_last), end='', file=fd)
        nb_loc += project_loc
        nb_projects += 1
        if nb_projects % 50 == 0:
            util.logger.info("%d PROJECTS and %d LoCs, still counting...", nb_projects, nb_loc)
    if file_format == 'json':
        print(json.dumps(loc_list, indent=3, sort_keys=False, separators=(',', ': ')), file=fd)
    if file is not None:
        fd.close()
    util.logger.info("%d PROJECTS and %d LoCs", len(project_list), nb_loc)


def main():
    parser = util.set_common_args('Extract projects lines of code, as computed for the licence')
    parser = util.set_component_args(parser)
    parser.add_argument('-n', '--projectName', required=False, default=False, action='store_true',
                        help='Also list the project name on top of the project key')
    parser.add_argument('-a', '--lastAnalysis', required=False, default=False, action='store_true',
                        help='Also list the last analysis date on top of nbr of LoC')
    parser.add_argument('-o', '--outputFile', required=False, help='File to generate the report, default is stdout'
                        'Format is automatically deducted from file extension, if extension given')
    parser.add_argument('-f', '--format', required=False, default='csv',
                        help='Format of output (json, csv), default is csv')
    args = util.parse_and_check_token(parser)
    endpoint = env.Environment(url=args.url, token=args.token)
    util.check_environment(vars(args))
    util.logger.info('sonar-tools version %s', version.PACKAGE_VERSION)

    args.format = __deduct_format(args.format, args.outputFile)
    project_list = projects.search(endpoint=endpoint)
    __dump_loc(project_list, args.outputFile, args.format, **vars(args))
    sys.exit(0)


if __name__ == '__main__':
    main()
