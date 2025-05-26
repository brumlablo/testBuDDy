# TestBuDDy-Requirements-coverage
# NFR-02, FR-08, FR-09, FR-11, FR-12, FR-14, FR-15

import os
import shutil
import traceback
import datetime
from pprint import pprint
import gitlab
import abc
import git
from app import dbs
from base_objects import CIRun, TriggerType, ResultState, Project, Report

# import logging
# logger = logging.getLogger()
# print = logger.info


class CICommunicatorFactory:
    """Factory that handles user input information about their chosen CI
     and creates needed CI object."""

    def create_ci_communicator(self, project):
        """Create your CI communicator here."""
        if project.ci_communicator == "gitlab":
            return GitlabCICommunicator(project, ".gitlab-ci.yml")
        else:
            raise NotImplemented("Requested CI communicator NOT found.")


class BaseCICommunicatorAdapter(abc.ABC):  # abstract class
    """Adapter for CI communication """

    @abc.abstractmethod
    def __init__(self, project, ci_file_name):
        self.project = project
        self.repo_url = project.repo_url
        self.ci_file_name = ci_file_name

    @abc.abstractmethod
    def get_ci_file_name(self):
        raise NotImplemented

    @abc.abstractmethod
    def push(self, to_push, is_init, custom_msg):
        raise NotImplemented

    @abc.abstractmethod
    def trigger_pipeline(self):
        raise NotImplemented

    @abc.abstractmethod
    def set_tmp_workdir(self, tmp_file):
        raise NotImplemented

    @abc.abstractmethod
    def save_ci_run(self, ci_run=None, commit_hash=None, pipeline_id=None, trigger_type=None, status=None):
        raise NotImplemented

    @abc.abstractmethod
    def add_changed_files_to_repo(self, to_push):
        raise NotImplemented

    @abc.abstractmethod
    def generate_ci_file(self, ci_file_variables, to_push):
        raise NotImplemented

    @abc.abstractmethod
    def init_repo(self):
        raise NotImplemented

    @abc.abstractmethod
    def purge_repo(self, test_dir):
        raise NotImplemented

    @abc.abstractmethod
    def get_pipeline_info(self, p_id):
        raise NotImplemented

    @abc.abstractmethod
    def get_remote_repo(self):
        raise NotImplemented

    @abc.abstractmethod
    def get_repo_pipelines(self):
        raise NotImplemented

    @abc.abstractmethod
    def get_pipeline_output(self, pipeline_id):
        raise NotImplemented


