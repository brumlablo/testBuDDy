# TestBuDDy-Requirements-coverage
# FR-06, FR-07, FR-13, FR-14

import json
import traceback

from flask import request, jsonify
import core
import base_objects
from app import dbs, app
import consts
from endpoints.test_specification_plan_module import check_if_tmod_in_tp, check_if_tp_in_proj
from base_objects import TCPriority, Testcase, Testplan, Testmodule, Teststepdefinition, Teststep, Gherkintype, Project


def check_if_tc_in_tmod(tc, tmod):
    if not (tc and tmod):
        raise RuntimeError("Test case or test module does not exist.")
    if tc not in tmod.test_cases:
        raise RuntimeError("Test case with id: " + str(tc.id) + " NOT found within test module with id: "
                           + str(tmod.id) + ".")


@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base + '/<tp_id>'
           + Testmodule.routing_base + '/<tm_id>' + Testcase.routing_base, methods=['GET'])
def get_tmod_list_tcases(proj_id, tp_id, tm_id):
    try:
        dbs.session.begin()
        p = Project.dbs_model.query.get(proj_id)
        tp = Testplan.dbs_model.query.get(tp_id)
        tm = Testmodule.dbs_model.query.get(tm_id)
        check_if_tp_in_proj(tp, p)
        check_if_tmod_in_tp(tm, tp)
        if not tm or not tm.test_cases:
            raise RuntimeError("Test module not found or does not have any test cases.")
    except Exception as e:
        print(e)
        return "Test cases NOT found: " + str(e), consts.HTTP_404_NOT_FOUND
    response = {"message": "Successfully found test module test cases.",
                "object": [tcc.to_dict() for tcc in tm.test_cases]}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base + '/<tp_id>'
           + Testmodule.routing_base + '/<tm_id>' + Testcase.routing_base + '/<tc_id>', methods=['GET'])
def get_tcase(proj_id, tp_id, tm_id, tc_id):
    try:
        dbs.session.begin()
        p = Project.dbs_model.query.get(proj_id)
        tp = Testplan.dbs_model.query.get(tp_id)
        tm = Testmodule.dbs_model.query.get(tm_id)
        tc = Testcase.dbs_model.query.get(tc_id)
        check_if_tp_in_proj(tp, p)
        check_if_tmod_in_tp(tm, tp)
        check_if_tc_in_tmod(tc, tm)
    except RuntimeError as re:
        print(re)
        return str(re), consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "Error while accessing test plan, test module or test case from database.", consts.HTTP_404_NOT_FOUND
    tc_d = tc.to_dict()
    tc_d['users_assigned'] = [u_a.id for u_a in tc.users_assigned]
    tc_d['scenario_content'] = ""
    if tc.scenario_content is not None and tc.scenario_content != "":
        tc_d['scenario_content'] = tc.scenario_content
    return jsonify({"message": "Test case successfully found:.", "object": tc_d}), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base + '/<tp_id>'
           + Testmodule.routing_base + '/<tm_id>' + Testcase.routing_base, methods=['POST'])
def create_tc(proj_id, tp_id, tm_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None or 'name' not in data_dict:
            return "Invalid json data, please provide 'name'.", consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    dbs.session.begin()
    try:
        p = Project.dbs_model.query.get(proj_id)
        tp = Testplan.dbs_model.query.get(tp_id)
        tm = Testmodule.dbs_model.query.get(tm_id)
        check_if_tp_in_proj(tp, p)
        check_if_tmod_in_tp(tm, tp)

        if 'priority' not in data_dict:
            prio = TCPriority.dbs_model.query.filter_by(type="low").first()
        else:
            prio = TCPriority.dbs_model.query.get(data_dict['priority'])
        # create new test case
        new_tc = Testcase.dbs_model(name=data_dict['name'])
        new_tc.test_module = tm
        new_tc.priority = prio
        if 'users_assigned' in data_dict:
            for u in data_dict['users_assigned']:
                user = base_objects.User.dbs_model.query.get(u)
                if not user:
                    continue
                if user not in new_tc.users_assigned:
                    new_tc.users_assigned.append(user)
                    dbs.session.flush()
        dbs.session.add(new_tc)
        dbs.session.commit()
    except RuntimeError as re:
        print(re)
        return str(re), consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        traceback.print_exc()
        dbs.session.rollback()
        return "Error while working with database. Test case could NOT be created.", \
               consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Successfully created test case .", "object": new_tc.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base + '/<tp_id>'
           + Testmodule.routing_base + '/<tm_id>' + Testcase.routing_base + '/<tc_id>', methods=['DELETE'])
