# TestBuDDy-Requirements-coverage
# NFR-01, NFR-02

import errno
import os
import shutil
import tempfile
from pprint import pprint
from urllib.parse import urlparse

from app import dbs
from base_objects import Teststepdefinition, CIRun, Project, Bug, ResultState
from ci_communication import ci_communicators
from issue_tracking import issue_trackers
from processing import processors
import map_database as orm
# import logging
import typing

# logging.basicConfig(format="%d(pathname)s - %(lineno)d - %(levelname)s : %(message)s", level=logging.DEBUG)
# logger = logging.getLogger()
# print = logger.info


class Core:
    """Tested project core that communicates with processing and CI communicator interfaces."""

    def __init__(self, project: orm.Project,
                 language_processor: processors.BaseGherkinProcessorAdapter,
                 ci_communicator: ci_communicators.BaseCICommunicatorAdapter,
                 issue_tracker: typing.Optional[issue_trackers.BaseIssueTrackerAdapter]):
        self.tmp_file = tempfile.mkdtemp(dir="/app/tmp")
        # print("created temporary folder: " + self.tmp_file)
        ci_communicator.set_tmp_workdir(self.tmp_file)
        self.ci_communicator = ci_communicator
        self.language_processor = language_processor
        self.issue_tracker = issue_tracker
        self.project = project

    def __del__(self):
        try:
            # print("removing temporary folder: " + self.tmp_file)
            shutil.rmtree(self.tmp_file, ignore_errors=True)
        except OSError as e:
            # Reraise unless ENOENT: No such file or directory
            # (ok if directory has already been deleted)
            if e.errno != errno.ENOENT:
                raise

    """BDD framework (GherkinProcessor) methods."""
    def parse_scenarios(self, data) -> dict:
        return self.language_processor.parse_scenario(data)

    def prepare_files_for_ci(self, to_push):
        return self.language_processor.prepare_files_for_ci(to_push)

    def prepare_story_file(self, story_content, story_name, tm, to_push):
        return self.language_processor.prepare_story_file(story_content, story_name, tm, to_push)

    def get_story_file_path(self, story_name, tm):
        return self.language_processor.get_story_file_path(story_name, tm)

    def get_ci_variables(self):
        return self.language_processor.get_ci_variables()

    def get_generated_code_info(self):
        return self.language_processor.get_generated_code_info()

    def get_runner_file_info(self):
        return self.language_processor.get_runner_file_info()

    def get_repo_test_dir(self):
        return self.language_processor.get_repo_test_dir()

    def analyze_story_file(self, new_steps_json, tc, tp):
        return self.language_processor.analyze_story_file(new_steps_json, tc, tp)

    def prepare_steps_file(self, old_steps_file_content, steps_dict, tm, tc, to_push):
        return self.language_processor.prepare_steps_file(old_steps_file_content, steps_dict, tm, tc, to_push)

    def get_stories_info(self):
        return self.language_processor.get_stories_info()

    def get_generated_code_file_path(self, tm_id, tm_name_no_spaces):
        return self.language_processor.get_generated_code_file_path(tm_id, tm_name_no_spaces)

    def parse_report_data(self, data):
        return self.language_processor.parse_report_data(data)

    # ------------------------------------------------------------------------------------------------

    """CI/CD tool (CICommunicator) methods."""
    def init_repo(self):
        return self.ci_communicator.init_repo()

    def push(self, to_push, is_init, custom_msg):
        return self.ci_communicator.push(to_push, is_init, custom_msg)

    def save_ci_run(self, ci_run=None, commit_hash=None, pipeline_id=None, trigger_type=None, status=None):
        return self.ci_communicator.save_ci_run(ci_run=ci_run, commit_hash=commit_hash, pipeline_id=pipeline_id,
                                                trigger_type=trigger_type, status=status)

    def trigger_pipeline(self):
        return self.ci_communicator.trigger_pipeline()

    def get_repo_pipelines(self):
        return self.ci_communicator.get_repo_pipelines()

    def add_changed_files_to_repo(self, to_push):
        return self.ci_communicator.add_changed_files_to_repo(to_push)

    def generate_ci_file(self, ci_file_variables, to_push):
        return self.ci_communicator.generate_ci_file(ci_file_variables, to_push)

    def init_push(self):  # can throw an Exception
        """Initial push of CI needed files."""
        self.init_repo()
        ci_file_variables = self.get_ci_variables()
        to_push = {}
        self.generate_ci_file(ci_file_variables, to_push)
        self.prepare_files_for_ci(to_push)
        pipeline_id, commit_hash = self.push(to_push, True, "")
        if commit_hash and pipeline_id:
            self.save_ci_run(commit_hash=commit_hash, pipeline_id=pipeline_id, trigger_type="commit")

    def clean_repo_and_delete_project(self, delete_project=False):
        """Purging repository test modules files."""
        self.init_repo()
        is_purged = self.ci_communicator.purge_repo([self.get_repo_test_dir(), self.get_stories_info()["dir"]])
        if is_purged and delete_project:
            dbs.session.delete(self.project)
            dbs.session.flush()
        if not is_purged:
            print("No changes on project repository. Nothing to purge.")

    def clean_test_step_definitions(self, to_push, tp):
        """Clean test step definitions that are not used by any step anymore."""
        # get all step definitions
        step_defs = dbs.session.query(Teststepdefinition.dbs_model) \
            .filter(Teststepdefinition.dbs_model.project_id == tp.project_id) \
            .filter(~Teststepdefinition.dbs_model.test_steps.any()) \
            .all()
        for step_d in step_defs:
            self.delete_step_from_modules(tp, step_d.id, to_push)
            dbs.session.delete(step_d)
        dbs.session.flush()

    def get_file_current_content(self, path, to_push, force_default=False):
        """Returns current content of modified file, or opens new file and saves
        its current content into a dictionary."""

        class ForceSkip(Exception):
            pass

        try:
            if force_default:
                raise ForceSkip
            if path in to_push:
                return to_push[path]
            else:
                with open(os.path.join(self.tmp_file, path), "r") as f:
                    return f.read()
        except (IOError, ForceSkip) as e:
            #  in case CI files weren't properly initialized, add them
            ci_files = {}
            self.prepare_files_for_ci(ci_files)
            self.generate_ci_file(self.get_ci_variables(), ci_files)
            if path in ci_files:
                print("Reinitializing CI file: " + path)
                return ci_files[path]
            return ""

    def delete_step_from_modules(self, tp, step_def_id, to_push):
        """Delete step from modules."""
        # look through repo files in testplan
        # go through contents of each module and find comment with module name and step definition
        gen_code_info = self.get_generated_code_info()
        for mod in tp.test_modules:
            mod_base_path = self.get_generated_code_file_path(str(mod.id), mod.name_no_spaces)
            mod_path = os.path.join(self.tmp_file, mod_base_path)
            if not os.path.isfile(mod_path):  # module does not have any source code
                continue
            mod_file_content = self.get_file_current_content(mod_base_path, to_push)
            step_comment_string = gen_code_info["step_comment"].format(STEP_DEF_ID=str(step_def_id))
            if step_comment_string in mod_file_content:
                # find it and delete what's between steps file
                start_index = mod_file_content.find(step_comment_string)  # header - start index
                end_index = mod_file_content.find(step_comment_string, start_index + 1)  # footer - end index
                if end_index == -1:
                    raise RuntimeError("Comment footer '" + step_comment_string + "' NOT found in module: " + mod_path)
                new_mod_file_content = mod_file_content[:start_index]\
                                       + mod_file_content[end_index + len(step_comment_string):]
                print("erasing: .... \n" + mod_file_content[start_index:end_index + len(step_comment_string)])
                to_push[mod_base_path] = new_mod_file_content

    def push_and_save_ci(self, to_push, msg):
        """Push files and save CI Run."""
        if not to_push:
            print("No changes in repository, nothing to push!")
            return
        pipeline_id, commit_hash = self.push(to_push, False, msg)
        if commit_hash and pipeline_id:
            self.save_ci_run(commit_hash=commit_hash, pipeline_id=pipeline_id, trigger_type="commit")

    def add_stepsfile_to_runnerfile(self, tm, to_push):
        """Add new module steps file to runnner file."""
        # add stepsfile.java for module into runner file
        gen_code_info = self.get_generated_code_info()
        runner_file_info = self.get_runner_file_info()
        runner_proj_path = os.path.join(runner_file_info["dir"], runner_file_info["filename"])
        runner_file_content = self.get_file_current_content(runner_proj_path, to_push)
        searched_module = gen_code_info["class"].format(TEST_MODULE_NAME=tm.name_no_spaces, TEST_MODULE_ID=str(tm.id))
        if searched_module not in runner_file_content:
            end_index = runner_file_content.find(runner_file_info["add_module_ending"])
            if end_index == -1:  # broken runner file, get default one
                runner_file_content = self.get_file_current_content(runner_proj_path, to_push, True)
                end_index = runner_file_content.find(runner_file_info["add_module_ending"])
            new_runner_content = runner_file_content[:end_index] + (runner_file_info["add_module"]) \
                .format(TEST_MODULE_NAME=tm.name_no_spaces, TEST_MODULE_ID=tm.id) + runner_file_content[end_index:]
            to_push[runner_proj_path] = new_runner_content

    def analyze_steps_to_be_generated_in_repo_modules(self, steps_json, tp, to_push):
        """Analyze which steps to generate in module steps file."""
        # look through repo files for project test plan
        # go through contents of each module and find comment with module name and step definition
        gen_code_info = self.get_generated_code_info()
        for mod in tp.test_modules:  # get all modules:
            mod_filename = gen_code_info["full_filename"] \
                .format(TEST_MODULE_NAME=mod.name_no_spaces, TEST_MODULE_ID=str(mod.id))
            mod_proj_path = os.path.join(gen_code_info["dir"], mod_filename)
            mod_path = os.path.join(self.tmp_file, mod_proj_path)
            #  print("---------------mod: " + mod_filename + " --------------------")
            #  print(mod_path)
            if not os.path.isfile(mod_path):
                # print("module NOT found!!!!")
                continue
            mod_file_content = self.get_file_current_content(mod_proj_path, to_push)
            for s in steps_json[1]:
                step_comment_string = gen_code_info["step_comment"].format(STEP_DEF_ID=s["definition_id"])
                #  isfound = "NOT FOUND"
                if step_comment_string in mod_file_content:
                    s["step_to_generate"] = False
                    #  isfound = "FOUND"
                # print(step_comment_string + " - " + isfound)
        new_steps_json = steps_json[0], list(filter(lambda st: st["operation"] != "delete"
                                                               and st["step_to_generate"] is True, steps_json[1]))

        # generate only unique definitions within test case (no repeating of step definitions)
        clean_steps_json = steps_json[0], []
        steps_to_generate = set()
        for s in new_steps_json[1]:
            if int(s["definition_id"]) not in steps_to_generate:
                steps_to_generate.add(int(s["definition_id"]))
                clean_steps_json[1].append(s)
        # pprint(clean_steps_json)
        return gen_code_info, clean_steps_json

    def update_ci_runs_with_pipelines(self):
        """Update CI Runs and their states."""
        pipelines = self.get_repo_pipelines()
        if not pipelines:
            raise RuntimeError("CI runs NOT found for repo. Did you initialize TestBuDDY repository? "
                               "If not, please call: '<TestBuDDy url:port>" + Project.routing_base + "/"
                               + str(self.project.id) + "'/init_repo'")
        for p_id, p_data in pipelines.items():
            ci_run = dbs.session.query(CIRun.dbs_model) \
                .filter(CIRun.dbs_model.project_id == self.project.id) \
                .filter(CIRun.dbs_model.data.like('%"pipeline_id": ' + str(p_id) + ',%')).first()
            # create and save new pipelines into dbs
            self.save_ci_run(ci_run=ci_run, commit_hash=p_data["sha"], pipeline_id=p_id, trigger_type="other",
                             status=p_data["status"])
        print("CI Runs successfully refreshed based on CI/CD tool.")

    def update_reports(self):
        """Update reports with new parsed data from updated CI Runs. Add possible bug tables if CI Run failed."""
        ci_runs = dbs.session.query(CIRun.dbs_model) \
            .filter(CIRun.dbs_model.project_id == self.project.id) \
            .filter(CIRun.dbs_model.report != None).all()
        for ci_r in ci_runs:
            # I presume 1 report per ci_run with status "failed"/"success"
            print("Updating report for CI run  connected to pipeline_id: " + str(ci_r.pipeline_id))
            new_data = self.parse_report_data(ci_r.report.content_raw)
            ci_r.report.set_parsed_info(new_data)
            dbs.session.flush()
            # pprint(ci_r.report.to_dict())
        print("Reports successfully refreshed based on CI Runs saved in database.")

    def update_bugs(self):
        """Update reports with new parsed data from updated CI Runs. Add possible bug tables if CI Run failed."""
        """Returns: set of modified bugs"""
        failed_result_state = ResultState.dbs_model.query.filter_by(name="failed").first()
        if not failed_result_state:
            raise RuntimeError("Inconsistent database, please reinit test data by calling '/clean-data' "
                               "and '/init-data'.")

        ci_runs = dbs.session.query(CIRun.dbs_model) \
            .filter(CIRun.dbs_model.project_id == self.project.id) \
            .filter(CIRun.dbs_model.result_state_id == failed_result_state.id) \
            .filter(CIRun.dbs_model.report != None).all()
        modified_bugs = set()
        for ci_r in ci_runs:

            if ci_r.report.content_raw == {} or ci_r.report.content_raw == "":
                continue
            report_info = ci_r.report.get_parsed_info()
            if not report_info or "result" not in report_info or report_info["result"] != "failed":
                continue
            if "test_cases" in report_info:
                for tc, tc_info in report_info["test_cases"].items():
                    if tc_info["result"] != "failed":
                        continue
                    # find if bug exists already
                    bugs = dbs.session.query(Bug.dbs_model) \
                        .filter(Bug.dbs_model.project_id == self.project.id) \
                        .filter(Bug.dbs_model.status == "open")\
                        .filter(Bug.dbs_model.data.like('%"' + tc_info["failed_at_step"] + '"%')).all()
                    if not bugs:
                        bug = Bug.dbs_model(status="open", project_id=self.project.id)
                        # bug could be connected to test case here
                        bug.set_data({"test_cases_affected": [tc], "broken_step": tc_info["failed_at_step"]})
                        if ci_r not in bug.ci_runs:
                            bug.ci_runs.append(ci_r)
                        dbs.session.add(bug)
                        dbs.session.flush()
                        print("Creating bug: " + str(bug.id))
                    else:
                        # found new ci_run for bug
                        # BUG ONLY SAVES INFORMATION ABOUT FAILING TEST CASES in CI RUNS, while user is responsible
                        # to check successful ci runs and set bug state to closed if bug is no longer active
                        bug = bugs[0]
                        if ci_r not in bug.ci_runs:
                            bug.ci_runs.append(ci_r)
                        b_data = bug.get_data()
                        if tc not in b_data["test_cases_affected"]:
                            b_data["test_cases_affected"].append(tc)
                        bug.set_data(b_data)
                        print("Refreshing bug: " + str(bug.id))
                        modified_bugs.add(bug)
                        dbs.session.flush()
                    # pprint(bug.to_dict())
        return list(modified_bugs)

    def replace_in_runner(self, runner_file_info, old_val, new_val, to_push):
        """Replace used module in CI runner file"""
        runner_proj_path = os.path.join(runner_file_info["dir"], runner_file_info["filename"])
        runner_file_content = self.get_file_current_content(runner_proj_path, to_push, False)
        if old_val in runner_file_content:
            runner_content = runner_file_content.replace(old_val, new_val)
            to_push[runner_proj_path] = runner_content

    def modify_or_erase_module_story_files(self, old_mod_basename, new_mod_basename, to_push):
        """Rename or erase stories from module folder"""

        stories_info = self.get_stories_info()
        mod_folder_path = os.path.join(stories_info["dir"], old_mod_basename)

        # we only want to erase story files
        if new_mod_basename != "":
            new_mod_folder_path = os.path.join(stories_info["dir"], new_mod_basename)
        else:
            new_mod_folder_path = ""

        if os.path.isdir(os.path.join(self.tmp_file, mod_folder_path)):
            for root, dirs, files in os.walk(os.path.join(self.tmp_file, mod_folder_path)):
                for fil in files:
                    fil_proj_path = os.path.join(mod_folder_path, fil)
                    fil_content = self.get_file_current_content(fil_proj_path, to_push)
                    to_push[fil_proj_path] = "REMOVE"
                    if new_mod_folder_path != "":
                        new_fil_proj_path = os.path.join(new_mod_folder_path, fil)
                        to_push[new_fil_proj_path] = fil_content

    def get_module_formatted_info(self, mod_name, mod_id):
        """Get module info from Langugage processor"""
        gen_code_info = self.get_generated_code_info()
        mod = {}
        mod["base_dir"] = gen_code_info["dir"]
        mod["step_comment"] = gen_code_info["step_comment"]
        mod["full_filename"] = gen_code_info["full_filename"].format(TEST_MODULE_NAME=mod_name,
                                                                     TEST_MODULE_ID=str(mod_id))
        mod["module_steps_base_name"] = gen_code_info["module_steps_base_name"].format(TEST_MODULE_NAME=mod_name,
                                                                                       TEST_MODULE_ID=str(mod_id))
        mod["class"] = gen_code_info["class"].format(TEST_MODULE_NAME=mod_name, TEST_MODULE_ID=str(mod_id))
        mod["proj_path"] = os.path.join(gen_code_info["dir"], mod["full_filename"])
        return mod

    # ------------------------------------------------------------------------------------------------
    """IssueTracker methods."""

    def send_data_to_issue_tracker_bug(self, bugs):
        if self.issue_tracker:
            return self.issue_tracker.send_data_to_issue_tracker_bug(bugs)
        else:
            raise RuntimeError("No Issue Tracker defined in project data. Please update project info.")

    def update_bugs_from_issue_tracker(self):
        if self.issue_tracker:
            return self.issue_tracker.update_bugs_from_issue_tracker()
        else:
            raise RuntimeError("No Issue Tracker defined in project data. Please update project info.")

    def check_if_issue_exists(self, bug):
        if self.issue_tracker:
            return self.issue_tracker.check_if_issue_exists(bug)
        else:
            raise RuntimeError("No Issue Tracker defined in project data. Please update project info.")


