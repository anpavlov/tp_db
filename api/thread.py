# TODO: list, listPosts

from ext import mysql, user_exists, thread_exists, user_details, forum_details, thread_details
from flask import request, jsonify, Blueprint
from werkzeug.exceptions import BadRequest

thread_api = Blueprint('thread_api', __name__)


@thread_api.route('/create/', methods=['POST'])
def thread_create():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('forum' in req_json and 'title' in req_json and 'isClosed' in req_json
            and 'user' in req_json and 'date' in req_json
            and 'message' in req_json and 'slug' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    new_thread_forum = req_json['forum']
    new_thread_title = req_json['title']
    new_thread_user = req_json['user']
    new_thread_date = req_json['date']
    new_thread_message = req_json['message']
    new_thread_slug = req_json['slug']

    if req_json['isDeleted'] is not False and req_json['isDeleted'] is not True:
        return jsonify(code=3, response="Wrong parameters")
    new_thread_is_closed = req_json['isDeleted']

    if 'isDeleted' in req_json:
        if req_json['isDeleted'] is not False and req_json['isDeleted'] is not True:
            return jsonify(code=3, response="Wrong parameters")
        new_thread_is_deleted = req_json['isDeleted']
    else:
        new_thread_is_deleted = False

    conn = mysql.get_db()
    cursor = conn.cursor()

    if not user_exists(cursor, new_thread_user):
        return jsonify(code=1, response="No user with such email!")

    cursor.execute("SELECT 1 FROM Forum WHERE short_name=%s", (new_thread_forum,))
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No forum with such short name!")

    sql_data = (new_thread_forum, new_thread_user, new_thread_title, new_thread_message, new_thread_slug,
                new_thread_date, new_thread_is_closed, new_thread_is_deleted)
    cursor.execute("INSERT INTO Thread VALUES (null, %s, %s, %s, %s, %s, %s, %s, %s, 0, 0, 0, 0)", sql_data)
    conn.commit()

    resp = {
        "date": new_thread_date,
        "forum": new_thread_forum,
        "id": cursor.lastrowid,
        "isClosed": bool(new_thread_is_closed),
        "isDeleted": bool(new_thread_is_deleted),
        "message": new_thread_message,
        "slug": new_thread_slug,
        "title": new_thread_title,
        "user": new_thread_user
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/details/', methods=['GET'])
def thread_details():
    req_params = request.args

    if not ('thread' in req_params):
        return jsonify(code=3, response="Wrong parameters")

    thread_id = req_params['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT forum, user, title, message, slug, DATE_FORMAT(date,'%%Y-%%m-%%d %%T'),"
                   "isClosed, isDeleted, posts, likes, dislikes, points FROM Thread WHERE id=%s", (thread_id,))
    data = cursor.fetchone()
    if data is None:
        return jsonify(code=1, response="No thread with such id!")

    if 'related' in req_params:
        related_list = request.args.getlist('related')

        if 'forum' in related_list:
            forum_info = forum_details(cursor, data[0])
        else:
            forum_info = data[0]

        if 'user' in related_list:
            user_info = user_details(cursor, data[1])
        else:
            user_info = data[1]

    else:
        user_info = data[1]
        forum_info = data[0]

    resp = {
        "id": thread_id,
        "forum": forum_info,
        "user": user_info,
        "title": data[2],
        "message": data[3],
        "slug": data[4],
        "date": data[5],
        "isClosed": bool(data[6]),
        "isDeleted": bool(data[7]),
        "posts": data[8],
        "likes": data[9],
        "dislikes": data[10],
        "points": data[11]
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/close/', methods=['POST'])
def thread_close():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    thread_id = req_json['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT isClosed FROM Thread WHERE id=%s", (thread_id,))
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No thread with such id!")

    if data[0] is False:
        cursor.execute("UPDATE Thread SET isClosed=TRUE WHERE id=%s", (thread_id,))
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

    thread_id = req_json['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT isClosed FROM Thread WHERE id=%s", (thread_id,))
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No thread with such id!")

    if data[0] is True:
        cursor.execute("UPDATE Thread SET isClosed=FALSE WHERE id=%s", (thread_id,))
        conn.commit()

    resp = {
        "thread": thread_id
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/remove/', methods=['POST'])
def thread_remove():
    # TODO: remove posts inside
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    thread_id = req_json['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT isDeleted FROM Thread WHERE id=%s", (thread_id,))
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No thread with such id!")

    if data[0] is False:
        cursor.execute("UPDATE Thread SET isDeleted=TRUE WHERE id=%s", (thread_id,))
        conn.commit()

    resp = {
        "thread": thread_id
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/restore/', methods=['POST'])
def thread_restore():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    thread_id = req_json['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT isDeleted FROM Thread WHERE id=%s", (thread_id,))
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No thread with such id!")

    if data[0] is True:
        cursor.execute("UPDATE Thread SET isDeleted=FALSE WHERE id=%s", (thread_id,))
        conn.commit()

    resp = {
        "thread": thread_id
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/subscribe/', methods=['POST'])
def thread_subscribe():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json and 'user' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    thread_id = req_json['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    user = req_json['user']

    conn = mysql.get_db()
    cursor = conn.cursor()

    if not user_exists(cursor, user):
        return jsonify(code=1, response="No user with such email!")

    if not thread_exists(cursor, thread_id):
        return jsonify(code=1, response="No thread with such id!")

    cursor.execute("INSERT IGNORE INTO Subscriptions VALUES (%s, %s)", (user, thread_id))
    conn.commit()

    resp = {
        "thread": thread_id,
        "user": user
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/unsubscribe/', methods=['POST'])
def thread_unsubscribe():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json and 'user' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    thread_id = req_json['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    user = req_json['user']

    conn = mysql.get_db()
    cursor = conn.cursor()

    if not user_exists(cursor, user):
        return jsonify(code=1, response="No user with such email!")

    if not thread_exists(cursor, thread_id):
        return jsonify(code=1, response="No thread with such id!")

    cursor.execute("DELETE FROM Subscriptions WHERE user=%s AND thread=%s", (user, thread_id))
    conn.commit()

    resp = {
        "thread": thread_id,
        "user": user
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/update/', methods=['POST'])
def thread_update():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json and 'message' in req_json and 'slug' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    thread_id = req_json['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    thread_new_message = req_json['message']
    thread_new_slug = req_json['slug']

    conn = mysql.get_db()
    cursor = conn.cursor()

    if not thread_exists(cursor, thread_id):
        return jsonify(code=1, response="No thread with such id!")

    sql_data = (thread_new_message, thread_new_slug, thread_id)
    cursor.execute("UPDATE Thread SET message=%s AND slug=%s WHERE id=%s", sql_data)
    conn.commit()

    resp = thread_details(cursor, thread_id)

    return jsonify(code=0, response=resp)


@thread_api.route('/vote/', methods=['POST'])
def thread_vote():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('thread' in req_json and 'vote' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    thread_id = req_json['thread']
    try:
        thread_id = int(thread_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    vote = req_json['vote']
    try:
        vote = int(vote)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")
    if vote != 1 and vote != -1:
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.get_db()
    cursor = conn.cursor()

    if not thread_exists(cursor, thread_id):
        return jsonify(code=1, response="No thread with such id!")

    if vote == 1:
        cursor.execute("UPDATE Thread SET likes=likes+1 WHERE id=%s", (thread_id,))
    else:
        cursor.execute("UPDATE Thread SET dislikes=dislikes+1 WHERE id=%s", (thread_id,))

    cursor.execute("UPDATE Thread SET points=points+%s WHERE id=%s", (vote, thread_id))
    conn.commit()

    resp = thread_details(cursor, thread_id)

    return jsonify(code=0, response=resp)