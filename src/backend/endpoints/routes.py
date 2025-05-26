# TestBuDDy-Requirements-coverage
# NFR-03
from flask import jsonify

from app import app, dbs
from endpoints import projects, test_specification_plan_module, test_specification_case_step, users, test_execution, \
     reports, requirements, issues
import consts


@app.route('/init-data', methods=['POST'])
def init_data():
    to_call = [users.init_users, projects.init_projects, test_specification_plan_module.init_testlibrary,
               requirements.init_requirements, test_execution.init_ci]
    categories_to_call = ["Users", "Projects", "Test library", "Requirements", "CI support"]
    full_response = ""
    for cat, init_method in zip(categories_to_call, to_call):
        response, code = init_method()
        full_response += cat + " - " + response + "\n"
        if code != consts.HTTP_200_OK:
            return full_response + " >> Please call '/clean-data' and '/init-data' to reinitialize all data.", code
    return full_response + " >> All data initialization done.", consts.HTTP_200_OK


@app.route('/clean-data', methods=['POST'])
def clean_data():
    try:
        dbs.session.begin()
        meta = dbs.metadata
        for table in reversed(meta.sorted_tables):
            print("Clear table: " + str(table))
            dbs.session.execute(table.delete())
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error removing tables: " + str(e), consts.HTTP_500_INTERNAL_SERVER_ERROR
    return "All tables erased.", consts.HTTP_200_OK