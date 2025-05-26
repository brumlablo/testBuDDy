# TestBuDDy-Requirements-coverage
# NFR-02, FR-07, FR-09, FR-11, FR-13, FR-15

import abc
import os
import re
from pprint import pprint
from collections import OrderedDict

from app import dbs
from base_objects import Gherkintype, Teststepdefinition
from processing.jbehave_src.jbehave_constants import JBehaveConstants


class GherkinProcessorFactory:
    """Factory that handles user input information about their chosen
    processing language/framework for automation and creates chosen object."""

    def create_processor(self, processor_type):
        """ Create your Gherkin Processor here."""
        if processor_type == "java-jbehave":
            return JBehaveGherkinProcessor()
        else:
            raise NotImplemented("Requested Gherkin Processor (Framework) NOT found.")


class BaseGherkinProcessorAdapter(abc.ABC):  # abstract class
    """ Adapter for different parsers (interface) """

    @abc.abstractmethod
    def parse_scenario(self, text_raw):
        """Parse test steps."""
        raise NotImplemented

    @abc.abstractmethod
    def prepare_steps_file(self, old_steps_file_content, steps_json, tm, tc, to_push):
        """Generate test steps."""
        raise NotImplemented

    @abc.abstractmethod
    def prepare_files_for_ci(self, to_push):
        """Initialization of files for CI."""
        raise NotImplemented

    @abc.abstractmethod
    def prepare_story_file(self, story_content, story_name, tm, to_push):
        """Prepare story file."""
        raise NotImplemented

    @abc.abstractmethod
    def get_ci_variables(self):
        """Get CI variables."""
        raise NotImplemented

    @abc.abstractmethod
    def get_generated_code_info(self):
        """Get generated code info."""
        raise NotImplemented

    @abc.abstractmethod
    def get_runner_file_info(self):
        """Get runner file info."""
        raise NotImplemented

    @abc.abstractmethod
    def get_repo_test_dir(self):
        """Get repo test directory."""
        raise NotImplemented

    @abc.abstractmethod
    def get_story_file_path(self, story_name, tm):
        """Get story file project path."""
        raise NotImplemented

    @abc.abstractmethod
    def analyze_story_file(self, new_steps_json, tc, tp):
        """Analyze story file."""
        raise NotImplemented

    @abc.abstractmethod
    def get_stories_info(self):
        """Get stories information."""
        raise NotImplemented

    @abc.abstractmethod
    def get_generated_code_file_path(self, tm_id, tm_name_no_spaces):
        """Get generated code path."""
        raise NotImplemented

    @abc.abstractmethod
    def parse_report_data(self, data):
        """Parse report data."""
        raise NotImplemented