def delete_tc(proj_id, tp_id, tm_id, tc_id):
    try:
        dbs.session.begin()
        p = Project.dbs_model.query.get(proj_id)
        tp = Testplan.dbs_model.query.get(tp_id)
        tm = Testmodule.dbs_model.query.get(tm_id)
        tc = Testcase.dbs_model.query.get(tc_id)
        check_if_tp_in_proj(tp, p)
        check_if_tmod_in_tp(tm, tp)
        check_if_tc_in_tmod(tc, tm)
    except RuntimeError as re:
        print(re)
        return str(re), consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "Error while accessing project, test plan, test module or test case from database. " \
               "Test case could NOT be deleted.", consts.HTTP_404_NOT_FOUND
    try:
        proj_core = core.CoreCreator().create_core(tp.project)
        to_push = {}
        proj_core.init_repo()

        # erase story file
        if tc.scenario_name is not None and tc.scenario_name != "":
            to_push[proj_core.get_story_file_path(tc.scenario_name+str(tc_id)
                                                  + proj_core.get_stories_info()["file_type"], tm)] = "REMOVE"

        # remove all old steps from database (mandatory after analysis!)
        for s in tc.test_steps:
            dbs.session.delete(s)
        dbs.session.flush()
        proj_core.clean_test_step_definitions(to_push, tp)
        dbs.session.delete(tc)

        # save CI run
        proj_core.push_and_save_ci(to_push, "TEST CASE: REMOVAL")
        dbs.session.commit()
    except RuntimeError as re:
        print(re)
        traceback.print_exc()
        dbs.session.rollback()
        return "Error deleting test case with id: " + str(tc_id) + ", test case could not be deleted.", \
               consts.HTTP_500_INTERNAL_SERVER_ERROR
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error deleting test case with id: " + str(tc_id) + ", test case could not be deleted.", \
               consts.HTTP_500_INTERNAL_SERVER_ERROR
    return "Successfully deleted test case from module and repository.\n", consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base + '/<tp_id>'
           + Testmodule.routing_base + '/<tm_id>' + Testcase.routing_base + '/<tc_id>', methods=['PUT'])
def update_tcase_info(proj_id, tp_id, tm_id, tc_id):
    """Updates test case basic information, but not steps."""

    if request.headers['Content-Type'] != 'application/json':
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    data_dict = request.get_json()
    if data_dict is None:
        return "Invalid json data.", consts.HTTP_400_BAD_REQUEST
    try:
        dbs.session.begin()
        p = Project.dbs_model.query.get(proj_id)
        tp = Testplan.dbs_model.query.get(tp_id)
        tm = Testmodule.dbs_model.query.get(tm_id)
        tc = Testcase.dbs_model.query.get(tc_id)
        check_if_tp_in_proj(tp, p)
        check_if_tmod_in_tp(tm, tp)
        check_if_tc_in_tmod(tc, tm)
    except RuntimeError as re:
        print(re)
        return str(re), consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "Error while accessing project, test plan, test module or test case from database.",\
               consts.HTTP_404_NOT_FOUND
    if 'priority' in data_dict:
        tc.priority = TCPriority.dbs_model.query.filter_by(type=data_dict['priority']).first()
    if 'description' in data_dict and data_dict["description"] != "":
        tc.description = data_dict['description']
    if 'name' in data_dict:
        proj_core = core.CoreCreator().create_core(tp.project)
        to_push = {}
        proj_core.init_repo()
        # modify story file
        if tc.scenario_name is not None and tc.scenario_name != "":
            to_push[proj_core.get_story_file_path(tc.scenario_name + str(tc_id) +
                                                  proj_core.get_stories_info()["file_type"], tm)] = "REMOVE"
        tc.scenario_name = (data_dict['name']).replace(" ", "")
        if tc.scenario_content is not None and tc.scenario_content != "":
            # modified content
            story_content = tc.scenario_content.replace(tc.name, data_dict['name'])
            proj_core.prepare_story_file(story_content, tc.scenario_name + str(tc_id)
                                         + proj_core.get_stories_info()["file_type"], tm, to_push)
        # save CI run
        proj_core.push_and_save_ci(to_push, "TEST CASE: NAME CHANGED")
    if 'users_assigned' in data_dict:
        user_arr = []
        if 'users_assigned' in data_dict:
            for u in data_dict['users_assigned']:
                user_arr.append(base_objects.User.dbs_model.query.get(u))
        tc.users_assigned = user_arr
    try:
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error updating test case info: " + str(e), consts.HTTP_500_INTERNAL_SERVER_ERROR
    tc_d = tc.to_dict()
    tc_d['id'] = str(tc.id)  # swagger json friendly
    tc_d['users_assigned'] = [u_a.id for u_a in tc.users_assigned]
    response = {"message": "Test case successfully updated in database and repository",
                "object": tc_d}
    return jsonify(response), consts.HTTP_200_OK


