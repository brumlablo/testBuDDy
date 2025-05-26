# Unittests for each endpoint
import json
import os
from pprint import pprint

import requests
root_url = "http://backend:5000"
req_counter = 0

M_POST = "POST   http://localhost:5000"
M_DEL =  "DELETE http://localhost:5000"
M_PUT =  "PUT    http://localhost:5000"
M_GET =  "GET    http://localhost:5000"


print("-----------------------------------TESTBUDDY---TESTS-----------------------------------")
print("------------------------------------Demo endpoints-------------------------------------")
init_endpoints = [
    {
        "endpoint": "",
        "method": requests.get,
        "to_print": M_GET,
        "additionals": {
        }
    },
    {
        "endpoint": "/init-ci",
        "method": requests.post,
        "to_print": M_POST,
        "additionals": {
        }
    },
    {
        "endpoint": "/init-projects",
        "method": requests.post,
        "to_print": M_POST,
        "additionals": {
        }
    },
    {
        "endpoint": "/init-requirements",
        "method": requests.post,
        "to_print": M_POST,
        "additionals": {
        }
    },
    {
        "endpoint": "/init-testlibrary",
        "method": requests.post,
        "to_print": M_POST,
        "additionals": {
        }
    },
    {
        "endpoint": "/clean-data",
        "method": requests.post,
        "to_print": M_POST,
        "additionals": {
        }
    },
    {
        "endpoint": "/init-data",
        "method": requests.post,
        "to_print": M_POST,
        "additionals": {
        }
    }
]

for test_req in init_endpoints:
    print(test_req["to_print"] + test_req["endpoint"])
    r = test_req["method"](root_url + test_req["endpoint"], **test_req["additionals"])
    assert r.status_code == 200
    print(r.content)

print("-----------------------------------Project managmenent-----------------------------------")

proj_endpoints = [
    {
        "endpoint": "/projects",
        "method": requests.get,
        "to_print": M_GET,
        "additionals": {
        }
    },
    {
        "endpoint": "/projects",
        "method": requests.post,
        "to_print": M_POST,
        "additionals": {
            "json": {
                        "name": "test_proj",
                        "repo_url": "https://pajda.fit.vutbr.cz/xblozo00/testing_repo",
                        "language_processor": "java-jbehave",
                        "ci_communicator": "gitlab",
                        "ci_params": {
                        "key": os.getenv('CI_TOKEN')
                        }
                     }
        }
    },
    {
        "endpoint": "/projects/<{PROJ_ID}>",
        "method": requests.get,
        "to_print": M_GET,
        "additionals": {
        }
    },
    {
        "endpoint": "/projects/<{PROJ_ID}>",
        "method": requests.put,
        "to_print": M_PUT,
        "additionals": {
                        "json": {"name": "something new"}
        }
    },
    {
        "endpoint": "/projects/<{PROJ_ID}>",
        "method": requests.delete,
        "to_print": M_DEL,
        "additionals": {
        }
    }
]


id = {"proj": 0, "tplan": 0, "tmod": 0, "tcase": 0, "stepdef": 0, "pipeline": 0, "bug": 0, "req": 0, "tag": 0,
       "user": 0, "role": 0}


# get created project id
tmp_e = proj_endpoints[1]
print(tmp_e["to_print"] + tmp_e["endpoint"])
r = tmp_e["method"](root_url + tmp_e["endpoint"], **tmp_e["additionals"])
print(r.content)
assert r.status_code == 200

new_p = (json.loads(r.content))['object']
id["proj"] = int(new_p['id'])
print("created proj id: " + str(id["proj"]))

for test_req in proj_endpoints[2:]:
    print(test_req["to_print"] + test_req["endpoint"])
    r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"])), **test_req["additionals"])
    assert r.status_code == 200
    print(r.content)

# get project id and test plan id
tmp_e = proj_endpoints[0]
print(tmp_e["to_print"] + tmp_e["endpoint"])
r = tmp_e["method"](root_url + tmp_e["endpoint"], **tmp_e["additionals"])
assert r.status_code == 200

projects = (json.loads(r.content))['object']
for p in projects:
    id["proj"] = int(p['id'])
    id["tplan"]  = p['testplan']['id']
    break

print("-----------------------------------Test run managmenent-----------------------------------")


testrun_endpoints = [
    {
        "endpoint": "/projects",
        "method": requests.get,
        "to_print": M_GET,
        "additionals": {
        }
    },
    {
        "endpoint": "/projects/<{PROJ_ID}>/purge_repo",
        "method": requests.post,
        "to_print": M_POST,
        "additionals": {
        }
    },
    {
        "endpoint": "/projects/<{PROJ_ID}>/init_repo",
        "method": requests.post,
        "to_print": M_POST,
        "additionals": {
        }
    }
# "/projects/<{PROJ_ID}>/bugs/<{BUG_ID}>"
# "/projects/<{PROJ_ID}>/ci_runs/<{PIPELINE_ID}>"
# "/projects/<{PROJ_ID}>/ci_runs/<{PIPELINE_ID}>/reports"
# "/projects/<{PROJ_ID}>/ci_runs/sync"
# "/projects/<{PROJ_ID}>/ci_runs/trigger_pipeline"
]














plurals_req = ["/projects/<{PROJ_ID}>/plans", "/projects/<{PROJ_ID}>/tags", "/projects/<{PROJ_ID}>/requirements",
               "/projects/<{PROJ_ID}>/stepdefinitions",
               "/projects/<{PROJ_ID}>/ci_runs", "/projects/<{PROJ_ID}>/ci_runs/reports",
               "/projects/<{PROJ_ID}>/bugs",
               "/users", "/users/roles", "/projects"]


# "/projects/<{PROJ_ID}>/plans/<{TPLAN_ID}>"
# "/projects/<{PROJ_ID}>/plans/<{TPLAN_ID}>/mods"
# "/projects/<{PROJ_ID}>/plans/<{TPLAN_ID}>/mods/<{PLAN_ID}>"
# "/projects/<{PROJ_ID}>/plans/<{TPLAN_ID}>/mods/<{PLAN_ID}>/cases"
# "/projects/<{PROJ_ID}>/plans/<{TPLAN_ID}>/mods/<{PLAN_ID}>/cases/<{TCASE_ID}>"
# "/projects/<{PROJ_ID}>/plans/<{TPLAN_ID}>/mods/<{PLAN_ID}>/cases/<{TCASE_ID}>/requirements"
# "/projects/<{PROJ_ID}>/plans/<{TPLAN_ID}>/mods/<{PLAN_ID}>/cases/<{TCASE_ID}>/requirements/assign-requirement"
# "/projects/<{PROJ_ID}>/requirements/<{REQ_ID}>"
# "/projects/<{PROJ_ID}>/requirements/<{REQ_ID}>/assign-tag"
# "/projects/<{PROJ_ID}>/stepdefinitions/<{DEF_ID}>/steps"
# "/projects/<{PROJ_ID}>/tags/<{TAG_ID}>"

# "/users/<{USER_ID}>"
# "/users/<{USER_ID}>/assign-project"
# "/users/<{USER_ID}>/assign-role"
# "/users/<{USER_ID}>/assign-testcase"
# "/users/roles"
# "/users/roles/<{ROLE_ID}>"
