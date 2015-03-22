# TODO: listPosts, listThreads, listUsers

from ext import mysql, user_details, user_exists
from flask import request, jsonify, Blueprint
from werkzeug.exceptions import BadRequest

forum_api = Blueprint('forum_api', __name__)


@forum_api.route('/create/', methods=['POST'])
def forum_create():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('name' in req_json and 'short_name' in req_json and 'user' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    new_forum_name = req_json['name']
    new_forum_short_name = req_json['short_name']
    new_forum_user = req_json['user']

    conn = mysql.get_db()
    cursor = conn.cursor()

    if not user_exists(cursor, new_forum_user):
        return jsonify(code=1, response="No user with such email!")

    cursor.execute("SELECT id, user FROM Forum WHERE name=%s AND short_name=%s",
                   (new_forum_name, new_forum_short_name))
    data = cursor.fetchone()
    if data is not None:
        resp = {
            "id": data[0],
            "name": new_forum_name,
            "short_name": new_forum_short_name,
            "user": data[1]
        }
        return jsonify(code=0, response=resp)
    # TODO: know if name exists but shorts are not equal or naoborot

    sql_data = (new_forum_name, new_forum_short_name, new_forum_user)
    cursor.execute("INSERT INTO Forum VALUES (null, %s, %s, %s)", sql_data)
    conn.commit()

    resp = {
        "id": cursor.lastrowid,
        "name": new_forum_name,
        "short_name": new_forum_short_name,
        "user": new_forum_user
    }

    return jsonify(code=0, response=resp)


@forum_api.route('/details/', methods=['GET'])
def forum_details():
    req_params = request.args

    if not ('forum' in req_params):
        return jsonify(code=3, response="Wrong parameters")

    forum_short_name = req_params['forum']

    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Forum WHERE short_name=%s", (forum_short_name,))
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