# Unittests for each endpoint
import datetime
import json
import os
import random
from pprint import pprint
import requests

# globals
root_url = "http://backend:5000"
req_counter = 0

M_POST = "POST   http://localhost:5000"
M_DEL =  "DELETE http://localhost:5000"
M_PUT =  "PUT    http://localhost:5000"
M_GET =  "GET    http://localhost:5000"

id = {"proj": 0, "newproj": 0, "tplan": 0, "tmod": 0, "newtmod": 0, "tcase": 0, "stepdef": 0,
      "pipeline": 0, "bug": 0, "req": 0, "tag": 0, "user": 0, "role": 0}


# tests
def init_tests():
    print("--------------------------Demo endpoints------------------------------")
    init_endpoints = [
        {
            "endpoint": "",
            "method": requests.get,
            "to_print": M_GET,
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


def proj_tests():
    print("--------------------------Project management--------------------------")
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
                            "name": "test_proj" + str(random.randint(0, 666)),
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
            "endpoint": "/projects/{PROJ_ID}",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}",
            "method": requests.put,
            "to_print": M_PUT,
            "additionals": {
                            "json": {"name": "something new" + str(random.randint(0, 666))}
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}",
            "method": requests.delete,
            "to_print": M_DEL,
            "additionals": {
            }
        }
    ]
    # get created project id
    tmp_e = proj_endpoints[1]
    print(tmp_e["to_print"] + tmp_e["endpoint"])
    r = tmp_e["method"](root_url + tmp_e["endpoint"], **tmp_e["additionals"])
    assert r.status_code == 200
    new_p = (json.loads(r.content))['object']
    id["proj"] = int(new_p['id'])

    for test_req in proj_endpoints[2:]:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"]))
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"])), **test_req["additionals"])
        assert r.status_code == 200

    # plus one extra project
    tmp_e = proj_endpoints[1]
    r = tmp_e["method"](root_url + tmp_e["endpoint"], **tmp_e["additionals"])
    assert r.status_code == 200
    new_p = (json.loads(r.content))['object']
    id["newproj"] = int(new_p['id'])

    # get project id and test plan id
    tmp_e = proj_endpoints[0]
    print(tmp_e["to_print"] + tmp_e["endpoint"])
    r = tmp_e["method"](root_url + tmp_e["endpoint"], **tmp_e["additionals"])
    assert r.status_code == 200

    projects = (json.loads(r.content))['object']
    for p in projects:
        id["proj"] = int(p['id'])
        id["tplan"] = p['testplan']['id']
        break

    # repository prep tests
    proj_repo_endpoints = [
        {
            "endpoint": "/projects/{PROJ_ID}/purge_repo",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/init_repo",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
            }
        }

    ]

    for test_req in proj_repo_endpoints:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"]))
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"])), **test_req["additionals"])
        assert r.status_code == 200


def test_run_tests():
    print("------------Test execution, reporting, incident management------------")
    test_run_endpoints = [
        {
            "endpoint": "/projects/{PROJ_ID}/ci_runs/sync",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/ci_runs/trigger_pipeline",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/ci_runs",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/ci_runs/reports",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/ci_runs/{PIPELINE_ID}",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/ci_runs/{PIPELINE_ID}/reports",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/bugs",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/bugs/{BUG_ID}",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/bugs/{BUG_ID}",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
                "json": {"link": "TTR-1"}
            }
        }
    ]

    for test_req in test_run_endpoints[:3]:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"]))
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"])), **test_req["additionals"])
        assert r.status_code == 200

    # get failed pipeline_id
    tmp_e = test_run_endpoints[3]
    print(tmp_e["to_print"] + tmp_e["endpoint"].format(PROJ_ID=id["proj"]))
    r = tmp_e["method"](root_url + (tmp_e["endpoint"].format(PROJ_ID=id["proj"])), **tmp_e["additionals"])
    assert r.status_code == 200

    reports = (json.loads(r.content))['object']
    for rep in reports:
        if rep["report_data"]["result"] != "failed":
            continue
        if "test_cases" not in rep["report_data"]:
            continue
        id["pipeline"] = int(rep["ci_run"]["pipeline_id"])
        break

    for test_req in test_run_endpoints[4:6]:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"], PIPELINE_ID=id["pipeline"]))
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"], PIPELINE_ID=id["pipeline"])),
                               **test_req["additionals"])
        assert r.status_code == 200

    #  get bug id
    tmp_e = test_run_endpoints[6]
    print(tmp_e["to_print"] + tmp_e["endpoint"].format(PROJ_ID=id["proj"]))
    r = tmp_e["method"](root_url + (tmp_e["endpoint"].format(PROJ_ID=id["proj"])), **tmp_e["additionals"])
    assert r.status_code == 200
    bugs = (json.loads(r.content))['object']
    for b in bugs:
        id["bug"] = int(b['id'])
        break

    for test_req in test_run_endpoints[7:]:
        print(tmp_e["to_print"] + tmp_e["endpoint"].format(PROJ_ID=id["proj"], BUG_ID=id["bug"]))
        r = tmp_e["method"](root_url + (tmp_e["endpoint"].format(PROJ_ID=id["proj"], BUG_ID=id["bug"])),
                            **tmp_e["additionals"])
        assert r.status_code == 200


