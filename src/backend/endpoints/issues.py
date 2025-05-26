# TestBuDDy-Requirements-coverage
# FR-09, FR-10

import json
import traceback

from flask import request, jsonify

import core
from app import app, dbs
import consts
from base_objects import Bug, Project


# get bug
@app.route(Project.routing_base + '/<proj_id>' + Bug.routing_base + '/<bug_id>', methods=['GET'])
def get_bug(proj_id, bug_id):
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
        proj_core = core.CoreCreator().create_core(proj)
        proj_core.update_reports()
        proj_core.update_bugs()
        proj_core.update_bugs_from_issue_tracker()
        dbs.session.commit()
        bug = Bug.dbs_model.query.get(bug_id)
        if int(bug.project_id) != int(proj_id):
            return "Found bug does not belong to requested project with id: " + str(proj_id) + ".", \
                   consts.HTTP_404_NOT_FOUND
        if not bug:
            raise RuntimeError
    except Exception as e:
        print(e)
        return "Bug with id: " + str(bug_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    response = {"message": "Successfully found bug.", "object": bug.to_dict(1)}
    return jsonify(response), consts.HTTP_200_OK


# list all bugs (only related to current ci_runs)
@app.route(Project.routing_base + '/<proj_id>' + Bug.routing_base, methods=['GET'])
def list_bugs(proj_id):
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
        proj_core = core.CoreCreator().create_core(proj)
        proj_core.update_reports()
        proj_core.update_bugs()
        dbs.session.commit()
        print("Bugs successfully renewed based on saved reports from database.")
    except Exception as e:
        traceback.print_exc()
        print(e)
        dbs.session.rollback()
        return "Error accessing CI runs from server: " + str(e), consts.HTTP_500_INTERNAL_SERVER_ERROR
    try:
        bugs = dbs.session.query(Bug.dbs_model).filter(Bug.dbs_model.project_id == int(proj_id)).all()
        if not bugs:
            raise RuntimeError("Bugs NOT found for project with id: " + str(proj_id) + ".")
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return str(e), consts.HTTP_404_NOT_FOUND
    response = {"message": "Successfully found project bugs.", "object": [b.to_dict(0) for b in bugs]}
    return jsonify(response), consts.HTTP_200_OK


# bugs - with links and refresh bugs for project
@app.route(Project.routing_base + '/<proj_id>' + Bug.routing_base + '/<bug_id>', methods=['POST'])
def add_link_to_bug(proj_id, bug_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None:
            return "Invalid json data.", consts.HTTP_400_BAD_REQUEST
        if 'link' not in data_dict:
            return 'Insufficient json data, please provide issue tracker "link" for your bug.',\
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
        bug = Bug.dbs_model.query.get(bug_id)
        if not bug:
            raise RuntimeError("Bug with id: " + str(bug_id) + " NOT found.")
        bug.link = data_dict["link"]
        dbs.session.flush()
        proj_core = core.CoreCreator().create_core(proj)
        if not proj_core.check_if_issue_exists(bug):
            raise RuntimeError("Bug with id: " + str(bug.id) +
                               " - there was NO connected Issue found in your Issue tracker with bug link: " + bug.link)
        proj_core.update_bugs_from_issue_tracker()
        proj_core.send_data_to_issue_tracker_bug([bug])
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Problem while working with bug: " + str(e), consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Successfully added link to bug.", "object": bug.to_dict(1)}
    return jsonify(response), consts.HTTP_200_OK