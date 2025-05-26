import os
import random

import map_database
from app import dbs


class CIRun:
    dbs_model = map_database.CIRun
    routing_base = '/ci_runs'


class Bug:
    dbs_model = map_database.Bug
    routing_base = '/bugs'


class Requirement:
    dbs_model = map_database.Requirement
    routing_base = '/requirements'

    @staticmethod
    def create_requirements():
        projects = dbs.session.query(Project.dbs_model).all()
        if len(projects) < 2:
            Project.create_projects()
        projects = dbs.session.query(Project.dbs_model).all()
        tags = dbs.session.query(Tag.dbs_model).all()
        if len(tags) < 5:
            Tag.create_tags()
        tags = dbs.session.query(Tag.dbs_model).all()

        num_rows_deleted = dbs.session.query(Requirement.dbs_model).delete()
        content = [
            "All basic application functions are logged.",
            "UI is usable.",
            "User can log into the login screen using his password.",
            "User can manage his files in File management screen.",
            "Service ABC communicates with service XYZ based on protocol on page ABCD.",
            "Passwords are encoded and hashed.",
            "User can manage his personal data.",
            "User can view Weather screen.",
            "Current Weather data are shown on Weather screen.",
            "Application reaction time is above concurrent's average."]
        for p in projects:
            for i in range(len(content)):
                rand_tags = set()
                for _ in range(0, 3):
                    rand_t = tags[(random.randint(0, len(tags) - 1))]
                    rand_tags.add(rand_t)
                req = Requirement.dbs_model(project_id=p.id, content=content[i])
                req.tags = list(rand_tags)
                dbs.session.add(req)
        dbs.session.flush()


class Tag:
    routing_base = '/tags'
    dbs_model = map_database.Tag

    @staticmethod
    def create_tags():
        projects = dbs.session.query(Project.dbs_model).all()
        if len(projects) < 2:
            Project.create_projects()
        projects = dbs.session.query(Project.dbs_model).all()
        num_rows_deleted = dbs.session.query(Tag.dbs_model).delete()
        for p in projects:
            tags = [Tag.dbs_model(content="logging", category="functional", project_id= p.id),
                    Tag.dbs_model(content="usability", category="nonfunctional", project_id=p.id),
                    Tag.dbs_model(content="speed", category="nonfunctional", project_id=p.id),
                    Tag.dbs_model(content="authentication", category="functional", project_id=p.id),
                    Tag.dbs_model(content="file management", category="functional", project_id=p.id),
                    Tag.dbs_model(content="weather screen", category="functional", project_id=p.id),
                    Tag.dbs_model(content="integration with service XYZ", category="functional", project_id=p.id)
                    ]
            dbs.session.add_all(tags)
            dbs.session.flush()

class TriggerType:
    dbs_model = map_database.TriggerType

    @staticmethod
    def create_tt():
        tt_count = int(dbs.session.query(TriggerType.dbs_model).count())
        if tt_count == 3:
            return
        num_rows_deleted = dbs.session.query(TriggerType.dbs_model).delete()
        tt = [TriggerType.dbs_model(type="commit"), TriggerType.dbs_model(type="triggered_run"),
              TriggerType.dbs_model(type="other")]
        dbs.session.add_all(tt)
        dbs.session.flush()


class ResultState:
    dbs_model = map_database.ResultState

    @staticmethod
    def create_rs():
        rs_count = int(dbs.session.query(ResultState.dbs_model).count())
        if rs_count == 6:
            return
        num_rows_deleted = dbs.session.query(ResultState.dbs_model).delete()
        rs = [ResultState.dbs_model(name="pending"), ResultState.dbs_model(name="running"),
              ResultState.dbs_model(name="success"), ResultState.dbs_model(name="failed"),
              ResultState.dbs_model(name="canceled"), ResultState.dbs_model(name="skipped"),
              ResultState.dbs_model(name="created")]
        dbs.session.add_all(rs)
        dbs.session.flush()


class Project:
    dbs_model = map_database.Project
    routing_base = '/projects'

    @staticmethod
    def create_projects():
        # for testing purposes
        if dbs.session.query(Project.dbs_model).filter(Project.dbs_model.name == 'testbuddy-sut').first() == None:
            proj = Project.dbs_model(name="testbuddy-sut",
                                     repo_url='https://pajda.fit.vutbr.cz/testos/testbuddy-sut',
                                     ci_communicator='gitlab', language_processor='java-jbehave',
                                     issue_tracker='jira')
            dbs.session.add(proj)
            proj.set_ci_params({"key": os.getenv('CI_TOKEN')})
            proj.set_issue_tracker_params({"server": "https://tesbuddy.atlassian.net/",
                                           "username": "testbuddyBUT@gmail.com",
                                           "password": os.getenv('JIRA_TOKEN'),
                                           "project_shortcut": "SUT"})

        if dbs.session.query(Project.dbs_model).filter(Project.dbs_model.name == 'testing_repo').first() == None:
            proj2 = Project.dbs_model(name='testing_repo',
                                      repo_url='https://pajda.fit.vutbr.cz/xblozo00/testing_repo',
                                      ci_communicator='gitlab', language_processor='java-jbehave',
                                      issue_tracker='jira')
            dbs.session.add(proj2)
            proj2.set_ci_params({"key": os.getenv('CI_TOKEN')})
            proj2.set_issue_tracker_params({"server": "https://tesbuddy.atlassian.net/",
                                           "username": "testbuddyBUT@gmail.com",
                                           "password": os.getenv('JIRA_TOKEN'),
                                            "project_shortcut": "TTR"})

        offset = dbs.session.query(Project.dbs_model).count()
        for i in range(offset-1):
            dbs.session.add(Project.dbs_model(name='test_proj' + str(i),
                                              repo_url='pajda.fit.vutbr.cz/test_proj' + str(i),
                                              ci_communicator='gitlab', language_processor='java-jbehave',
                                              issue_tracker='jira'))
        dbs.session.flush()


