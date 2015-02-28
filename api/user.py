from ext import mysql
from flask import request, jsonify, Blueprint
from werkzeug.exceptions import BadRequest

user_api = Blueprint('user_api', __name__)


@user_api.route('/create', methods=['POST'])
def user_create():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('username' in req_json and 'about' in req_json and 'name' in req_json and 'email' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.connect()
    cursor = conn.cursor()

    new_user_username = conn.escape_string(req_json['username'])
    new_user_about = conn.escape_string(req_json['about'])
    new_user_name = conn.escape_string(req_json['name'])
    new_user_email = conn.escape_string(req_json['email'])
    new_user_is_anon = bool(req_json.get('isAnonymous', False))

    cursor.execute("SELECT 1 FROM User WHERE email='" + new_user_email + "' OR username='" + new_user_username + "'")
    data = cursor.fetchone()
    if data is not None:
        return jsonify(code=5, response="User with such email or username already exists!")

    cursor.execute("INSERT INTO User VALUES (null,'" + new_user_about + "','" + new_user_email + "','" + str(new_user_is_anon)
                   + "','" + new_user_name + "','" + new_user_username + "')")
    conn.commit()

    cursor.execute("SELECT id FROM User WHERE email='" + new_user_email + "'")

    data = cursor.fetchone()  # got tuple
    new_user_id = data[0]

    resp = {
        "email": new_user_email,
        "username": new_user_username,
        "about": new_user_about,
        "name": new_user_name,
        "isAnonymous": new_user_is_anon,
        "id": new_user_id
    }

    return jsonify(code=0, response=resp)


@user_api.route('/details', methods=['GET'])
def user_details():
    req_params = request.args

    if not ('user' in req_params):
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.connect()
    cursor = conn.cursor()

    user_email = conn.escape_string(req_params['user'])

    cursor.execute("SELECT * FROM User WHERE email='" + user_email + "'")
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No user with such email!")

    # TODO: add followers and subscriptions

    resp = {
        "id": data[0],
        "about": data[1],
        "email": data[2],
        "isAnonymous": bool(data[3]),
        "name": data[4],
        "username": data[5]
    }
    return jsonify(code=0, response=resp)