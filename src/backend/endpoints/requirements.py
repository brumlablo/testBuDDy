# TestBuDDy-Requirements-coverage
# FR-16, FR-17

import json
import traceback

from flask import request, jsonify

import consts
from app import app, dbs
from base_objects import Requirement, Tag, Project, Testcase, Testplan, Testmodule
from endpoints.test_specification_case_step import check_if_tc_in_tmod
from endpoints.test_specification_plan_module import check_if_tmod_in_tp, check_if_tp_in_proj


@app.route('/init-requirements', methods=['POST'])
def init_requirements():
    try:
        dbs.session.begin()
        Requirement.create_requirements()
        dbs.session.commit()
    except Exception as e:
        dbs.session.rollback()
        traceback.print_exc()
        print(e)
        return "Initialization problem: " + str(e), consts.HTTP_500_INTERNAL_SERVER_ERROR
    return "Initialization done.", consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Tag.routing_base + '/<tag_id>', methods=['GET'])
def get_tag(proj_id, tag_id):
    try:
        proj = Project.dbs_model.query.get(proj_id)
        if not proj:
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Project with id: " + str(proj_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        tag = Tag.dbs_model.query.get(tag_id)
        if not tag or int(tag.project_id) != int(proj.id):
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Tag with id: " + str(tag_id) + " NOT found or does not belong to requested project.",\
               consts.HTTP_404_NOT_FOUND
    response = {"message": "Tag successfully found.",
                "object": tag.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Tag.routing_base, methods=['GET'])
def list_proj_tags(proj_id):
    try:
        proj = Project.dbs_model.query.get(proj_id)
        if not proj:
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Project with id: " + str(proj_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        if not proj.tags:
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Project tags NOT found.", consts.HTTP_404_NOT_FOUND
    response = {"message": "Tags successfully found.",
                "object": [t.to_dict() for t in proj.tags]}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Tag.routing_base, methods=['POST'])
def create_tag(proj_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None and 'content' not in data_dict and 'category' not in data_dict:
            return "Invalid json data. Please provide 'content' and 'category'.", consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
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
        tag = Tag.dbs_model(content=data_dict['content'], category=data_dict['category'], project_id=proj.id)
        dbs.session.add(tag)
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        traceback.print_exc()
        return "Tag could NOT be created.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Tag successfully created.",
                "object": tag.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Tag.routing_base + '/<tag_id>', methods=['DELETE'])
def delete_tag(proj_id, tag_id):
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
        tag = Tag.dbs_model.query.get(tag_id)
        if not tag or int(tag.project_id) != int(proj.id):
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Tag with id: " + str(tag_id) + " NOT found or does not belong to requested project.", \
               consts.HTTP_404_NOT_FOUND
    try:
        dbs.session.delete(tag)
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        traceback.print_exc()
        return "Tag could NOT be erased.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    return "Successfully removed tag with id: " + str(tag_id), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Tag.routing_base + '/<tag_id>', methods=['PUT'])
def modify_tag(proj_id, tag_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None:
            return "Invalid json data. Please provide correct 'content' or 'category'.", consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
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
        tag = Tag.dbs_model.query.get(tag_id)
        if not tag or int(tag.project_id) != int(proj.id):
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Tag with id: " + str(tag_id) + " NOT found or does not belong to requested project.", \
               consts.HTTP_404_NOT_FOUND
    try:
        if 'content' in data_dict:
            tag.content = data_dict['content']
        if 'category' in data_dict:
            tag.category = data_dict['category']
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        traceback.print_exc()
        return "Tag could NOT be modified.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Tag successfully modified.",
                "object": tag.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Requirement.routing_base, methods=['GET'])
def list_proj_requirements(proj_id):
    try:
        proj = Project.dbs_model.query.get(proj_id)
        if not proj:
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Project with id: " + str(proj_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        if not proj.requirements:
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Project requirements NOT found.", consts.HTTP_404_NOT_FOUND
    response = {"message": "Project requirements successfully found.",
                "object": [r.to_dict(0) for r in proj.requirements]}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Requirement.routing_base + '/<req_id>', methods=['GET'])
def get_requirement(proj_id, req_id):
    try:
        proj = Project.dbs_model.query.get(proj_id)
        if not proj:
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Project with id: " + str(proj_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        req = Requirement.dbs_model.query.get(req_id)
        if not req or int(req.project_id) != int(proj.id):
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Requirement with id: " + str(req_id) + " NOT found or does not belong to requested project.",\
               consts.HTTP_404_NOT_FOUND
    response = {"message": "Requirement successfully found.",
                "object": req.to_dict(2)}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Requirement.routing_base, methods=['POST'])
def create_requirement(proj_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None and 'content' not in data_dict:
            return "Invalid json data. Please provide 'content'.", consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
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
        req = Requirement.dbs_model(content=data_dict['content'], project_id=proj.id)
        dbs.session.add(req)
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        traceback.print_exc()
        return "Requirement could NOT be created.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Requirement successfully created.",
                "object": req.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Requirement.routing_base + '/<req_id>', methods=['DELETE'])
def delete_requirement(proj_id, req_id):
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
        req = Requirement.dbs_model.query.get(req_id)
        if not req or int(req.project_id) != int(proj.id):
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Requirement with id: " + str(req_id) + " NOT found or does not belong to requested project.", \
               consts.HTTP_404_NOT_FOUND
    try:
        dbs.session.delete(req)
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        traceback.print_exc()
        return "Requirement could NOT be erased.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    return "Successfully removed requirement with id: " + str(req_id), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Requirement.routing_base + '/<req_id>', methods=['PUT'])