def test_library_tests():
    print("----------------------------Test library------------------------------")
    tp_endpoints = [
        {
            "endpoint": "/projects/plans",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/plans",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{NEWPROJ_ID}/plans",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
                "json": {
                    "name": "test_plan" + str(random.randint(0, 666)),
                }
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/plans/{TPLAN_ID}",
            "method": requests.put,
            "to_print": M_PUT,
            "additionals": {
                "json": {
                            "name": "new test plan" + str(random.randint(0, 666)),
                         }
            }
        }
    ]
    for test_req in tp_endpoints:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                 NEWPROJ_ID=id["newproj"],
                                                                 TPLAN_ID=id["tplan"]))
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                       NEWPROJ_ID=id["newproj"],
                                                                       TPLAN_ID=id["tplan"])),
                               **test_req["additionals"])
        assert r.status_code == 200

    tmod_endpoints = [
        {
            "endpoint": "/projects/{PROJ_ID}/plans/{TPLAN_ID}/mods",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
                "json": {
                    "name": "test_module" + str(random.randint(0, 666)),
                }
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/plans/{TPLAN_ID}/mods/{TMOD_ID}",
            "method": requests.put,
            "to_print": M_PUT,
            "additionals": {
                "json": {
                            "name": "new test module" + str(random.randint(0, 666)),
                         }
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/plans/{TPLAN_ID}/mods/{TMOD_ID}",
            "method": requests.delete,
            "to_print": M_DEL,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/plans/{TPLAN_ID}",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        }
    ]

    # get created module id
    tmp_e = tmod_endpoints[0]
    print(tmp_e["to_print"] + (tmp_e["endpoint"].format(PROJ_ID=id["proj"], TPLAN_ID=id["tplan"])))
    r = tmp_e["method"](root_url + (tmp_e["endpoint"].format(PROJ_ID=id["proj"], TPLAN_ID=id["tplan"])),
                        **tmp_e["additionals"])
    assert r.status_code == 200
    id["tmod"] = int((json.loads(r.content))['object']['id'])

    for test_req in tmod_endpoints[1:-1]:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                 TPLAN_ID=id["tplan"],
                                                                 TMOD_ID=id["tmod"]))
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                       TPLAN_ID=id["tplan"],
                                                                       TMOD_ID=id["tmod"])),
                               **test_req["additionals"])
        assert r.status_code == 200

    # get module id
    tmp_e = tmod_endpoints[-1]
    print(tmp_e["to_print"] + (tmp_e["endpoint"].format(PROJ_ID=id["proj"], TPLAN_ID=id["tplan"])))
    r = tmp_e["method"](root_url + (tmp_e["endpoint"].format(PROJ_ID=id["proj"], TPLAN_ID=id["tplan"])),
                        **tmp_e["additionals"])
    assert r.status_code == 200

    modules = (json.loads(r.content))['object']['test_modules']
    for mod in modules:
        if "testcases" in mod:
            id["tmod"] = int(mod['id'])
            for tc in mod["testcases"]:
                id["tcase"] = int(tc['id'])
                break
            break

    tcase_endpoints = [
        {
            "endpoint": "/projects/{PROJ_ID}/plans/{TPLAN_ID}/mods/{TMOD_ID}/cases",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/plans/{TPLAN_ID}/mods/{TMOD_ID}/cases",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
                "json": {
                        "name": "test case " + str(random.randint(0, 666)),
                        "description": "blabla"
                }
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/plans/{TPLAN_ID}/mods/{TMOD_ID}/cases/{TCASE_ID}",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
                "headers": {
                    "content-type": "text/plain"
                },
                "data": "Scenario: Unit test scenario test 123\n"
                        "Given It [is] a [happy] day\n"
                        "When [Sun] is shining\n"
                        "Then It is a [fun] day\n"
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/plans/{TPLAN_ID}/mods/{TMOD_ID}/cases/{TCASE_ID}",
            "method": requests.put,
            "to_print": M_PUT,
            "additionals": {
                "json": {
                            "name": "new test case name" + str(random.randint(0, 666))
                         }
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/stepdefinitions",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/stepdefinitions/{DEF_ID}/steps",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/plans/{TPLAN_ID}/mods/{TMOD_ID}/cases/{TCASE_ID}",
            "method": requests.delete,
            "to_print": M_DEL,
            "additionals": {
            }
        }
    ]
    for test_req in tcase_endpoints[:4]:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                 TPLAN_ID=id["tplan"],
                                                                 TMOD_ID=id["tmod"],
                                                                 TCASE_ID=id["tcase"]))
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                       TPLAN_ID=id["tplan"],
                                                                       TMOD_ID=id["tmod"],
                                                                       TCASE_ID=id["tcase"])),
                               **test_req["additionals"])
        assert r.status_code == 200

    # get step def id
    tmp_e = tcase_endpoints[4]
    print(tmp_e["to_print"] + (tmp_e["endpoint"].format(PROJ_ID=id["proj"], TPLAN_ID=id["tplan"])))
    r = tmp_e["method"](root_url + (tmp_e["endpoint"].format(PROJ_ID=id["proj"], TPLAN_ID=id["tplan"])),
                        **tmp_e["additionals"])
    assert r.status_code == 200
    stepdefs = (json.loads(r.content))['object']
    for sd in stepdefs:
        id["stepdef"] = int(sd['id'])
        break

    for test_req in tcase_endpoints[5:]:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                 TPLAN_ID=id["tplan"],
                                                                 TMOD_ID=id["tmod"],
                                                                 TCASE_ID=id["tcase"],
                                                                 DEF_ID=id["stepdef"]))
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                       TPLAN_ID=id["tplan"],
                                                                       TMOD_ID=id["tmod"],
                                                                       TCASE_ID=id["tcase"],
                                                                       DEF_ID=id["stepdef"])),
                               **test_req["additionals"])
        assert r.status_code == 200

    tmp_e = tcase_endpoints[0]
    r = tmp_e["method"](root_url + (tmp_e["endpoint"].format(PROJ_ID=id["proj"], TPLAN_ID=id["tplan"],
                                                             TMOD_ID=id["tmod"])), **tmp_e["additionals"])
    cases = (json.loads(r.content))['object']
    for c in cases:
        id["tcase"] = int(c["id"])
        break


