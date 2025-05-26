# TestBuDDy-Requirements-coverage
# FR-03, FR-04, FR-05

import os
import traceback

import MySQLdb
import sqlalchemy

import base_objects
import core
from app import app
from app import dbs
from flask import jsonify
from flask import request
import consts

from base_objects import TCPriority, Testcase, Testplan, Testmodule, Project, Gherkintype, Teststepdefinition


@app.route('/init-testlibrary', methods=['POST'])
def init_testlibrary():
    dbs.session.begin()
    try:
        TCPriority.create_priorities()
        Testplan.create_testplans()  # how much I want in total
        Testmodule.create_testmodules()
        Testcase.create_testcases()
        Gherkintype.create_gherkintypes()
        dbs.session.commit()
    except Exception as e:
        dbs.session.rollback()
        traceback.print_exc()
        print(e)
        return "Initialization problem: " + str(e), consts.HTTP_500_INTERNAL_SERVER_ERROR
    return "Initialization done.", consts.HTTP_200_OK


@app.route(Project.routing_base + Testplan.routing_base, methods=['GET'])
def list_tps():
    try:
        dbs.session.begin()
        tps = Testplan.dbs_model.query.all()
        if not tps:
            return "Test plans NOT found.", consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "Test plans NOT found.", consts.HTTP_404_NOT_FOUND
    result = []
    for tp in tps:
        result.append(tp.to_dict())
    response = {"message": "Successfully found all test plans.", "object": result}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base, methods=['GET'])
