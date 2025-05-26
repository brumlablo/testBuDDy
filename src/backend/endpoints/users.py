# TestBuDDy-Requirements-coverage
# FR-01, FR-02

import json
import traceback
import base_objects
from app import app, dbs
from flask import jsonify, request
import consts
from base_objects import Role, User


@app.route('/init-users', methods=['POST'])
def init_users():
    dbs.session.begin()
    try:
        r_cnt = dbs.session.query(Role.dbs_model).count()
        if r_cnt < 6:
            Role.create_roles()
        u_cnt = dbs.session.query(User.dbs_model).count()
        if u_cnt < 4:
            User.create_users(3)
        dbs.session.commit()
    except Exception as e:
        print(e)
        traceback.print_exc()
        dbs.session.rollback()
        return "Initialization problem: " + str(e), consts.HTTP_500_INTERNAL_SERVER_ERROR
    return "Initialization done.", consts.HTTP_200_OK


@app.route(User.routing_base, methods=['GET'])
def list_users():
    try:
        dbs.session.begin()
        users  = User.dbs_model.query.all()
        if not users:
            return "Requested users NOT found.", consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "Requested users NOT found.", consts.HTTP_404_NOT_FOUND
    result = []
    for user in users:
        assign_projs = []
        for proj in user.projects:
            assign_projs.append({'project_id': proj.id, 'name': proj.name, 'proj_repo': proj.repo_url})
        tmp = user.to_dict()
        tmp['assigned_projects'] = assign_projs
        result.append(tmp)
    respo = {"message": "Succesfully found users.", "object": result}
    return jsonify(respo), consts.HTTP_200_OK