def requirements_tests():
    print("------------------------Requirement management------------------------")
    tag_endpoints = [
        {
            "endpoint": "/projects/{PROJ_ID}/tags",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/tags",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
                "json": {
                    "content": "my new tag" + str(random.randint(0, 666)),
                    "category": "functional"
                }

            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/tags/{TAG_ID}",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
                }

        },
        {
            "endpoint": "/projects/{PROJ_ID}/tags/{TAG_ID}",
            "method": requests.put,
            "to_print": M_PUT,
            "additionals": {
                "json": {
                    "content": "my renamed tag" + str(random.randint(0, 666)),
                }
            }

        },
        {
            "endpoint": "/projects/{PROJ_ID}/tags/{TAG_ID}",
            "method": requests.delete,
            "to_print": M_DEL,
            "additionals": {
            }

        }
    ]
    # get tag id
    tmp_e = tag_endpoints[0]
    print(tmp_e["to_print"] + (tmp_e["endpoint"].format(PROJ_ID=id["proj"])))
    r = tmp_e["method"](root_url + (tmp_e["endpoint"].format(PROJ_ID=id["proj"])), **tmp_e["additionals"])
    assert r.status_code == 200
    tags = (json.loads(r.content))['object']
    for t in tags:
        id["tag"] = int(t['id'])
        break

    for test_req in tag_endpoints[1:-1]:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"], TAG_ID=id["tag"]))
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"], TAG_ID=id["tag"])),
                               **test_req["additionals"])
        assert r.status_code == 200

    req_endpoints = [
        {
            "endpoint": "/projects/{PROJ_ID}/requirements",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/requirements",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
                "json": {
                    "content": "my new req" + str(random.randint(0, 666)),
                }

            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/requirements/{REQ_ID}",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }

        },
        {
            "endpoint": "/projects/{PROJ_ID}/requirements/{REQ_ID}",
            "method": requests.put,
            "to_print": M_PUT,
            "additionals": {
                "json": {
                    "content": "my renamed req" + str(random.randint(0, 666)),
                }
            }

        },
        {
            "endpoint": "/projects/{PROJ_ID}/requirements/{REQ_ID}",
            "method": requests.delete,
            "to_print": M_DEL,
            "additionals": {
            }

        }
    ]
    # get requirement id
    tmp_e = req_endpoints[0]
    print(tmp_e["to_print"] + (tmp_e["endpoint"].format(PROJ_ID=id["proj"])))
    r = tmp_e["method"](root_url + (tmp_e["endpoint"].format(PROJ_ID=id["proj"])), **tmp_e["additionals"])
    assert r.status_code == 200
    tags = (json.loads(r.content))['object']
    for t in tags:
        id["req"] = int(t['id'])
        break

    for test_req in req_endpoints[1:-1]:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"], REQ_ID=id["req"]))
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"], REQ_ID=id["req"])),
                               **test_req["additionals"])
        assert r.status_code == 200


    assign_endpoints = [
        {
            "endpoint": "/projects/{PROJ_ID}/requirements/{REQ_ID}/assign-tag",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
                "json": {
                    "tag_id": 0
                }
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/requirements/{REQ_ID}/assign-tag",
            "method": requests.delete,
            "to_print": M_DEL,
            "additionals": {
                "json": {
                    "tag_id": 0
                }
            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/plans/{TPLAN_ID}/mods/{TMOD_ID}/cases/{TCASE_ID}"
                        "/requirements/assign-requirement",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
                "json": {
                    "requirement_id": 0
                }

            }
        },
        {
            "endpoint": "/projects/{PROJ_ID}/plans/{TPLAN_ID}/mods/{TMOD_ID}/cases/{TCASE_ID}/requirements",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }

        },
        {
            "endpoint": "/projects/{PROJ_ID}/plans/{TPLAN_ID}/mods/{TMOD_ID}/cases/{TCASE_ID}"
                        "/requirements/assign-requirement",
            "method": requests.delete,
            "to_print": M_DEL,
            "additionals": {
                "json": {
                    "requirement_id": 0
                }
            }

        }
    ]
    for test_req in assign_endpoints:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                 REQ_ID=id["req"],
                                                                 TAG_ID=id["tag"],
                                                                 TPLAN_ID=id["tplan"],
                                                                 TMOD_ID=id["tmod"],
                                                                 TCASE_ID=id["tcase"]))
        if "json" in test_req["additionals"]:
            if "tag_id" in test_req["additionals"]["json"]:
                test_req["additionals"]["json"]["tag_id"] = int(id["tag"])
            if "requirement_id" in test_req["additionals"]["json"]:
                test_req["additionals"]["json"]["requirement_id"] = int(id["req"])
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                       REQ_ID=id["req"],
                                                                       TAG_ID=id["tag"],
                                                                       TPLAN_ID=id["tplan"],
                                                                       TMOD_ID=id["tmod"],
                                                                       TCASE_ID=id["tcase"])),
                               **test_req["additionals"])
        assert r.status_code == 200

    for test_req in [tag_endpoints[-1], req_endpoints[-1]]:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                 REQ_ID=id["req"],
                                                                 TAG_ID=id["tag"]))
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                       REQ_ID=id["req"],
                                                                       TAG_ID=id["tag"])),
                               **test_req["additionals"])
        assert r.status_code == 200