def list_proj_tp(proj_id):
    try:
        dbs.session.begin()
        testplans = Testplan.dbs_model.query.filter_by(project_id=proj_id).all()
        if not testplans:
            return "Test plan for project with id: " + str(proj_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "Test plan for project with id: " + str(proj_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    result = []
    for tp in testplans:
        result.append(tp.to_dict())
    response = {"message": "Successfully found test plan(s) for project.", "object": result}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base + '/<tp_id>', methods=['GET'])
def get_tp(proj_id, tp_id):
    try:
        # check if data are correct
        proj = Project.dbs_model.query.get(int(proj_id))
        tp = Testplan.dbs_model.query.get(int(tp_id))
        check_if_tp_in_proj(tp, proj)
    except RuntimeError as re:
        print(re)
        return str(re), consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "Test plan with id: " + str(tp_id) + " or project with id:" + str(proj_id) + " NOT found.", \
               consts.HTTP_404_NOT_FOUND
    response = {"message": "Successfully found test plan for project.", "object": tp.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base, methods=['POST'])
def create_tp(proj_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None or 'name' not in data_dict:
            return "Invalid json data, please provide at least 'name' parameter.", consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    try:
        dbs.session.begin()
        proj = base_objects.Project.dbs_model.query.get(int(proj_id))
        if not proj:
            raise RuntimeError("Project NOT found.")
        descr = ""
        if 'description' in data_dict:
            descr = data_dict['description']
        new_tp = Testplan.dbs_model(name=data_dict['name'], description=descr, project_id=proj.id)
        new_tp.project = proj
        dbs.session.add(new_tp)
        dbs.session.commit()
    except (MySQLdb.Error, MySQLdb.Warning, sqlalchemy.except_.OperationalError) as e:
        dbs.session.rollback()
        print(e)
        traceback.print_exc()
        return "Project has already a test plan.", consts.HTTP_400_BAD_REQUEST
    except Exception as e:
        print(e)
        traceback.print_exc()
        dbs.session.rollback()
        return "Test plan could NOT be created: " + str(e), consts.HTTP_404_NOT_FOUND
    response = {"message": "Successfully created test plan.", "object": new_tp.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


# @app.route(Testplan.routing_base + '/<tp_id>', methods=['DELETE'])
# def delete_tp(tp_id):
#     try:
#         dbs.session.begin()
#         tp_todel = Testplan.dbs_model.query.get(tp_id)  # filter_by(id=id).first()
#         dbs.session.delete(tp_todel)
#         dbs.session.commit()
#     except Exception as e:
#         print(e)
#         dbs.session.rollback()
#         return "Test plan with id: " + str(tp_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
#     return "Successfully deleted test plan with id: " + str(tp_id) + ".\n", consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base + '/<tp_id>', methods=['PUT'])
def update_tp(proj_id, tp_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None:
            return "Invalid json data, please provide at least new 'name' or 'description'.",\
                   consts.HTTP_400_BAD_REQUEST
        try:
            dbs.session.begin()
            tp_to_upd = Testplan.dbs_model.query.get(int(tp_id))
            # check if data are correct
            proj = Project.dbs_model.query.get(int(proj_id))
            check_if_tp_in_proj(tp_to_upd, proj)
        except RuntimeError as re:
            print(re)
            return str(re), consts.HTTP_404_NOT_FOUND
        except Exception as e:
            print(e)
            return "Test plan with id: " + str(tp_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE

    if 'description' in data_dict and data_dict['description'] != "":
        tp_to_upd.description = data_dict['description']
    if 'name' in data_dict and (data_dict['name']).replace(" ", "") != "":
        tp_to_upd.name = data_dict['name']
    try:
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error while working with test plan. Test plan could not be updated.", \
               consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Successfully updated test plan.", "object": tp_to_upd.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


# ----------------------------------------------------------------------------------- #
def check_if_tp_in_proj(tp, proj):
    if not(tp and proj):
        raise RuntimeError("Test plan or project NOT found.")
    if int(proj.test_plan.id) != int(tp.id):
        raise RuntimeError("Project test plan with id: " + str(proj.test_plan.id) +
                           " does not adhere to requested test plan with id: " + str(tp.id) + ".\n")


def check_if_tmod_in_tp(tmod, tp):
    if not (tmod and tp):
        raise RuntimeError("Test module or test plan NOT found.")
    if tmod not in tp.test_modules:
        raise RuntimeError("Test module with id: " + str(tmod.id) + " NOT found within test plan with id: "
                           + str(tp.id) + ".")


@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base + '/<tp_id>'
           + Testmodule.routing_base, methods=['POST'])
def create_tp_module(proj_id, tp_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None or 'name' not in data_dict:
            return "Invalid json data, please provide 'name' parameter.", consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    try:
        dbs.session.begin()
        tp = Testplan.dbs_model.query.get(int(tp_id))
        p = Project.dbs_model.query.get(int(proj_id))
        check_if_tp_in_proj(tp, p)
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Test module could NOT be created: " + str(e), consts.HTTP_404_NOT_FOUND
    try:
        if (data_dict['name']).replace(" ", "") == "":
            raise RuntimeError("Empty 'name' parameter")
        tmod = Testmodule.dbs_model(name=data_dict['name'], name_no_spaces=(data_dict['name']).replace(" ", ""))
        tp.test_modules.append(tmod)
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Test module could NOT be created: " + str(e), consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Successfully created test module.", "object": tmod.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


# ? assign existing test module to test plan - NOT NEEDED, as we create modules for test plans directly

@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base + '/<tp_id>' + Testmodule.routing_base
           + '/<tm_id>', methods=['DELETE'])
def delete_tp_module(proj_id, tp_id, tm_id):
    try:
        tp = Testplan.dbs_model.query.get(tp_id)
        tm = Testmodule.dbs_model.query.get(tm_id)
        p = Project.dbs_model.query.get(proj_id)
        check_if_tp_in_proj(tp, p)
        check_if_tmod_in_tp(tm, tp)
    except RuntimeError as re:
        print(re)
        return str(re), consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "Project, test plan with id: " + str(tp_id) + " or test module with id: " + str(
            tm_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        dbs.session.begin()
        tm_info = tm.to_dict()  # save module info
        dbs.session.delete(tm)
        dbs.session.flush()

        proj_core = core.CoreCreator().create_core(tp.project)
        to_push = {}
        proj_core.init_repo()

        # repository changes needed
        if tm.name_no_spaces is not None and tm.name_no_spaces != "":
            mod = proj_core.get_module_formatted_info(tm_info["name_no_spaces"], tm_info["id"])
            # clean against unused step definitions
            proj_core.clean_test_step_definitions(to_push, tp)
            # move remaining definitions to some other module file
            step_defs = dbs.session.query(Teststepdefinition.dbs_model)\
                .filter(Teststepdefinition.dbs_model.project_id == tp.project_id).all()
            mod_full_path = os.path.join(proj_core.tmp_file, mod["proj_path"])
            if os.path.isfile(mod_full_path):
                copied_steps = ""
                for step_d in step_defs:
                    # generated code file - replace
                    mod_file_content = proj_core.get_file_current_content(mod["proj_path"], to_push)

                    step_comment_string = mod["step_comment"].format(STEP_DEF_ID=str(step_d.id))
                    if step_comment_string in mod_file_content:
                        # find it and copy it to other module
                        start_index = mod_file_content.find(step_comment_string)  # header - start index
                        end_index = mod_file_content.find(step_comment_string, start_index + 1)  # footer - end index
                        if end_index == -1:  # step definition is broken
                            print("Comment footer '" + step_comment_string + "' NOT found in module: "
                                  + mod["proj_path"] + ". Skipping step definition: " + str(step_d.id) + ".")
                        copied_steps += mod_file_content[start_index:end_index + len(step_comment_string)] + "\n"

                gen_code_info = proj_core.get_generated_code_info()
                other_mods = dbs.session.query(Testmodule.dbs_model)\
                    .filter(Testmodule.dbs_model.test_plan_id == tp.id).all()
                mod_found = False
                for m in other_mods:
                    m_form = proj_core.get_module_formatted_info(m.name_no_spaces, str(m.id))
                    mod_full_path = os.path.join(proj_core.tmp_file, m_form["proj_path"])
                    if os.path.isfile(mod_full_path):
                        mod_found = True
                        m_content = proj_core.get_file_current_content(m_form["proj_path"], to_push)
                        closing_bracket_index = m_content.rfind(gen_code_info["class_end"])
                        new_content = m_content[:closing_bracket_index] + copied_steps + gen_code_info["class_end"]
                        to_push[m_form["proj_path"]] = new_content
                        proj_core.add_stepsfile_to_runnerfile(m, to_push)
                        break
                to_push[mod["proj_path"]] = "REMOVE"
                if not mod_found:
                    print("No other module generated code files were found. Deleted module steps and definitions"
                          " were erased.")

            # remove from runner file
            runner_file_info = proj_core.get_runner_file_info()
            to_find = runner_file_info["add_module"].format(TEST_MODULE_NAME=tm_info["name_no_spaces"],
                                                            TEST_MODULE_ID=tm_info["id"])
            proj_core.replace_in_runner(runner_file_info, to_find, "", to_push)
            # retry - if some whitespaces erased
            proj_core.replace_in_runner(runner_file_info, to_find.strip(), "", to_push)

            # remove stories
            proj_core.modify_or_erase_module_story_files(mod["module_steps_base_name"], "", to_push)

        dbs.session.commit()
        proj_core.push_and_save_ci(to_push, "TEST MODULE: REMOVED")
    except Exception as e:
        print(e)
        traceback.print_exc()
        dbs.session.rollback()
        return "Test plan with id: " + str(tp_id) + " or test module with id: " + str(
            tm_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    return "Successfully deleted test module with id: " + str(tm_id) + ".\n", consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base + '/<tp_id>'
           + Testmodule.routing_base + '/<tm_id>', methods=['PUT'])
def update_tp_module(proj_id, tp_id, tm_id):
    if request.headers['Content-Type'] != 'application/json':
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    data_dict = request.get_json()
    if data_dict is None:
        return "Invalid json data.", consts.HTTP_400_BAD_REQUEST
    if 'name' not in data_dict or (data_dict["name"]).replace(" ", "") == "":
        return "Missing 'name' argument to modify test module.", consts.HTTP_400_BAD_REQUEST
    try:
        tp = Testplan.dbs_model.query.get(tp_id)
        tm = Testmodule.dbs_model.query.get(tm_id)
        p = Project.dbs_model.query.get(proj_id)
        check_if_tp_in_proj(tp, p)
        check_if_tmod_in_tp(tm, tp)
    except RuntimeError as re:
        print(re)
        return str(re), consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "Project or test plan with id: " + str(tp_id) + " or test module with id: " + str(
            tm_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        dbs.session.begin()
        old_name_no_spaces = tm.name_no_spaces

        proj_core = core.CoreCreator().create_core(tp.project)
        to_push = {}
        proj_core.init_repo()

        tm.name = data_dict['name']
        tm.name_no_spaces = data_dict['name'].replace(" ", "")
        dbs.session.flush()

        # repository changes needed
        if tm.name_no_spaces is not None and tm.name_no_spaces != "":
            # rename steps file and rename its class name

            # prepare needed info
            old_mod = proj_core.get_module_formatted_info(old_name_no_spaces, tm.id)
            new_mod = proj_core.get_module_formatted_info(tm.name_no_spaces, tm.id)

            # generated code file - replace
            if os.path.isfile(os.path.join(proj_core.tmp_file, old_mod["proj_path"])):
                old_mod_file_content = proj_core.get_file_current_content(old_mod["proj_path"], to_push)
                to_push[old_mod["proj_path"]] = "REMOVE"

                # class name
                old_mod_file_content = old_mod_file_content.replace(old_mod["class"], new_mod["class"])
                # class header in comment
                old_mod_file_content = old_mod_file_content\
                    .replace(old_mod["module_steps_base_name"], new_mod["module_steps_base_name"])
                to_push[new_mod["proj_path"]] = old_mod_file_content

            # runner file - replace
            runner_file_info = proj_core.get_runner_file_info()
            proj_core.replace_in_runner(runner_file_info, old_mod["class"], new_mod["class"], to_push)

            # modify stories folder
            proj_core.modify_or_erase_module_story_files(old_mod["module_steps_base_name"],
                                                         new_mod["module_steps_base_name"], to_push)
            proj_core.push_and_save_ci(to_push, "TEST MODULE: RENAMING")
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Internal server error. Test plan was NOT updated.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Successfully updated test plan.", "object": tm.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base + '/<tp_id>'
           + Testmodule.routing_base + '/<tm_id>', methods=['GET'])
def get_tp_module(proj_id, tp_id, tm_id):
    try:
        tp = Testplan.dbs_model.query.get(tp_id)
        tm = Testmodule.dbs_model.query.get(tm_id)
        p = Project.dbs_model.query.get(proj_id)
        check_if_tp_in_proj(tp, p)
        check_if_tmod_in_tp(tm, tp)
    except RuntimeError as re:
        print(re)
        return str(re), consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "Test plan with id: " + str(tp_id) + " or test module with id: " + str(
            tm_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    response = {"message": "Successfully found test module.", "object": tm.to_dict()}
    return jsonify(response), consts.HTTP_200_OK
