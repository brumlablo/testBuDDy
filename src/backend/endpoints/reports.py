# TestBuDDy-Requirements-coverage
# FR-11, FR-15

import json
import traceback

from flask import jsonify

import consts
import core
from app import app, dbs
from base_objects import Report, Project, CIRun


@app.route(Project.routing_base + '/<proj_id>' + CIRun.routing_base + '/<pipeline_id>'
           + Report.routing_base, methods=['GET'])
def print_ci_report(proj_id, pipeline_id):
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
        dbs.session.commit()
        ci_run = dbs.session.query(CIRun.dbs_model)\
            .filter(CIRun.dbs_model.project_id == proj_id)\
            .filter(CIRun.dbs_model.data.like('%"pipeline_id": ' + str(pipeline_id) + ',%')).first()
        if not ci_run:
            raise RuntimeError("CI Run for pipeline: " + str(pipeline_id) + " NOT found.")
        if ci_run.report is None:
            raise RuntimeError("Report for requested pipeline NOT found.")
    except Exception as e:
        dbs.session.rollback()
        return "Problem while working with CI Run data: " + str(e), consts.HTTP_404_NOT_FOUND
    response = {"message": "Successfully found report.", "object": ci_run.report.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


@app.route(Project.routing_base + '/<proj_id>' + CIRun.routing_base + Report.routing_base, methods=['GET'])
def print_proj_reports(proj_id):
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
        proj_core.update_ci_runs_with_pipelines()
        proj_core.update_reports()
        dbs.session.commit()
        ci_runs = dbs.session.query(CIRun.dbs_model)\
            .filter(CIRun.dbs_model.project_id == proj_id)\
            .filter(CIRun.dbs_model.report != None).all()
        if not ci_runs:
            raise RuntimeError("Reports for requested project NOT found.")
    except Exception as e:
        dbs.session.rollback()
        return "Problem while working with reports data: " + str(e), consts.HTTP_404_NOT_FOUND
    response = {"message": "Successfully found reports.", "object": [(ci_r.report).to_dict() for ci_r in ci_runs]}
    return jsonify(response), consts.HTTP_200_OK