class JBehaveGherkinProcessor(BaseGherkinProcessorAdapter):
    """JBehave processing that parses BDD steps and generates JBehave code."""

    def init_keywords_expected(self, arr):
        out = []
        for i in range(len(arr)):
            if arr[i] in ["Scenario", "Narrative"]:
                to_add = ": "
            else:
                to_add = " "
            out.append(arr[i] + to_add)
        return out

    def __init__(self):
        self.keywords = ["Scenario", "Given", "When", "Then", "!--", "Narrative"]
        self.keywords_expected = self.init_keywords_expected(self.keywords)
        self.PARSER_INCORRECT_SYNTAX = "Incorrect JBehave .story syntax, please refer to jbehave.org."


    def parse_report_data(self, data):
        parsed_data = {}
        test_cases = {}
        if data == "":
            return {"result": "CI build failed"}

        # first check overall result
        if JBehaveConstants.report_fail_check in data:
            parsed_data["result"] = "failed"
        elif JBehaveConstants.report_success_check[0] in data:
            parsed_data["result"] = "success"
            if JBehaveConstants.report_success_check[1] not in data:  # build ok, tc were not performed
                return parsed_data
        else:
            raise RuntimeError(self.PARSER_INCORRECT_SYNTAX + " Incorrect report syntax: missing BUILD RESULT.")

        # parse test case info
        cases_start_index = data.find(JBehaveConstants.report_before_stories)
        cases_end_index = data.find(JBehaveConstants.report_after_stories, cases_start_index + 1)
        if -1 in [cases_start_index, cases_end_index]:
            if parsed_data["result"] == "failed":
                return parsed_data
            raise RuntimeError(self.PARSER_INCORRECT_SYNTAX + " Incorrect report syntax: No stories footers aka "
                                                              "'(BeforeStories)'.")
        stories_base = data[cases_start_index:cases_end_index]

        current_tc = ""
        for ln in stories_base.splitlines():
            ln_base = ln.strip()  # add if empty, continue
            if ln == "":
                continue
            if ln_base.find(JBehaveConstants.report_before_1_story) > -1:
                current_tc = ln_base.replace(JBehaveConstants.report_before_1_story, "")
                test_cases[current_tc] = {"result": "success"}
                continue
            else:
                # check if this is a step
                is_step = False
                for step_base in JBehaveConstants.report_step_base:
                    if step_base in ln_base:
                        is_step = True
                        break
                if is_step:
                    end_index = [ln_base.find(JBehaveConstants.report_step_fail),
                                 ln_base.find(JBehaveConstants.report_step_not_performed)]
                    if end_index[0] > -1:
                        test_cases[current_tc]["result"] = "failed"
                        test_cases[current_tc]["failed_at_step"] = ln_base[:end_index[0]]
                    elif end_index[1] > -1:
                        if "failed_at_step" not in test_cases[current_tc]:
                            test_cases[current_tc]["result"] = " NOT performed"

        # check if result of test cases matches overall build result
        tc_result = "success"
        for case_result in test_cases.values():
            if case_result.get("result", "") == "failed":
                tc_result = "failed"
                break
        if tc_result != parsed_data["result"]:
            raise RuntimeError(self.PARSER_INCORRECT_SYNTAX + " Incorrect report syntax: Test cases results do not "
                                                              "match final CI result.")
        parsed_data["test_cases"] = test_cases
        return parsed_data

    def get_repo_test_dir(self):
        return JBehaveConstants.SUT_TEST_DIR

    def get_stories_info(self):
        return {"dir": JBehaveConstants.stories_base_dir, "file_type": JBehaveConstants.story_file_type}

    def get_runner_file_info(self):
        return {"dir": JBehaveConstants.runner_dir,
                "filename": JBehaveConstants.runner_file_name,
                "add_module": JBehaveConstants.runner_file_module_add,
                "add_module_ending": JBehaveConstants.runner_file_add_module_ending
                }

    def get_generated_code_info(self):
        return {"file_type": JBehaveConstants.generated_code_file_type,
                "step_comment": JBehaveConstants.generated_code_step_comment,
                "class": JBehaveConstants.generated_code_class,
                "module_steps_base_name": JBehaveConstants.module_steps_class_name,
                "full_filename": JBehaveConstants.generated_code_file_full_name,
                "dir": JBehaveConstants.generated_code_dir,
                "class_end": JBehaveConstants.generated_code_class_end
                }

    def get_param_type(self, param):
        # in case we want to take type into account,
        # currently not needed as framework reads all parameters as Strings,
        # so tester will edit type on his own in step definition body
        # try:
        #     int(param)
        #     return "Integer"
        # except Exception as e:
        #     pass
        # try:
        #     float(param)
        #     return "Double"
        # except Exception as e:
        #     pass
        return "String"

    def parse_test_step(self, step_content):
        global param_unit
        params = []
        is_param = False
        param_num = 1
        step_content_renewed = ""
        for c in step_content:
            if c == "[":
                is_param = True
                param_unit = {"content": "", "type": "", "order": "", "name": ""}
                step_content_renewed += "[$"
            elif c == "]":
                is_param = False
                param_unit["type"] = self.get_param_type(param_unit["content"])
                param_unit["name"] = "param_" + str(param_num)
                step_content_renewed += param_unit["name"] + "]"
                param_unit["order"] = param_num
                params.append(param_unit)
                param_num += 1
            elif is_param:
                param_unit["content"] += c
            else:
                step_content_renewed += c
                continue
        return params, step_content_renewed

    def parse_scenario(self, text_raw):
        scenario_raw = text_raw.decode('utf8')
        scenario_raw = scenario_raw.replace("\r", "")
        if scenario_raw[-1] != "\n":
            scenario_raw += "\n"
        inner_pattern = "|".join(self.keywords_expected)  # prepare regex pattern
        matches = re.findall('^[ \t]*((?:' + inner_pattern + ')(?=(.*)(?:\n)))', scenario_raw, re.MULTILINE)
        story_generated = []
        scenarios_steps_data = OrderedDict()
        current_scenario = None
        step_order = 1
        try:
            for i, match in enumerate(matches):
                if i == 0 and match[0] == self.keywords_expected[5]:  #  narrative can be only at the start
                    story_generated.append(match[0] + match[1])
                elif match[0] == self.keywords_expected[0]:  # Scenario start
                    current_scenario = match[1]
                    scenarios_steps_data[current_scenario] = []  # reference to current scenario
                    story_generated.append(match[0] + match[1])
                elif match[0] in self.keywords_expected[:5]:  # not a "narrative"
                    story_generated.append(match[0] + match[1])
                    if match[0] == self.keywords_expected[4]:  # comment
                        continue
                    params = []
                    params, step_gen_content = self.parse_test_step(match[1])  # parse parameters and their types
                    step = {"type": match[0], "order": step_order, "generated_content": step_gen_content,
                            "definition_content": step_gen_content.replace("[$", "{").replace("]", "}"),
                            "raw_content": match[1],
                            "parameters": params}
                    step_order += 1
                    # print(step)
                    scenarios_steps_data[current_scenario].append(step)
                else:
                    raise RuntimeError(self.PARSER_INCORRECT_SYNTAX + "Incorrect keyword: " + match[0])
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(self.PARSER_INCORRECT_SYNTAX) from e
        story_generated_text = ""
        scenario_counter = 0
        for i in range(len(story_generated)):
            if self.keywords_expected[0] in story_generated[i]:  # scenario
                scenario_counter += 1
                if scenario_counter <= 1:
                    story_generated_text += story_generated[i] + "\n"
            elif scenario_counter <= 1:
                story_generated_text += story_generated[i] + "\n"
                if self.keywords_expected[5] in story_generated[i]:  # narrative
                    story_generated_text += "\n"
            else:
                break  # we choose to ignore new scenarios for now
        # pprint(story_generated_text)
        # pprint(scenarios_steps_data)
        return story_generated_text, list(scenarios_steps_data.items())[0]

    def prepare_story_file(self, story_content, story_name, tm, to_push):
        to_push[os.path.join(JBehaveConstants.stories_base_dir, JBehaveConstants.story_dir
                             .format(TEST_MODULE_ID=tm.id, TEST_MODULE_NAME=tm.name_no_spaces),
                             story_name)] = story_content

    def get_story_file_path(self, story_name, tm):
        return os.path.join(JBehaveConstants.stories_base_dir,
                            JBehaveConstants.story_dir.format(TEST_MODULE_ID=tm.id,
                                                              TEST_MODULE_NAME=tm.name_no_spaces), story_name)

    def get_generated_code_file_path(self, tm_id, tm_name_no_spaces):
        mod_name = JBehaveConstants.generated_code_file_full_name\
            .format(TEST_MODULE_ID=tm_id, TEST_MODULE_NAME=tm_name_no_spaces)
        return os.path.join(JBehaveConstants.generated_code_dir, mod_name)

    def prepare_steps_file(self, old_steps_file_content, steps_json, tm, tc, to_push):
        if old_steps_file_content == "":  # init
            generated_code = JBehaveConstants.generated_code_head
            generated_code += JBehaveConstants.generated_code_class_start.format(TEST_MODULE_ID=tm.id,
                                                                                 TEST_MODULE_NAME=tm.name_no_spaces)
        else:
            closing_bracket_index = old_steps_file_content.rfind(JBehaveConstants.generated_code_class_end)
            generated_code = old_steps_file_content[:closing_bracket_index]
        scenario_name, scenario = steps_json
        for step in scenario:
            steps_params = []
            for param_unit in step["parameters"]:
                steps_params.append(JBehaveConstants.generated_code_param_declaration.format(
                    PARAM_UNIT_NAME=param_unit["name"], PARAM_UNIT_TYPE=param_unit["type"]))
            generated_code += JBehaveConstants.generated_code_step_core.format(
                STEP_DEF_ID=step["definition_id"], GHERKIN_TYPE=(step["type"]).strip(),
                STEP_CONTENT=step["generated_content"], STEP_FUNC_DECL="stepCode" + str(step["definition_id"]),
                STEP_PARAMS=", ".join(steps_params))
        generated_code += JBehaveConstants.generated_code_class_end
        mod_name = JBehaveConstants.generated_code_file_full_name\
            .format(TEST_MODULE_ID=tm.id, TEST_MODULE_NAME=tm.name_no_spaces)
        # file[dir+name] =  content
        to_push[os.path.join(JBehaveConstants.generated_code_dir, mod_name)] = generated_code

    def get_ci_variables(self):
        ci_file = {"IMAGE": JBehaveConstants.ci_file_img, "PROCESSOR_VARS": JBehaveConstants.ci_file_variables,
                   "BUILD_SCRIPT": JBehaveConstants.ci_file_build_script,
                   "TEST_SCRIPT": JBehaveConstants.ci_file_test_script,
                   "TEST_ARTIFACTS": JBehaveConstants.ci_file_test_other}
        return ci_file

    def prepare_files_for_ci(self, to_push):
        with open(os.path.join("processing", "jbehave_src", JBehaveConstants.pom_file_name), "r") as file:
            to_push[os.path.join(JBehaveConstants.pom_file_dir, JBehaveConstants.pom_file_name)] = file.read()
        with open(os.path.join("processing", "jbehave_src/", JBehaveConstants.runner_file_name), "r") as file:
            to_push[os.path.join(JBehaveConstants.runner_dir, JBehaveConstants.runner_file_name)] = file.read()

    def analyze_story_file(self, new_steps_json, tc, tp):
        # prepare steps statuses
        for new_s in new_steps_json:
            new_s["tc_id"] = tc.id
            new_s["definition_id"] = None  # new step
            new_s["operation"] = "create"
            new_s_def = dbs.session.query(Teststepdefinition.dbs_model) \
                .filter(Teststepdefinition.dbs_model.content == new_s["definition_content"])\
                .filter((Teststepdefinition.dbs_model.project_id == tp.project_id)) \
                .filter(Teststepdefinition.dbs_model.gherkin_types.any(Gherkintype.dbs_model.name == new_s["type"])) \
                .first()
            if new_s_def is not None:
                new_s["definition_id"] = new_s_def.id
                new_s["operation"] = "modify"
        # find steps to delete
        for old_s in tc.test_steps:
            step_to_delete = True
            for new_s in new_steps_json:
                if old_s.test_step_definition_id == new_s["definition_id"]:
                    step_to_delete = False
            if step_to_delete:
                new_steps_json.append({"operation": "delete", "definition_id": old_s.test_step_definition_id,
                                       "step_id": old_s.id, "tc_id": old_s.test_case.id, "step_to_generate": False})
        return new_steps_json

    # {
    #     "scenario name":
    #        [
    #          {
    #             "type": "given",
    #             "order":"1",
    #             "gen_content: "i am on [$param1] content",
    #             "story_content": "i am on [login] screen"
    #         "parameters" = {"ord":"1", "content":"blabla","type":"string"}
    #         },
    #         {
    #             "type": "when",
    #             "order":"2",
    #             "content:"bblasblasblbslbsl",
    #         "parameters" = [{"content":"blabla","type":"string"},{"content":"blabla","type":"string"}]
    #         },
    #         {
    #             "type": "given",
    #             "order":"3",
    #             "content:"bblasblasblbslbsl",
    #             "parameters" = {"ord":"1", "content":"blabla","type":"string"}
    #         }
    #        ],
    #     "scenario name": []
    # }