class Report:
    dbs_model = map_database.Report
    routing_base = '/reports'


class TCPriority:
    dbs_model = map_database.Priority

    @staticmethod
    def create_priorities():
        prio_count = int(dbs.session.query(TCPriority.dbs_model).count())
        if prio_count == 3:
            return
        num_rows_deleted = dbs.session.query(TCPriority.dbs_model).delete()
        prio = [TCPriority.dbs_model(type='high'), TCPriority.dbs_model(type='medium'),
                TCPriority.dbs_model(type='low')]
        dbs.session.add_all(prio)
        dbs.session.flush()


class Teststep:
    dbs_model = map_database.TestStep
    routing_base = '/steps'


class Testcase:
    dbs_model = map_database.TestCase
    routing_base = '/cases'

    @staticmethod
    def create_testcases():
        cases_per_module = 3  # default
        tmodules = Testmodule.dbs_model.query.all()
        if not tmodules or len(tmodules) < 3 * int(dbs.session.query(Testplan.dbs_model).count()):
            Testmodule.create_testmodules()
        tmodules = Testmodule.dbs_model.query.all()
        prio = TCPriority.dbs_model.query.all()
        all_users = User.dbs_model.query.all()
        num_rows_deleted = dbs.session.query(Testcase.dbs_model).delete()
        for tm in tmodules:
            for i in range(0, cases_per_module):
                new_tc = Testcase.dbs_model(name="test case " + str(random.randint(0, 666)))
                new_tc.test_module = tm
                new_tc.priority = prio[random.randint(0, len(prio) - 1)]  # assign random priority
                if len(all_users) > 1:
                    new_tc.users_assigned.append(
                        all_users[(random.randint(0, len(all_users) - 1))])  # assign to random user
                    if random.randint(0, 3) <= 2:  # randomly try to assign another random user
                        try:
                            new_tc.users_assigned.append(all_users[(random.randint(0, len(all_users) - 1))])
                        except Exception as e:
                            pass
                dbs.session.add(new_tc)
            dbs.session.flush()


class Teststepdefinition:
    dbs_model = map_database.TestStepDefinition
    routing_base = '/stepdefinitions'


class Gherkintype:
    dbs_model = map_database.GherkinType

    @staticmethod
    def create_gherkintypes():
        gherkin_count = int(dbs.session.query(TCPriority.dbs_model).count())
        if gherkin_count > 3:  # at least 3 basic gherkin types has to be supported
            return
        num_rows_deleted = dbs.session.query(Gherkintype.dbs_model).delete()
        gtypes = [Gherkintype.dbs_model(name='Given'), Gherkintype.dbs_model(name='When'),
                  Gherkintype.dbs_model(name='Then')]
        dbs.session.add_all(gtypes)
        dbs.session.flush()


class Testplan:
    dbs_model = map_database.TestPlan
    routing_base = '/plans'

    @staticmethod
    def create_testplans():
        all_projs_count = int(dbs.session.query(Project.dbs_model).count())
        if all_projs_count < 3:
            Project.create_projects()
        projs = Project.dbs_model.query.filter(Project.dbs_model.test_plan == None).all()
        proj_count = len(projs)
        projs_rand = set()  # projects saved on random indexes in a list
        while len(projs_rand) < proj_count:
            projs_rand.add(projs[random.randint(0, proj_count - 1)])
        for i, proj in enumerate(projs_rand):
            tp = Testplan.dbs_model(name='tp' + str(i), description='test plan for testing purposes')
            tp.project = proj
            dbs.session.add(tp)
        dbs.session.flush()


class Testmodule:
    dbs_model = map_database.TestModule
    routing_base = '/mods'

    @staticmethod
    def create_testmodules():
        mods_per_tp = 3  # default
        testplans = Testplan.dbs_model.query.all()
        if not testplans or int(dbs.session.query(Testplan.dbs_model).count()) < 3:
            Testplan.create_testplans()
        testplans = Testplan.dbs_model.query.all()
        num_rows_deleted = dbs.session.query(Testmodule.dbs_model).delete()
        for tp in testplans:
            for i in range(1, mods_per_tp):
                mod_name = "test module " + str(i)
                tmod = Testmodule.dbs_model(name=mod_name, name_no_spaces=mod_name.replace(" ", ""))
                tp.test_modules.append(tmod)
            dbs.session.flush()


class Role:
    routing_base = '/roles'
    dbs_model = map_database.Role

    @staticmethod
    def create_roles():
        roles_count = int(dbs.session.query(Role.dbs_model).count())
        if roles_count == 3:
            return
        num_rows_deleted = dbs.session.query(Role.dbs_model).delete()
        roles = [Role.dbs_model(name='tester'), Role.dbs_model(name='test architect'),
                 Role.dbs_model(name='project manager')]
        dbs.session.add_all(roles)
        dbs.session.flush()


class User:
    dbs_model = map_database.User
    routing_base = '/users'

    @staticmethod
    def create_users(size):
        roles_count = dbs.session.query(Role.dbs_model).count()
        if roles_count < 3:
            Role.create_roles()
        roles_count = dbs.session.query(Role.dbs_model).count()
        roles_min = dbs.session.query(Role.dbs_model.id).group_by(Role.dbs_model.id).first().id
        for i in range(size):
            role_id = random.randint(roles_min, roles_min + roles_count - 1)
            u = User.dbs_model(username='username_' + str(i + 3), surname='Doe', name='John_' + str(i),
                               password_hash='test')
            u.roles.append(Role.dbs_model.query.get(role_id))
            dbs.session.add(u)
            dbs.session.flush()