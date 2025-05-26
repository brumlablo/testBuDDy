# TestBuDDy-Requirements-coverage
# FR-02, FR-08

import json
import os
import traceback

import core
from app import app, dbs
from flask import jsonify, request
import consts
from base_objects import Project


@app.route('/init-projects', methods=['POST'])
def init_projects():
    dbs.session.begin()
    try:
        count = int(dbs.session.query(Project.dbs_model).count())
        if count < 3:
            Project.create_projects()
        dbs.session.commit()
    except Exception as e:
        print(e)
        traceback.print_exc()
        dbs.session.rollback()
        return "Initialization problem: " + str(e), consts.HTTP_500_INTERNAL_SERVER_ERROR
    return "Initialization done.", consts.HTTP_200_OK


@app.route(Project.routing_base, methods=['GET'])
def list_projects():
    try:
        data = Project.dbs_model.query.all()
        if not data:
            raise RuntimeError
    except Exception as e:
        print(e)
        return "Projects NOT found.", consts.HTTP_404_NOT_FOUND
    response = {"message": "Projects successfully found.", "object": [proj.to_dict() for proj in data]}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>', methods=['GET'])
def get_project(proj_id):
    try:
        proj = Project.dbs_model.query.get(proj_id)
        if not proj:
            raise RuntimeError
    except Exception as e:
        print(e)
        return "Project with id: " + str(proj_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    response = {"message": "Project successfully found.", "object": proj.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base, methods=['POST'])
def create_project():
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None:
            return "Invalid json data.", consts.HTTP_400_BAD_REQUEST
        if ('name' not in data_dict or 'repo_url' not in data_dict or 'ci_params' not in data_dict
                or 'key' not in data_dict['ci_params']):
            return 'Insufficient json data, please provide "name" and "repo_url" and "ci_params" ' \
                   ' with "key" token for your repository.',\
                   consts.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE

    try:
        dbs.session.begin()
        # default values
        if 'ci_communicator' not in data_dict:
            data_dict['ci_communicator'] = "gitlab"
        if 'language_processor' not in data_dict:
            data_dict['language_processor'] = "java-jbehave"
        new_proj = Project.dbs_model(name=data_dict['name'], repo_url=data_dict['repo_url'],
                                     ci_communicator=data_dict["ci_communicator"],  # dict with params
                                     language_processor=data_dict["language_processor"])
        new_proj.set_ci_params(data_dict["ci_params"])  # expected token {"key": "repo token key"}
        if 'issue_tracker' in data_dict and 'issue_tracker_params' in data_dict:
            new_proj.issue_tracker = data_dict['issue_tracker']
            new_proj.set_issue_tracker_params(data_dict["issue_tracker_params"])

        dbs.session.add(new_proj)
        dbs.session.flush()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error while creating project, project was not created.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    try:
        proj_core = core.CoreCreator().create_core(new_proj)
        proj_core.init_repo()
        proj_core.init_push()
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error preparing CI base.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Successfully created and initialized project.", "object": new_proj.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>', methods=['DELETE'])
def delete_project(proj_id):
    try:
        dbs.session.begin()
        proj_todel = Project.dbs_model.query.get(proj_id)  # filter_by(id=id).first()
        if not proj_todel:
            raise RuntimeError
    except Exception as e:
        print(e)
        return "Project with id: " + str(proj_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        proj_core = core.CoreCreator().create_core(proj_todel)
        params = proj_core.project.get_ci_params()
        repo_url = params["server_url"] + params["server_base"] + params["proj_path"]
        delete_project_in_dbs = False
        if 'delete_project_in_dbs' in request.args:
            delete_project_in_dbs = bool(request.args.get('delete_project_in_dbs'), False)
        proj_core.clean_repo_and_delete_project(delete_project=delete_project_in_dbs)
        dbs.session.commit()
    except Exception as e:
        dbs.session.rollback()
        print(e)
        return "Error deleting project, project was not erased.\n", consts.HTTP_500_INTERNAL_SERVER_ERROR
    msg = "Successfully cleaned TestBuDDy part of repository: '" + repo_url + "'"
    if delete_project_in_dbs:
        msg += " and deleted project " + str(proj_id) + "in database"
    msg += ".\n"
    return msg, consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>', methods=['PUT'])
def project_update(proj_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None:
            return "Invalid json data.", consts.HTTP_400_BAD_REQUEST
        try:
            proj_to_upd = Project.dbs_model.query.get(proj_id)
            if not proj_to_upd:
                raise RuntimeError
        except Exception as e:
            print(e)
            return "Project with id: " + str(proj_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    try:
        dbs.session.begin()
        if 'name' in data_dict:
            proj_to_upd.name = data_dict['name']

        if 'language_processor' in data_dict:
            proj_to_upd.language_processor = data_dict['language_processor']

        if 'ci_params' in data_dict:
            old_ci_params = proj_to_upd.get_ci_params()
            if not old_ci_params:
                proj_to_upd.set_ci_params(data_dict['ci_params'].to_dict())
            else:
                for key, value in data_dict['ci_params'].items():
                    old_ci_params[key] = value
                proj_to_upd.set_ci_params(old_ci_params)
            dbs.session.flush()
            print("Please don't forget to reinitialize your TestBuDDy project remote repository too.")
        if 'issue_tracker' in data_dict:
            proj_to_upd.issue_tracker = data_dict['issue_tracker']
        if 'issue_tracker_params' in data_dict:
            old_issue_tracker_params = proj_to_upd.get_issue_tracker_params()
            if not old_issue_tracker_params:
                proj_to_upd.set_issue_tracker_params(data_dict['issue_tracker_params'])
            else:
                for key, value in data_dict['issue_tracker_params'].items():
                    old_issue_tracker_params[key] = value
                proj_to_upd.set_issue_tracker_params(old_issue_tracker_params)
            dbs.session.flush()
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error updating project. Project was not updated.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Successfully updated project.", "object": proj_to_upd.to_dict()}
    return jsonify(response), consts.HTTP_200_OK
