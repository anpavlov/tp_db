from ext import mysql
from flask import request, jsonify, Blueprint
from werkzeug.exceptions import BadRequest

thread_api = Blueprint('thread_api', __name__)


@thread_api.route('/create', methods=['POST'])
def forum_reate():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('forum' in req_json and 'title' in req_json and 'isClosed' in req_json
            and 'user' in req_json and 'date' in req_json
            and 'message' in req_json and 'slug' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.connect()
    cursor = conn.cursor()

    new_thread_forum = conn.escape_string(req_json['forum'])
    new_thread_title = conn.escape_string(req_json['title'])
    new_thread_is_closed = conn.escape_string(req_json['isClosed'])
    new_thread_user = conn.escape_string(req_json['user'])
    new_thread_date = conn.escape_string(req_json['date'])
    new_thread_message = conn.escape_string(req_json['message'])
    new_thread_slug = conn.escape_string(req_json['slug'])

    # TODO: add type check (isinstance)

    if 'isDeleted' in req_json:
        if req_json['isDeleted'] is not False and req_json['isDeleted'] is not True:
            return jsonify(code=3, response="Wrong parameters")
        new_thread_is_deleted = req_json['isDeleted']
    else:
        new_thread_is_deleted = False

    cursor.execute("SELECT 1 FROM User WHERE email='" + new_thread_user + "'")
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No user with such email!")

    cursor.execute("SELECT 1 FROM Forum WHERE short_name='" + new_thread_forum + "'")
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No forum with such short name!")

    cursor.execute("SELECT id, user FROM Thread WHERE forum='" + new_thread_forum +
                   "' AND title='" + new_thread_title + "' AND message='" + new_thread_message + "'")
    data = cursor.fetchone()
    if data is not None:

        # TODO: return existing thread
        resp = {
            # "id": data[0],
            # "name": new_forum_name,
            # "short_name": new_forum_short_name,
            # "user": data[1]
        }

        return jsonify(code=0, response=resp)

    cursor.execute("INSERT INTO Thread VALUES (null,'" + new_thread_forum + "','" + new_thread_user +
                   "','" + new_thread_title + "','" + new_thread_message + "','" + new_thread_slug +
                   "','" + new_thread_date + "','" + str(new_thread_is_closed) + "','" +
                   str(new_thread_is_deleted) + "')")
    conn.commit()

    cursor.execute("SELECT id FROM Thread WHERE forum='" + new_thread_forum +
                   "' AND title='" + new_thread_title + "' AND message='" + new_thread_message + "'")

    data = cursor.fetchone()  # got tuple

    resp = {
        "date": new_thread_date,
        "forum": new_thread_forum,
        "id": data[0],
        "isClosed": bool(new_thread_is_closed),
        "isDeleted": bool(new_thread_is_deleted),
        "message": new_thread_message,
        "slug": new_thread_slug,
        "title": new_thread_title,
        "user": new_thread_user
    }

    return jsonify(code=0, response=resp)