# -----------------------------------------------------------------------------------------------------

@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base + '/<tp_id>'
           + Testmodule.routing_base + '/<tm_id>' + Testcase.routing_base + '/<tc_id>', methods=['POST'])
def tc_add_test_steps(proj_id, tp_id, tm_id, tc_id):
    if request.headers['Content-Type'] == 'text/plain':
        if request.data is None:
            return "Invalid request data.", consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    try:
        dbs.session.begin()
        story_raw = request.data
        p = Project.dbs_model.query.get(proj_id)
        tp = Testplan.dbs_model.query.get(tp_id)
        tm = Testmodule.dbs_model.query.get(tm_id)
        tc = Testcase.dbs_model.query.get(tc_id)
        check_if_tp_in_proj(tp, p)
        if not tp:
            raise RuntimeError("Test plan does not exist.")
        check_if_tc_in_tmod(tc, tm)

        proj_core = core.CoreCreator().create_core(tp.project)

        to_push = {}  # basic data unit {"path to file":"file content",...}
        story_file_content, steps_raw = proj_core.parse_scenarios(story_raw)
        proj_core.init_repo()  # clone repo to tmp folder
        steps_json = steps_raw[0], proj_core.analyze_story_file(steps_raw[1], tc, tp)

        # remove all old steps from database (mandatory after analysis!)
        for s in tc.test_steps:
            dbs.session.delete(s)
        dbs.session.flush()
        try:
            for s in steps_json[1]:
                if s["operation"] == "create" or s["operation"] == "modify":
                    create_new_step_dbs(s, tc, tp)
                elif s["operation"] == "delete":
                    s["step_to_generate"] = False
                    continue
                else:
                    raise RuntimeError
        except RuntimeError as re:
            print(re)
            dbs.session.rollback()
            return str(re), consts.HTTP_404_NOT_FOUND
        except Exception as e:
            print("Problem while creating/modifying steps library.")
            print(e)
            dbs.session.rollback()
            return "Problem while creating/modifying steps library: " + str(e), consts.HTTP_500_INTERNAL_SERVER_ERROR

        try:
            for s in steps_json[1]:
                if s["operation"] == "create" or s["operation"] == "modify":
                    continue
                elif s["operation"] == "delete":
                    # find its definition in module
                    steps_based_on_def = Teststep.dbs_model.query\
                        .filter_by(test_step_definition_id=s["definition_id"]).all()
                    # check for type too, return steps for same definition with same type
                    if steps_based_on_def is None:  # step body is no longer used >> remove from modules
                        step_def = Teststepdefinition.dbs_model.query.get(s["definition_id"])
                        if step_def is None:  # step was already removed
                            continue
                        proj_core.delete_step_from_modules(tp, s["definition_id"], to_push)
                else:
                    raise RuntimeError
        except Exception as e:
            print("Problem while creating/modifying test case/steps library.")
            dbs.session.rollback()
            return "Problem while creating/modifying test case/steps library: " + str(e),\
                   consts.HTTP_500_INTERNAL_SERVER_ERROR

        proj_core.clean_test_step_definitions(to_push, tp)

        gen_code_info, clean_steps_json \
            = proj_core.analyze_steps_to_be_generated_in_repo_modules(steps_json, tp, to_push)
        proj_core.add_stepsfile_to_runnerfile(tm, to_push)

        # prepare story file
        old_story_filename = tc.scenario_name
        tc.scenario_name = steps_json[0].replace(" ", "")
        tc.name = steps_json[0]
        tc.scenario_content = story_file_content

        if old_story_filename is not None and old_story_filename != "":
            to_push[proj_core.get_story_file_path(old_story_filename + str(tc_id)
                                                  + proj_core.get_stories_info()["file_type"], tm)] = "REMOVE"
        proj_core.prepare_story_file(tc.scenario_content, tc.scenario_name + str(tc_id)
                                     + proj_core.get_stories_info()["file_type"], tm, to_push)

        # add new steps at the end + end classs
        steps_file_path = proj_core.get_generated_code_file_path(tm.id, tm.name_no_spaces)
        steps_file_content = proj_core.get_file_current_content(steps_file_path, to_push)
        proj_core.prepare_steps_file(steps_file_content, clean_steps_json, tm, tc, to_push)
        # save CI run
        proj_core.push_and_save_ci(to_push, "TEST CASE STEPS ADDED/MODIFIED")
        dbs.session.commit()
    except RuntimeError as re:
        print(re)
        traceback.print_exc()
        dbs.session.rollback()
        return str(re), consts.HTTP_400_BAD_REQUEST
    except Exception as e:
        print(e)
        traceback.print_exc()
        dbs.session.rollback()
        return str(e), consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Test case successfully modified, steps added in database and in project repository.",
                "object": tc.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


