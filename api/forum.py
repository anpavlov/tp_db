# TODO: listPosts, listThreads, listUsers

from ext import mysql, user_details, user_exists
from flask import request, jsonify, Blueprint
from werkzeug.exceptions import BadRequest

forum_api = Blueprint('forum_api', __name__)


@forum_api.route('/create', methods=['POST'])
def forum_create():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('name' in req_json and 'short_name' in req_json and 'user' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.connect()
    cursor = conn.cursor()

    new_forum_name = conn.escape_string(req_json['name'])
    new_forum_short_name = conn.escape_string(req_json['short_name'])
    new_forum_user = conn.escape_string(req_json['user'])

    if not user_exists(cursor, new_forum_user):
        return jsonify(code=1, response="No user with such email!")

    cursor.execute("SELECT id, user FROM Forum WHERE name='" + new_forum_name +
                   "' AND short_name='" + new_forum_short_name + "'")
    data = cursor.fetchone()
    if data is not None:

        resp = {
            "id": data[0],
            "name": new_forum_name,
            "short_name": new_forum_short_name,
            "user": data[1]
        }

        return jsonify(code=0, response=resp)

    cursor.execute("INSERT INTO Forum VALUES (null,'" + new_forum_name + "','" +
                   new_forum_short_name + "','" + new_forum_user + "')")
    conn.commit()

    cursor.execute("SELECT id FROM Forum WHERE short_name='" + new_forum_short_name + "'")

    data = cursor.fetchone()

    resp = {
        "id": data[0],
        "name": new_forum_name,
        "short_name": new_forum_short_name,
        "user": new_forum_user
    }

    return jsonify(code=0, response=resp)


@forum_api.route('/details', methods=['GET'])
def forum_details():
    req_params = request.args

    if not ('forum' in req_params):
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.connect()
    cursor = conn.cursor()

    forum_short_name = conn.escape_string(req_params['forum'])

    cursor.execute("SELECT * FROM Forum WHERE short_name='" + forum_short_name + "'")
    data = cursor.fetchone()
    if data is None:
        return jsonify(code=1, response="No forum with such short name!")

    if 'related' in req_params:
        if req_params['related'] != 'user':
            return jsonify(code=3, response="Wrong parameters")
        user_info = user_details(cursor, data[3])
    else:
        user_info = data[3]

    resp = {
        "id": data[0],
        "name": data[1],
        "short_name": data[2],
        "user": user_info
    }

    return jsonify(code=0, response=resp)