def users_tests():
    print("----------------------User and role management------------------------")
    role_endpoints = [
        {
            "endpoint": "/users/roles",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/users/roles",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
                "json": {
                    "name": "my new role" + str(random.randint(0, 666))
                }

            }
        },
        {
            "endpoint": "/users/roles/{ROLE_ID}",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
                }

        },
        {
            "endpoint": "/users/roles/{ROLE_ID}",
            "method": requests.put,
            "to_print": M_PUT,
            "additionals": {
                "json": {
                    "name": "my renamed role" + str(random.randint(0, 666))
                }
            }

        },
        {
            "endpoint": "/users/roles/{ROLE_ID}",
            "method": requests.delete,
            "to_print": M_DEL,
            "additionals": {
            }

        }
    ]
    # get role id
    tmp_e = role_endpoints[0]
    print(tmp_e["to_print"] + (tmp_e["endpoint"].format(PROJ_ID=id["proj"])))
    r = tmp_e["method"](root_url + (tmp_e["endpoint"].format(PROJ_ID=id["proj"])), **tmp_e["additionals"])
    assert r.status_code == 200
    roles = (json.loads(r.content))['object']
    for rol in roles:
        id["role"] = int(rol['id'])
        break

    for test_req in role_endpoints[1:-1]:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"], ROLE_ID=id["role"]))
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"], ROLE_ID=id["role"])),
                               **test_req["additionals"])
        assert r.status_code == 200

    user_endpoints = [
        {
            "endpoint": "/users",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
            }
        },
        {
            "endpoint": "/users",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
                "json": {
                    "username": "my new user" + str(random.randint(0, 666)),
                    "password": "12346789"
                }
            }
        },
        {
            "endpoint": "/users/{USER_ID}",
            "method": requests.get,
            "to_print": M_GET,
            "additionals": {
                }

        },
        {
            "endpoint": "/users/{USER_ID}",
            "method": requests.put,
            "to_print": M_PUT,
            "additionals": {
                "json": {
                    "username": "my renamed user" + str(random.randint(0, 666))
                }
            }

        },
        {
            "endpoint": "/users/{USER_ID}",
            "method": requests.delete,
            "to_print": M_DEL,
            "additionals": {
            }

        }
    ]
    # get user id
    tmp_e = user_endpoints[0]
    print(tmp_e["to_print"] + (tmp_e["endpoint"].format(PROJ_ID=id["proj"])))
    r = tmp_e["method"](root_url + (tmp_e["endpoint"].format(PROJ_ID=id["proj"])), **tmp_e["additionals"])
    assert r.status_code == 200
    users = (json.loads(r.content))['object']
    for u in users:
        id["user"] = int(u['id'])
        break

    for test_req in user_endpoints[1:-1]:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"], USER_ID=id["user"]))
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"], USER_ID=id["user"])),
                               **test_req["additionals"])
        assert r.status_code == 200

    assign_endpoints = [
        {
            "endpoint": "/users/{USER_ID}/assign-project",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
                "json": {
                    "project_id": 0
                }
            }
        },
        {
            "endpoint": "/users/{USER_ID}/assign-project",
            "method": requests.delete,
            "to_print": M_DEL,
            "additionals": {
                "json": {
                    "project_id": 0
                }
            }
        },
        {
            "endpoint": "/users/{USER_ID}/assign-role",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
                "json": {
                    "role_id": 0
                }
            }
        },
        {
            "endpoint": "/users/{USER_ID}/assign-role",
            "method": requests.delete,
            "to_print": M_DEL,
            "additionals": {
                "json": {
                    "role_id": 0
                }
            }
        },
        {
            "endpoint": "/users/{USER_ID}/assign-testcase",
            "method": requests.post,
            "to_print": M_POST,
            "additionals": {
                "json": {
                    "testcase_id": 0
                }
            }
        },
        {
            "endpoint": "/users/{USER_ID}/assign-testcase",
            "method": requests.delete,
            "to_print": M_DEL,
            "additionals": {
                "json": {
                    "testcase_id": 0
                }
            }
        }
    ]

    for test_req in assign_endpoints:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                 ROLE_ID=id["role"],
                                                                 USER_ID=id["user"],
                                                                 TCASE_ID=id["tcase"]))
        if "json" in test_req["additionals"]:
            if "testcase_id" in test_req["additionals"]["json"]:
                test_req["additionals"]["json"]["testcase_id"] = int(id["tcase"])
            if "project_id" in test_req["additionals"]["json"]:
                test_req["additionals"]["json"]["project_id"] = int(id["proj"])
            if "role_id" in test_req["additionals"]["json"]:
                test_req["additionals"]["json"]["role_id"] = int(id["role"])
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                       ROLE_ID=id["role"],
                                                                       USER_ID=id["user"],
                                                                       TCASE_ID=id["tcase"])),
                               **test_req["additionals"])
        assert r.status_code == 200

    for test_req in [role_endpoints[-1], user_endpoints[-1]]:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                 USER_ID=id["user"],
                                                                 ROLE_ID=id["role"]))
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"],
                                                                       USER_ID=id["user"],
                                                                       ROLE_ID=id["role"])),
                               **test_req["additionals"])
        assert r.status_code == 200


def final_cleanup():
    print("--------------------------Final cleanup-------------------------------")
    proj_repo_endpoints = [
        {
            "endpoint": "/projects/{PROJ_ID}/purge_repo",
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
        }
    ]
    for test_req in proj_repo_endpoints:
        print(test_req["to_print"] + test_req["endpoint"].format(PROJ_ID=id["proj"]))
        r = test_req["method"](root_url + (test_req["endpoint"].format(PROJ_ID=id["proj"])), **test_req["additionals"])
        assert r.status_code == 200


if __name__ == '__main__':
    print("--------------------------TESTBUDDY---TESTS---------------------------")
    init_tests()
    proj_tests()
    test_run_tests()
    test_library_tests()
    requirements_tests()
    users_tests()
    final_cleanup()
    print("--------------------------TESTBUDDY---TESTS--DONE---------------------")