class GitlabCICommunicator(BaseCICommunicatorAdapter):

    def __init__(self, project, ci_file_name):
        super().__init__(project, ci_file_name)
        self.tmp_workdir = None
        self.repo = None
        try:
            self.repo_string = self.project.get_ci_params()["server_url"] + "oauth2:" + self.project.get_ci_params()[
                "key"] + "@" + self.project.get_ci_params()["server_base"] + self.project.get_ci_params()[
                "proj_path"] + ".git"
        except KeyError:
            raise RuntimeError("Project 'ci_params' are not sufficient. Also, did you initialize TestBuDDY repository? "
                               "If not, please call: '<TestBuDDY web>" + Project.routing_base + "/" +
                               str(self.project.id) + "'/init_repo'")

    def purge_repo(self, dirs_to_del):
        """Clean TestBuDDy test library on repository."""
        try:
            for dir_to_purge in dirs_to_del:
                for root, dirs, files in os.walk(os.path.join(self.tmp_workdir, dir_to_purge)):
                    for file in files:
                        rem_path = os.path.join(root, file)
                        os.remove(rem_path)
                    for d in dirs:
                        shutil.rmtree(os.path.join(root, d), ignore_errors=True)

            changed_files = [item.a_path for item in self.repo.index.diff(None)]  # find changes
            if not changed_files:
                print("Repository clean - nothing changed!")
                return False  # nothing was committed
            commit_msg = "TestBuDDy - push: PROJECT REPO CLEANED at " + str(datetime.datetime.now())
            self.repo.index.remove(changed_files)  # stage new changes
            self.repo.index.commit(commit_msg)  # commit staged changes
            self.repo.git.push()
        except Exception as e:
            traceback.print_exc()
            print(e)
            raise
        return True

    def init_repo(self):
        """Initialize local repository into tmp folder. (clone)"""
        if self.repo is None:
            self.repo = git.Repo.clone_from(self.repo_string, self.tmp_workdir)

    def generate_ci_file(self, ci_file_variables, to_push):
        """Generate CI file."""
        with open(os.path.join("ci_communication", "gitlabci_src", self.get_ci_file_name()), "r") as f:
            ci_file = f.read()
        ci_file_cont = ci_file.format(IMAGE=ci_file_variables.get("IMAGE", ""),
                                      PROCESSOR_VARS=ci_file_variables.get("PROCESSOR_VARS", ""),
                                      BUILD_SCRIPT=ci_file_variables.get("BUILD_SCRIPT", ""),
                                      TEST_SCRIPT=ci_file_variables.get("TEST_SCRIPT", ""),
                                      TEST_ARTIFACTS=ci_file_variables.get("TEST_ARTIFACTS", ""))
        to_push[self.get_ci_file_name()] = ci_file_cont

    def get_ci_file_name(self):
        """Get CI file name. """
        return self.ci_file_name

    def set_tmp_workdir(self, tmp_file):
        """ Set tmp folder for local clone of repository. """
        self.tmp_workdir = tmp_file

    def push(self, to_push, is_init, custom_msg):
        """Push files to project repository."""

        print("Preparing files to push into: " + self.repo_string)
        # print("Tmp folder: " + self.tmp_workdir)
        self.init_repo()

        # pom, runner
        self.add_changed_files_to_repo(to_push)

        # self.repo.index.add(self.repo.untracked_files)  # stage new changes
        # changed_files = [item.a_path for item in self.repo.index.diff(None)]  # stage modified files against local repo
        if len(self.repo.index.diff("HEAD")) == 0:  # count staged files against remote repo
            print("No changes in repository, nothing to push!")
            return None, None  # nothing was committed
        if is_init:
            commit_msg = "TestBuDDy - push: INITIAL CI PREPARATION - at " + str(datetime.datetime.now()) + " [ci skip]"
        else:
            commit_msg = "TestBuDDy - push: " + custom_msg + "- at " + str(datetime.datetime.now())
        self.repo.index.commit(commit_msg)  # commit staged changes
        self.repo.git.push()
        print(self.repo.commit().message)
        # for c in my_repo.iter_commits():
        #     print(c.message)
        # print("status: ", my_repo.git.status())

        remote_repo = self.get_remote_repo()
        # print("last commit: ", my_repo.commit(), " and ", my_repo.commit().hexsha)
        # print("remote repo: ", remote_repo)
        pipelines = remote_repo.pipelines.list()
        for p in pipelines:
            if p.sha == self.repo.commit().hexsha:
                pprint("pipeline id: " + str(p.id) + ", commit_hash: " + p.sha)
                return p.id, p.sha
        return None, None

    def get_remote_repo(self):
        """Get remote repository."""
        try:
            server = gitlab.Gitlab(self.project.get_ci_params()["server"], self.project.get_ci_params()["key"])
            server.auth()
            remote_repo = server.projects.get(self.project.get_ci_params()["proj_path"][1:])
            return remote_repo
        except KeyError as e:
            raise RuntimeError("Project 'ci_params' are not sufficient. Also, did you initialize TestBuDDY repository? "
                               "If not, please call: '<TestBuDDy url:port>" + Project.routing_base + "/" +
                               str(self.project.id) + "'/init_repo'")

    def get_pipeline_output(self, pipeline_id):
        """Get pipeline output."""
        remote_repo = self.get_remote_repo()
        pipeline = remote_repo.pipelines.get(pipeline_id)
        # TODO: mention in doc that CI stage has to be named "test"
        all_test_jobs = list(filter(lambda x: x.name == "test", pipeline.jobs.list(all=True)))
        if all_test_jobs:  # in case of invalid yaml syntax
            test_job_base = all_test_jobs[0]
            test_job = remote_repo.jobs.get(test_job_base.id, lazy=True)
            return test_job.trace().decode("utf-8")
        return ""

    def get_repo_pipelines(self):
        """Get repo pipelines."""
        remote_repo = self.get_remote_repo()
        pipelines = remote_repo.pipelines.list(all=True)
        result = {}
        for p in pipelines:
            result[p.id] = {"sha": p.sha, "status": p.status}
        return result

    def add_changed_files_to_repo(self, to_push):
        """Save changes to local repository."""
        for proj_path, content in to_push.items():
            f_path = os.path.join(self.tmp_workdir, proj_path)
            pprint(f_path)
            os.makedirs(os.path.dirname(f_path), exist_ok=True)
            if content == "REMOVE":
                try:
                    os.remove(f_path)
                    self.repo.index.remove([proj_path])
                except IOError as e: # skip files that are already erased
                    pass
            else:
                with open(f_path, "w") as f:
                    f.write(content)
                self.repo.index.add([proj_path])

    def save_ci_run(self, ci_run=None, commit_hash=None, pipeline_id=None, trigger_type=None, status=None):
        """Save new CI Run and report if necessary or update already existing CI Run."""
        pipeline_data = {}
        # evaluate new data
        pipeline_data_raw = self.get_pipeline_info(pipeline_id)

        if ci_run:  # i have an existing ci_run
            print("Processing ci_run for pipeline: " + str(ci_run.pipeline_id))
            pipeline_data = ci_run.get_data()
            # already processed pipeline
            if pipeline_data.get("status", "pending") in ["failed", "success"] and not ci_run.report:  # finished CI run
                # save ci run base output for report - (for gitlab) tracefile
                output_file = "" + self.get_pipeline_output(pipeline_data["pipeline_id"])
                report = Report.dbs_model(ci_run_id=ci_run.id, content_raw=output_file,
                                          date=self.get_python_date(pipeline_data_raw.created_at))
                dbs.session.add(report)
                dbs.session.flush()
                return
        else:
            if pipeline_id:
                pipeline_data["pipeline_id"] = pipeline_id
            if commit_hash:
                pipeline_data["commit_hash"] = commit_hash

        if status:
            pipeline_data["status"] = status
        else:
            pipeline_data["status"] = pipeline_data_raw.status

        # add state
        result_state = ResultState.dbs_model.query.filter_by(name=pipeline_data["status"]).first()
        if not result_state:
            raise RuntimeError("Inconsistent database, please reinit test data by calling '/clean-data' "
                               "and '/init-data'.")
        if not ci_run:  # new ci_run
            trigger_type = TriggerType.dbs_model.query.filter_by(type=trigger_type).first()  # created by commit
            ci_run = CIRun.dbs_model(trigger_type_id=trigger_type.id, pipeline_id=pipeline_data["pipeline_id"],
                                     project_id=self.project.id, result_state_id=result_state.id)
            dbs.session.add(ci_run)
            dbs.session.flush()
            print("Creating ci_run for pipeline: " + str(ci_run.pipeline_id))
            if pipeline_data.get("status", "pending") in ["failed", "success"]:  # finished CI run
                # save ci run base output for report - (for gitlab) tracefile
                output_file = "" + self.get_pipeline_output(pipeline_data["pipeline_id"])
                report = Report.dbs_model(ci_run_id=ci_run.id, content_raw=output_file,
                                          date=self.get_python_date(pipeline_data_raw.created_at))
                # parse report information
                dbs.session.add(report)

        ci_run.result_state = result_state

        # set new data
        ci_run.set_data(pipeline_data)

        dbs.session.flush()

    def trigger_pipeline(self):
        """Trigger new CI Run (connected to pipeline)."""
        remote_repo = self.get_remote_repo()
        pipeline = remote_repo.pipelines.create({'ref': 'master'})  # possible support for more branches in future
        return pipeline.id, pipeline.sha

    def get_pipeline_info(self, p_id):
        """Get all pipeline info from API."""
        return self.get_remote_repo().pipelines.get(p_id)

    def get_python_date(self, raw_date):
        """Pythonize API date."""
        return datetime.datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S.%fZ")