def create_new_step_dbs(s, tc, tp):
    # get gherkin type based on step type
    gtype = dbs.session.query(Gherkintype.dbs_model).filter(Gherkintype.dbs_model.name == s["type"]).first()
    # compare with step definition
    step_def = dbs.session.query(Teststepdefinition.dbs_model)\
        .filter(Teststepdefinition.dbs_model.content == s["definition_content"])\
        .filter((Teststepdefinition.dbs_model.project_id == tp.project_id)) \
        .filter(Teststepdefinition.dbs_model.gherkin_types.any(Gherkintype.dbs_model.name == s["type"])) \
        .first()
    if step_def is None:
        step_def = Teststepdefinition.dbs_model(content=s["definition_content"],
                                                param_count=len(s["parameters"]), project_id=tp.project_id)
        step_def.gherkin_types.append(gtype)
        dbs.session.add(step_def)
        dbs.session.flush()
    # print(step_def)
    step = Teststep.dbs_model(content=s["raw_content"], order=int(s["order"]))
    step.set_params(s["parameters"])
    step.test_case = tc
    step.test_step_definition = step_def
    s["definition_id"] = step_def.id
    s["step_to_generate"] = True
    # print(step)
    dbs.session.add(step)
    dbs.session.flush()
    tc.test_steps.append(step)
    s["step_id"] = step.id
    s["tc_id"] = step.test_case.id


@app.route(Project.routing_base + '/<proj_id>' + Teststepdefinition.routing_base, methods=['GET'])
def list_step_definitions(proj_id):
    try:
        dbs.session.begin()
        proj = Project.dbs_model.query.get(proj_id)
        if not proj:
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Project with id: " + str(proj_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        step_defs = dbs.session.query(Teststepdefinition.dbs_model)\
            .filter((Teststepdefinition.dbs_model.project_id == proj_id)).all()
        if not step_defs:
            raise RuntimeError("Step definitions for project NOT found.")
    except Exception as e:
        print(e)
        return "Problem while working with step definition library: " + str(e), consts.HTTP_404_NOT_FOUND
    response = {"message": "Project step definitions found.", "object": [step_d.to_dict() for step_d in step_defs]}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Teststepdefinition.routing_base + '/<def_id>' + Teststep.routing_base,
           methods=['GET'])
def list_step_definition_steps(proj_id, def_id):
    try:
        dbs.session.begin()
        proj = Project.dbs_model.query.get(proj_id)
        if not proj:
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Project with id: " + str(proj_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        step_def = Teststepdefinition.dbs_model.query.get(def_id)
        if int(step_def.project_id) != int(proj_id):
            raise RuntimeError("Step definition project does not match set project. Real project id of "
                               "your step definition: " + str(step_def.project_id) + ".")
        if not step_def or not step_def.test_steps:
            raise RuntimeError("Step definition or steps based on the step definition NOT found.")
    except Exception as e:
        print(e)
        return "Problem while working with step definition library: " + str(e), consts.HTTP_404_NOT_FOUND
    result = []
    for s in step_def.test_steps:
        result.append({"id": s.id, "content": s.content, "order": s.order, "in_test_case": s.test_case_id})
    response = {"message": "Steps using step definition found.",
                "object": result}
    return jsonify(response), consts.HTTP_200_OK