def modify_requirement(proj_id, req_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None and 'content' not in data_dict:
            return "Invalid json data, please provide 'content' to modify requirement info.",\
                   consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
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
        req = Requirement.dbs_model.query.get(req_id)
        if not req or int(req.project_id) != int(proj.id):
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Requirement with id: " + str(req_id) + " NOT found or does not belong to requested project.", \
               consts.HTTP_404_NOT_FOUND
    try:
        if 'content' in data_dict:
            req.content = data_dict['content']
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        traceback.print_exc()
        return "Requirement could NOT be modified.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Requirement successfully modified.",
                "object": req.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Requirement.routing_base + '/<req_id>' + '/assign-tag',
           methods=['POST'])
def requirement_add_tag(proj_id, req_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None and 'tag_id' not in data_dict:
            return "Invalid json data, please provide 'tag_id' to add tag to requirement.",\
                   consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
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
        req = Requirement.dbs_model.query.get(req_id)
        if not req or int(req.project_id) != int(proj.id):
            raise RuntimeError("Requirement NOT found or does not belong to requested project.")
        tag = Tag.dbs_model.query.get(data_dict['tag_id'])
        if not tag or int(tag.project_id) != int(proj.id):
            raise RuntimeError("Tag NOT found or does not belong to requested project.")
        if tag not in req.tags:
            req.tags.append(tag)
        dbs.session.commit()
    except Exception as e:
        print(e)
        traceback.print_exc()
        dbs.session.rollback()
        return "Error while assigning tag: " + str(e), consts.HTTP_404_NOT_FOUND
    response = {"message": "Requirement successfully tagged.",
                "object": req.to_dict(2)}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Requirement.routing_base + '/<req_id>' + '/assign-tag',
           methods=['DELETE'])
def requirement_remove_tag(proj_id, req_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None and 'tag_id' not in data_dict:
            return "Invalid json data, please provide 'tag_id' to add tag to requirement.",\
                   consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
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
        req = Requirement.dbs_model.query.get(req_id)
        if not req or int(req.project_id) != int(proj.id):
            raise RuntimeError("Requirement NOT found or does not belong to requested project.")
        tag = Tag.dbs_model.query.get(data_dict['tag_id'])
        if not tag or int(tag.project_id) != int(proj.id):
            raise RuntimeError("Tag NOT found or does not belong to requested project.")
        if tag not in req.tags:
            raise RuntimeError("Assigned tag NOT found.")
        req.tags.remove(tag)
        dbs.session.commit()
    except Exception as e:
        print(e)
        traceback.print_exc()
        dbs.session.rollback()
        return "Error while removing assigned tag: " + str(e), consts.HTTP_404_NOT_FOUND
    response = {"message": "Assigned tag for requirement successfully removed.",
                "object": req.to_dict(2)}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base + '/<tp_id>'
           + Testmodule.routing_base + '/<tm_id>' + Testcase.routing_base + '/<tc_id>'
           + Requirement.routing_base, methods=['GET'])
def list_tc_requirements(proj_id, tp_id, tm_id, tc_id):
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
    try:
        if not tc.requirements:
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Test case requirements for requested test case NOT found.", consts.HTTP_404_NOT_FOUND
    response = {"message": "Test case requirements found.",
                "object": [r.to_dict(0) for r in tc.requirements]}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + Testplan.routing_base + '/<tp_id>'
           + Testmodule.routing_base + '/<tm_id>' + Testcase.routing_base + '/<tc_id>'
           + Requirement.routing_base + '/assign-requirement', methods=['POST'])
def add_tc_requirement(proj_id, tp_id, tm_id, tc_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None and 'requirement_id' not in data_dict:
            return "Invalid json data, please provide 'requirement_id' to add requirement to test case.",\
                   consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
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
    try:
        req = Requirement.dbs_model.query.get(data_dict['requirement_id'])
        if not req or int(req.project_id) != int(tp.project_id):
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Requirement with id: " + str(data_dict['requirement_id']) + \
               " NOT found or does not belong to requested test plan project.", consts.HTTP_404_NOT_FOUND
    try:
        if req not in tc.requirements:
            tc.requirements.append(req)
            dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        traceback.print_exc()
        return "Requirement could NOT be assigned to test case.", consts.HTTP_404_NOT_FOUND
    response = {"message": "Test case requirements found.",
                "object": [r.to_dict(0) for r in tc.requirements]}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' +
           Testplan.routing_base + '/<tp_id>' + Testmodule.routing_base + '/<tm_id>'
           + Testcase.routing_base + '/<tc_id>' + Requirement.routing_base + '/assign-requirement', methods=['DELETE'])
def remove_tc_requirement(proj_id, tp_id, tm_id, tc_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None and 'requirement_id' not in data_dict:
            return "Invalid json data, please provide 'requirement_id' to remove requirement from test case.",\
                   consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
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
    try:
        req = Requirement.dbs_model.query.get(data_dict['requirement_id'])
        if not req or req.project_id != int(tp.project_id):
            raise RuntimeError
        if tc not in req.test_cases:
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Requirement with id: " + str(data_dict['requirement_id']) + \
               " NOT found or does not belong to requested test plan project or test case.", consts.HTTP_404_NOT_FOUND
    try:
        tc.requirements.remove(req)
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        traceback.print_exc()
        return "Requirement could NOT be removed from test case.", consts.HTTP_404_NOT_FOUND
    response = {"message": "Test case assigned requirement successfully removed. Result test case requirements found.",
                "object": [r.to_dict(0) for r in tc.requirements]}
    return jsonify(response), consts.HTTP_200_OK