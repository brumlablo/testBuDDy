# TestBuDDy-Requirements-coverage
# FR-09, FR-11, FR-12, FR-15

import json
import traceback
from flask import jsonify, request

import consts
from app import app, dbs
import core
from base_objects import CIRun, TriggerType, Project, ResultState


@app.route('/init-ci', methods=['POST'])
def init_ci():
    try:
        dbs.session.begin()
        TriggerType.create_tt()
        ResultState.create_rs()
        dbs.session.commit()
    except Exception as e:
        dbs.session.rollback()
        traceback.print_exc()
        print(e)
        return "Initialization problem: " + str(e), consts.HTTP_500_INTERNAL_SERVER_ERROR
    return "Initialization done.", consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + '/init_repo', methods=['POST'])
def init_project_repo(proj_id):
    try:
        proj = Project.dbs_model.query.get(proj_id)
        if not proj:
            raise RuntimeError
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Project with id: " + str(proj_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        dbs.session.begin()
        reinit_project_repo(proj)
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error preparing CI base: " + str(e), consts.HTTP_400_BAD_REQUEST
    return "Preparation of TestBuDDY CI part of your project repository done.", consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>/purge_repo', methods=['POST'])
def purge_project_repo(proj_id):
    try:
        proj = Project.dbs_model.query.get(proj_id)
        # for testing purposes
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Project with id: " + str(proj_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        dbs.session.begin()
        proj_core = core.CoreCreator().create_core(proj)
        proj_core.clean_repo_and_delete_project()
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error purging of TestBuDDy part of your project repository. " + str(e),\
               consts.HTTP_400_BAD_REQUEST
    return "Purging of TestBuDDy part of repository done. Project erased.", consts.HTTP_200_OK


def reinit_project_repo(proj):
    proj_core = core.CoreCreator().create_core(proj)
    proj_core.init_push()


@app.route(Project.routing_base + '/<proj_id>' + CIRun.routing_base + '/trigger_pipeline', methods=['POST'])
def trigger_pipeline(proj_id):
    try:
        proj = Project.dbs_model.query.get(proj_id)
        if not proj:
            raise RuntimeError
        # for testing purposes
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Project with id: " + str(proj_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        dbs.session.begin()
        proj_core = core.CoreCreator().create_core(proj)
        pipeline_id, commit_hash = proj_core.trigger_pipeline()
        if commit_hash and pipeline_id:
            proj_core.save_ci_run(commit_hash=commit_hash, pipeline_id=pipeline_id, trigger_type="triggered_run")
        dbs.session.commit()
        ci_run = dbs.session.query(CIRun.dbs_model)\
            .filter(CIRun.dbs_model.project_id == proj_id)\
            .filter(CIRun.dbs_model.data.like('%"pipeline_id": ' + str(pipeline_id) + ',%')).first()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error triggering pipeline for project: " + str(e), consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Pipeline with id: " + str(pipeline_id) + " successfully issued in CI and created CI Run.",
                "object": ci_run.to_dict(0)}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + CIRun.routing_base + '/sync', methods=['POST'])
def renew_ci_runs(proj_id):
    try:
        # connect to gitlab
        # get all pipelines for the project
        dbs.session.begin()
        proj = Project.dbs_model.query.get(proj_id)
        if not proj:
            raise RuntimeError("Project not found.")
    except Exception as e:
        print(e)
        traceback.print_exc()
        return "Project with id: " + str(proj_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        if not request.args:  # default: renew all
            args = {'pipelines': True, 'reports': True, 'bugs': True}
        else:
            args = request.args
        proj_core = core.CoreCreator().create_core(proj)
        if 'pipelines' in args:
            if bool(args['pipelines']):
                proj_core.update_ci_runs_with_pipelines()
        if 'reports' in args:
            if bool(args['reports']):
                proj_core.update_reports()
        if 'bugs' in args:
            if bool(args['bugs']):
                proj_core.update_bugs_from_issue_tracker()
                modified_bugs = proj_core.update_bugs()
                proj_core.send_data_to_issue_tracker_bug(modified_bugs)
        # update pipelines that are already in the system (saved with their id)
        dbs.session.commit()
        print("CI Runs requested data successfully renewed.")
    except Exception as e:
        traceback.print_exc()
        print(e)
        dbs.session.rollback()
        return "Error accessing CI runs from server: " + str(e), consts.HTTP_500_INTERNAL_SERVER_ERROR
    try:
        ci_runs = dbs.session.query(CIRun.dbs_model).filter(CIRun.dbs_model.project_id == proj_id).all()
        if not ci_runs:
            raise RuntimeError("CI Runs NOT found for project with id: " + str(proj_id) + ".")
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Problem while updating with CI Runs data: " + str(e), consts.HTTP_404_NOT_FOUND
    response = {"message": "Successfully updated project CI Runs. Updated CI Runs.",
                "object": [ci_r.to_dict(0) for ci_r in ci_runs]}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + CIRun.routing_base, methods=['GET'])
def list_ci_runs(proj_id):
    # first renew ci run database
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
        # proj_core.update_ci_runs_with_pipelines()
        results = dbs.session.query(CIRun.dbs_model).filter(CIRun.dbs_model.project_id == proj_id).all()
        if not results:
            raise RuntimeError("CI Runs for project NOT found.")
        proj_core.update_reports()
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Problem while working with CI Runs data: " + str(e), consts.HTTP_404_NOT_FOUND
    response = {"message": "Successfully found project CI Runs.", "object": [r.to_dict(0) for r in results]}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + CIRun.routing_base + '/<pipeline_id>', methods=['GET'])
def get_ci_run(proj_id, pipeline_id):
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
        ci_run = dbs.session.query(CIRun.dbs_model)\
            .filter(CIRun.dbs_model.project_id == proj_id)\
            .filter(CIRun.dbs_model.data.like('%"pipeline_id": ' + str(pipeline_id) + ',%')).first()
        # test runs need to be updated
        if not ci_run and ci_run.result_state.name not in ["failed", "success"]:
            proj_core = core.CoreCreator().create_core(proj)
            # first renew ci_run database
            proj_core.update_ci_runs_with_pipelines()
            ci_run = dbs.session.query(CIRun.dbs_model)\
                .filter(CIRun.dbs_model.project_id == proj_id)\
                .filter(CIRun.dbs_model.data.like('%"pipeline_id": ' + str(pipeline_id) + ',%')).first()
        if not ci_run:
            raise RuntimeError("CI Run for pipeline NOT found.")
        dbs.session.flush()
        dbs.session.commit()
    except Exception as e:
        dbs.session.rollback()
        return "Problem while working with CI Run data: " + str(e), consts.HTTP_404_NOT_FOUND
    response = {"message": "Successfully found CI Run.", "object": ci_run.to_dict(1)}
    return jsonify(response), consts.HTTP_200_OK