class CoreCreator:
    """Core creator which initializes Core object based on set processor, CI communicator
    and Issue Tracker(optional)."""

    def create_core(self, project: orm.Project) -> Core:
        """Project core creation."""
        self.cache_ci_params(project)
        if project.issue_tracker:
            return Core(project, processors.GherkinProcessorFactory().create_processor(project.language_processor),
                        ci_communicators.CICommunicatorFactory().create_ci_communicator(project),
                        issue_trackers.IssueTrackerFactory().create_issue_tracker(project))
        return Core(project, processors.GherkinProcessorFactory().create_processor(project.language_processor),
                    ci_communicators.CICommunicatorFactory().create_ci_communicator(project), None)

    def cache_ci_params(self, project: orm.Project):
        """Cache CI params."""
        try:
            server_url = urlparse(project.repo_url)
            if server_url.scheme is None:
                server_url.scheme = "http"
            new_params = project.get_ci_params()
            new_params["server_base"] = server_url.netloc
            new_params["server_url"] = server_url.scheme + "://"
            new_params["server"] = server_url.scheme + "://" + server_url.netloc
            new_params["proj_path"] = server_url.path
            project.set_ci_params(new_params)
            dbs.session.flush()
        except Exception as e:
            dbs.session.rollback()
            raise e
