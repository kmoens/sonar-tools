#
# sonar-tools
# Copyright (C) 2019-2022 Olivier Korach
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

    Abstraction of the SonarQube "user" concept

'''
import json
import datetime as dt
import pytz
from sonarqube import env
import sonarqube.sqobject as sq
import sonarqube.utilities as util
import sonarqube.audit_problem as pb
import sonarqube.user_tokens as tok
import sonarqube.audit_rules as rules


class User(sq.SqObject):
    API_ROOT = 'users'
    API_CREATE = API_ROOT + '/create'
    API_SEARCH = API_ROOT + '/search'
    API_DEACTIVATE = API_ROOT + '/deactivate'

    def __init__(self, login, endpoint=None, data=None):
        super().__init__(login, endpoint)
        self.login = login
        self.jsondata = data
        self.name = data.get('name', None)
        self.is_local = data.get('local', False)
        self.email = data.get('email', None)
        self.scmAccounts = data.get('scmAccounts', None)
        self.groups = data.get('groups', None)
        self.nb_tokens = data.get('tokenCount', None)
        self.tokens_list = None
        self._last_login_date = None

    def __str__(self):
        return f"user '{self.login}'"

    def deactivate(self):
        env.post(User.API_DEACTIVATE, {'name': self.name, 'login': self.login}, self.endpoint)
        return True

    def tokens(self):
        if self.tokens_list is None:
            self.tokens_list = tok.search(self.login, self.endpoint)
        return self.tokens_list

    def last_login_date(self):
        if self._last_login_date is None and 'lastConnectionDate' in self.jsondata:
            self._last_login_date = util.string_to_date(self.jsondata['lastConnectionDate'])
        return self._last_login_date

    def audit(self, settings=None):
        util.logger.debug("Auditing %s", str(self))

        protected_users = util.csv_to_list(settings['audit.tokens.neverExpire'])
        if self.login in protected_users:
            util.logger.info("%s is protected, last connection date is ignored, tokens never expire", str(self))
            return []

        today = dt.datetime.today().replace(tzinfo=pytz.UTC)
        problems = []

        for t in self.tokens():
            age = abs((today - t.created_at).days)
            if age > settings['audit.tokens.maxAge']:
                rule = rules.get_rule(rules.RuleId.TOKEN_TOO_OLD)
                msg = rule.msg.format(str(t), age)
                problems.append(pb.Problem(rule.type, rule.severity, msg, concerned_object=t))
            if t.last_connection_date is None and age > settings['audit.tokens.maxUnusedAge']:
                rule = rules.get_rule(rules.RuleId.TOKEN_NEVER_USED)
                msg = rule.msg.format(str(t), age)
                problems.append(pb.Problem(rule.type, rule.severity, msg, concerned_object=t))
            if t.last_connection_date is None:
                continue
            last_cnx_age = abs((today - t.last_connection_date).days)
            if last_cnx_age > settings['audit.tokens.maxUnusedAge']:
                rule = rules.get_rule(rules.RuleId.TOKEN_UNUSED)
                msg = rule.msg.format(str(t), last_cnx_age)
                problems.append(pb.Problem(rule.type, rule.severity, msg, concerned_object=t))

        cnx = self.last_login_date()
        if cnx is not None:
            age = abs((today - cnx).days)
            if age > settings['audit.users.maxLoginAge']:
                rule = rules.get_rule(rules.RuleId.USER_UNUSED)
                msg = rule.msg.format(str(self), age)
                problems.append(pb.Problem(rule.type, rule.severity, msg, concerned_object=self))
        return problems

def search(params=None, endpoint=None):
    if params is None:
        params = {}
    return sq.search_objects(
        api=User.API_SEARCH, params=params,
        returned_field='users', key_field='login', object_class=User, endpoint=endpoint)


def create(name, login=None, endpoint=None):
    resp = env.post(User.API_CREATE, {'name': name, 'login': login}, endpoint)
    data = json.loads(resp.text)
    return User(data['login'], data['name'], endpoint, **data)


def audit(audit_settings, endpoint=None):
    if not audit_settings['audit.users']:
        util.logger.info('Auditing users is disabled, skipping...')
        return []
    util.logger.info("--- Auditing users ---")
    problems = []
    for _, u in search(endpoint=endpoint).items():
        problems += u.audit(audit_settings)
    return problems

def get_login_from_name(name, endpoint):
    u_list = search(params={'q': name}, endpoint=endpoint)
    if not u_list:
        return None
    if len(u_list) > 1:
        util.logger.warning("More than 1 user with name '%s', will return the 1st one", name)
    return list(u_list.keys()).pop(0)