@app.route(User.routing_base + '/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        dbs.session.begin()
        user = User.dbs_model.query.get(user_id)
        if not user:
            raise RuntimeError
        assign_projs = []
        result = []
        for proj in user.projects:
            assign_projs.append({'project_id': proj.id, 'name': proj.name, 'proj_repo': proj.repo_url})
        tmp = user.to_dict()
        tmp['assigned_projects'] = assign_projs
        result.append(tmp)
        response = {"message": "Successfully found user.", "object": result}
        return jsonify(response), consts.HTTP_200_OK
    except Exception as e:
        print(e)
        return "User with id: " + str(user_id) + " NOT found.", consts.HTTP_404_NOT_FOUND


@app.route(User.routing_base, methods=['POST'])
def create_user():
    # Users.dbs_model.query.all()
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None:
            return "Invalid json data.", consts.HTTP_400_BAD_REQUEST
        if 'username' not in data_dict or 'password' not in data_dict:
            return 'Insufficient json data, please provide "username" and "password" for your user.',\
                   consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    dbs.session.begin()
    try:
        new_u = User.dbs_model(username=data_dict['username'], password_hash=data_dict['password'])
        if 'name' in data_dict:
            new_u.name = data_dict['name']
        if 'surname' in data_dict:
            new_u.surname = data_dict['surname']
        dbs.session.add(new_u)
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error creating user. User was NOT created.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Successfully created user with id: " + str(new_u.id) + ".", "object": new_u.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


@app.route(User.routing_base + '/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        dbs.session.begin()
        u_todel = User.dbs_model.query.get(user_id)  # filter_by(id=id).first()
        if not u_todel:
            raise RuntimeError
    except Exception as e:
        print(e)
        return "User with id: " + str(user_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        dbs.session.delete(u_todel)
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error deleting user. User was NOT deleted.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    return "Successfully deleted user with id: " + str(user_id) + ".\n", consts.HTTP_200_OK


@app.route(User.routing_base + '/<user_id>', methods=['PUT'])
def user_update(user_id):
    try:
        dbs.session.begin()
        if request.headers['Content-Type'] == 'application/json':
            data_dict = request.get_json()
            if data_dict is None:
                return "Invalid json data.", consts.HTTP_400_BAD_REQUEST
        else:
            return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        try:
            u_to_upd = User.dbs_model.query.get(user_id)
            if not u_to_upd:
                return "User with id: " + str(user_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
        except Exception as e:
            print(e)
            return "User with id: " + str(user_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
        if 'username' in data_dict:
            u_to_upd.username = data_dict['username']
        if 'password' in data_dict:
            u_to_upd.password_hash = data_dict['password']
        if 'name' in data_dict:
            u_to_upd.name = data_dict['name'],
        if 'surname' in data_dict:
            u_to_upd.surname = data_dict['surname']
        dbs.session.flush()
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error updating user. User was NOT updated.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "User successfully updated.", "object": u_to_upd.to_dict()}
    return jsonify(response), consts.HTTP_200_OK

# ----------------------------------------------------------------------------------- #


@app.route(User.routing_base + '/<user_id>' + '/assign-project', methods=['POST'])
def user_assign_project(user_id):
    if request.headers['Content-Type'] == 'application/json':
        proj_dict = request.get_json()
        if proj_dict is None or 'project_id' not in proj_dict:
            return "Invalid json data, please provide 'project_id'.", consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    try:
        dbs.session.begin()
        u = User.dbs_model.query.get(user_id)
        p = base_objects.Project.dbs_model.query.get(proj_dict['project_id'])
        if not u or not p:
            return "User with id: " + str(user_id) + " or project with id: " + str(proj_dict['project_id']) + \
                   " NOT found.", consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "User with id: " + str(user_id) + " or project with id: " + str(proj_dict['project_id']) + \
               " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        u.projects.append(p)
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Project could NOT be assigned to a user.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    #  p.users.append(u)
    return "Successfully assigned project to user.", consts.HTTP_200_OK


@app.route(User.routing_base + '/<user_id>' + '/assign-project', methods=['DELETE'])
def delete_user_assign_project(user_id):
    if request.headers['Content-Type'] == 'application/json':
        proj_dict = request.get_json()
        if proj_dict is None or 'project_id' not in proj_dict:
            return "Invalid json data, please provide 'project_id'.", consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    try:
        dbs.session.begin()
        u = User.dbs_model.query.get(user_id)
        p = base_objects.Project.dbs_model.query.get(proj_dict['project_id'])
        if not u or not p:
            return "User with id: " + str(user_id) + " or project with id: " + str(proj_dict['project_id']) + \
                   " NOT found.", consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "User with id: " + str(user_id) + " or project with id: " + str(proj_dict['project_id']) + \
               " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        u.projects.remove(p)
        #  p.users.remove(u)
        dbs.session.commit()
    except Exception as e:
        dbs.session.rollback()
        print(e)
        return "Assigned project could NOT be removed.", consts.HTTP_500_INTERNAL_SERVER_ERROR

    return "Successfully removed assigned project from user.", consts.HTTP_200_OK

# ----------------------------------------------------------------------------------- #
#  assign or delete 1-N role(s) to user


@app.route(User.routing_base + Role.routing_base, methods=['GET'])
def list_roles():
    dbs.session.begin()
    try:
        data = Role.dbs_model.query.all()
        if not data:
            raise RuntimeError
    except Exception as e:
        print(e)
        return "Roles NOT found.", consts.HTTP_404_NOT_FOUND
    result = []
    for r in data:
        r_dict = r.to_dict()
        r_dict["user_ids"] = [user.id for user in r.users]
        result.append(r_dict)
    response = {"message": "Roles successfully found.", "object": result}
    return jsonify(response), consts.HTTP_200_OK


@app.route(User.routing_base + Role.routing_base + '/<role_id>', methods=['GET'])
def get_role(role_id):
    dbs.session.begin()
    try:
        role = Role.dbs_model.query.get(role_id)
        if not role:
            raise RuntimeError
    except Exception as e:
        print(e)
        return "Role NOT found.", consts.HTTP_404_NOT_FOUND
    result = []
    r_dict = role.to_dict()
    r_dict["user_ids"] = [user.id for user in role.users]
    result.append(r_dict)
    response = {"message": "Role successfully found.", "object": result}
    return jsonify(response), consts.HTTP_200_OK


@app.route(User.routing_base + Role.routing_base, methods=['POST'])
def create_role():
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None:
            return "Invalid json data.", consts.HTTP_400_BAD_REQUEST
        if 'name' not in data_dict:
            return 'Insufficient json data, please provide "name" for your role.',\
                   consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    dbs.session.begin()
    try:
        new_r = Role.dbs_model(name=data_dict['name'])
        dbs.session.add(new_r)
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error creating role. Role was NOT created.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Successfully created role with id: " + str(new_r.id)+".", "object": new_r.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


@app.route(User.routing_base + Role.routing_base + '/<role_id>', methods=['DELETE'])
def delete_role(role_id):
    try:
        dbs.session.begin()
        r_todel = Role.dbs_model.query.get(role_id)  # filter_by(id=id).first()
        if not r_todel:
            raise RuntimeError
    except Exception as e:
        print(e)
        return "Role with id: " + str(role_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        dbs.session.delete(r_todel)
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error deleting role. Role was NOT deleted.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    return "Successfully deleted role with id: " + str(role_id) + ".\n", consts.HTTP_200_OK


@app.route(User.routing_base + Role.routing_base + '/<role_id>', methods=['PUT'])
def role_update(role_id):
    try:
        dbs.session.begin()
        if request.headers['Content-Type'] == 'application/json':
            data_dict = request.get_json()
            if data_dict is None or 'name' not in data_dict:
                return "Invalid json data, please provide new 'name' for your role.", consts.HTTP_400_BAD_REQUEST
        else:
            return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        try:
            r_to_upd = Role.dbs_model.query.get(role_id)
            if not r_to_upd:
                return "Role with id: " + str(role_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
        except Exception as e:
            print(e)
            return "User with id: " + str(role_id) + " NOT found.", consts.HTTP_404_NOT_FOUND
        if 'name' in data_dict:
            r_to_upd.name = data_dict['name']
        dbs.session.flush()
        dbs.session.commit()

        result = []
        r_dict = r_to_upd.to_dict()
        r_dict["user_ids"] = [user.id for user in r_to_upd.users]
        result.append(r_dict)
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Error updating role. Role was NOT updated.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    response = {"message": "Role successfully updated.", "object": r_to_upd.to_dict()}
    return jsonify(response), consts.HTTP_200_OK


@app.route(User.routing_base + '/<user_id>' + '/assign-role', methods=['POST'])
def user_assign_role(user_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None or 'role_id' not in data_dict:
            return "Invalid json data, please provide 'role_id'.", consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    try:
        dbs.session.begin()
        u = User.dbs_model.query.get(user_id)
        r = Role.dbs_model.query.get(data_dict['role_id'])
        if not (u and r):
            return "User or role NOT found.", consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "User with id: " + str(user_id) + " or role with id: " + str(data_dict['role_id']) + \
               " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        u.roles.append(r)
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Role could NOT be assigned.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    return "Successfully assigned role to user.", consts.HTTP_200_OK


@app.route(User.routing_base + '/<user_id>' + '/assign-role', methods=['DELETE'])
def delete_user_assign_role(user_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None or 'role_id' not in data_dict:
            return "Invalid json data, please provide 'role_id'.", consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    try:
        dbs.session.begin()
        u = User.dbs_model.query.get(user_id)
        r = Role.dbs_model.query.get(data_dict['role_id'])
        if not (u and r):
            return "User or role NOT found.", consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "User with id: " + str(user_id) + " or role with id: " + str(data_dict['role_id']) + \
               " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        u.roles.remove(r)
        dbs.session.commit()
    except Exception as e:
        dbs.session.rollback()
        print(e)
        return "Assigned role could NOT be removed.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    return "Successfully removed assigned role from user.", consts.HTTP_200_OK


# ----------------------------------------------------------------------------------- #
# assign test cases


@app.route(User.routing_base + '/<user_id>' + '/assign-testcase', methods=['POST'])
def user_assign_tc(user_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None or 'testcase_id' not in data_dict:
            return "Invalid json data, please provide 'testcase_id'.", consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    try:
        dbs.session.begin()
        u = User.dbs_model.query.get(user_id)
        tc = base_objects.Testcase.dbs_model.query.get(data_dict['testcase_id'])
        if not (u and tc):
            return "User or test case NOT found.", consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "User with id: " + str(user_id) + " or test_case with id: " + \
               str(data_dict['testcase_id']) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        u.assigned_test_cases.append(tc)
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Test case could NOT be assigned to user.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    return "Successfully assigned test case to user.", consts.HTTP_200_OK


@app.route(User.routing_base + '/<user_id>' + '/assign-testcase', methods=['DELETE'])
def delete_user_assign_tc(user_id):
    if request.headers['Content-Type'] == 'application/json':
        data_dict = request.get_json()
        if data_dict is None or 'testcase_id' not in data_dict:
            return "Invalid json data, please provide 'testcase_id'.", consts.HTTP_400_BAD_REQUEST
    else:
        return "Unsupported Media Type.", consts.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    try:
        dbs.session.begin()
        u = User.dbs_model.query.get(user_id)
        tc = base_objects.Testcase.dbs_model.query.get(data_dict['testcase_id'])
        if not (u and tc):
            return "User or test case NOT found.", consts.HTTP_404_NOT_FOUND
    except Exception as e:
        print(e)
        return "User with id: " + str(user_id) + " or test case with id: "\
               + str(data_dict['testcase_id']) + " NOT found.", consts.HTTP_404_NOT_FOUND
    try:
        u.assigned_test_cases.remove(tc)
        dbs.session.commit()
    except Exception as e:
        print(e)
        dbs.session.rollback()
        return "Assigned test case could not be removed from user.", consts.HTTP_500_INTERNAL_SERVER_ERROR
    return "Successfully removed assigned test case from user.", consts.HTTP_200_OK
