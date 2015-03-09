# TODO: list, listPosts, update, vote

from ext import mysql, user_exists, user_details, forum_details
from flask import request, jsonify, Blueprint
from werkzeug.exceptions import BadRequest

thread_api = Blueprint('thread_api', __name__)


@thread_api.route('/create', methods=['POST'])
def thread_create():
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
    new_thread_user = conn.escape_string(req_json['user'])
    new_thread_date = conn.escape_string(req_json['date'])
    new_thread_message = conn.escape_string(req_json['message'])
    new_thread_slug = conn.escape_string(req_json['slug'])

    if req_json['isDeleted'] is not False and req_json['isDeleted'] is not True:
        return jsonify(code=3, response="Wrong parameters")
    new_thread_is_closed = req_json['isDeleted']

    if 'isDeleted' in req_json:
        if req_json['isDeleted'] is not False and req_json['isDeleted'] is not True:
            return jsonify(code=3, response="Wrong parameters")
        new_thread_is_deleted = req_json['isDeleted']
    else:
        new_thread_is_deleted = False

    if not user_exists(cursor, new_thread_user):
        return jsonify(code=1, response="No user with such email!")

    cursor.execute("SELECT 1 FROM Forum WHERE short_name='" + new_thread_forum + "'")
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No forum with such short name!")

    cursor.execute("SELECT id, user, isClosed, isDeleted, date FROM Thread WHERE forum='" + new_thread_forum +
                   "' AND title='" + new_thread_title + "' AND message='" + new_thread_message +
                   "' AND slug='" + new_thread_slug + "'")
    data = cursor.fetchone()
    if data is not None:
        resp = {
            "date": data[4],
            "forum": new_thread_forum,
            "id": data[0],
            "isClosed": bool(data[2]),
            "isDeleted": bool(data[3]),
            "message": new_thread_message,
            "slug": new_thread_slug,
            "title": new_thread_title,
            "user": data[1]
        }
        return jsonify(code=0, response=resp)

    cursor.execute("INSERT INTO Thread VALUES (null,'" + new_thread_forum + "','" + new_thread_user +
                   "','" + new_thread_title + "','" + new_thread_message + "','" + new_thread_slug +
                   "','" + new_thread_date + "','" + str(new_thread_is_closed) + "','" +
                   str(new_thread_is_deleted) + "', 0, 0, 0, 0)")
    conn.commit()

    cursor.execute("SELECT id FROM Thread WHERE forum='" + new_thread_forum +
                   "' AND title='" + new_thread_title + "' AND message='" + new_thread_message + "'")

    data = cursor.fetchone()

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


@thread_api.route('/details', methods=['GET'])
def thread_details():
    req_params = request.args

    if not ('thread' in req_params):
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.connect()
    cursor = conn.cursor()

    thread_id = req_params['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    cursor.execute("SELECT * FROM Thread WHERE id=" + thread_id)
    data = cursor.fetchone()
    if data is None:
        return jsonify(code=1, response="No thread with such id!")

    if 'related' in req_params:
        related_list = request.args.getlist('related')
        if 'user' in related_list:
            user_info = user_details(cursor, data[2])
        else:
            user_info = data[2]
        if 'forum' in related_list:
            forum_info = forum_details(cursor, data[1])
        else:
            forum_info = data[1]
    else:
        user_info = data[2]
        forum_info = data[1]

    resp = {
        "id": data[0],
        "forum": forum_info,
        "user": user_info,
        "title": data[3],
        "message": data[4],
        "slug": data[5],
        "date": data[6],
        "isClosed": bool(data[7]),
        "isDeleted": bool(data[8]),
        "posts": data[9],
        "likes": data[10],
        "dislikes": data[11],
        "points": data[12]
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/close', methods=['POST'])
def thread_close():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.connect()
    cursor = conn.cursor()

    thread_id = req_json['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    cursor.execute("SELECT isClosed FROM Thread WHERE id=" + thread_id)
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No thread with such id!")

    if data[0] is False:
        cursor.execute("UPDATE Thread SET isClosed=TRUE WHERE id=" + thread_id)
        conn.commit()

    resp = {
        "thread": thread_id
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/open', methods=['POST'])
def thread_open():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.connect()
    cursor = conn.cursor()

    thread_id = req_json['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    cursor.execute("SELECT isClosed FROM Thread WHERE id=" + thread_id)
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No thread with such id!")

    if data[0] is True:
        cursor.execute("UPDATE Thread SET isClosed=FALSE WHERE id=" + thread_id)
        conn.commit()

    resp = {
        "thread": thread_id
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/remove', methods=['POST'])
def thread_remove():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.connect()
    cursor = conn.cursor()

    thread_id = req_json['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    cursor.execute("SELECT isDeleted FROM Thread WHERE id=" + thread_id)
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No thread with such id!")

    if data[0] is False:
        cursor.execute("UPDATE Thread SET isDeleted=TRUE WHERE id=" + thread_id)
        conn.commit()

    resp = {
        "thread": thread_id
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/restore', methods=['POST'])
def thread_restore():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.connect()
    cursor = conn.cursor()

    thread_id = req_json['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    cursor.execute("SELECT isDeleted FROM Thread WHERE id=" + thread_id)
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No thread with such id!")

    if data[0] is True:
        cursor.execute("UPDATE Thread SET isDeleted=FALSE WHERE id=" + thread_id)
        conn.commit()

    resp = {
        "thread": thread_id
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/subscribe', methods=['POST'])
def thread_subscribe():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json and 'user' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.connect()
    cursor = conn.cursor()

    thread_id = req_json['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    user = conn.escape_string(req_json['user'])

    if not user_exists(cursor, user):
        return jsonify(code=1, response="No user with such email!")

    cursor.execute("INSERT IGNORE INTO Subscriptions VALUES ('" + user + "'," + thread_id)
    conn.commit()

    resp = {
        "thread": thread_id,
        "user": user
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/unsubscribe', methods=['POST'])
def thread_unsubscribe():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json and 'user' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.connect()
    cursor = conn.cursor()

    thread_id = req_json['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    user = conn.escape_string(req_json['user'])

    if not user_exists(cursor, user):
        return jsonify(code=1, response="No user with such email!")

    cursor.execute("DELETE FROM Subscriptions WHERE user='" + user +
                   "' AND thread=" + thread_id)
    conn.commit()

    resp = {
        "thread": thread_id,
        "user": user
    }

    return jsonify(code=0, response=resp)