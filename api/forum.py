from ext import mysql, user_details, user_exists, forum_exists, thread_details, forum_details as forum_detail, get_subs, get_followers
from flask import request, jsonify, Blueprint
from werkzeug.exceptions import BadRequest
from datetime import datetime

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
    # TODO: (?) know if name exists but shorts are not equal or naoborot

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


@forum_api.route('/listPosts/', methods=['GET'])
def forum_list_posts():
    req_params = request.args

    if not ('forum' in req_params):
        return jsonify(code=3, response="Wrong parameters")

    forum = req_params['forum']

    if "limit" in req_params:
        limit = req_params['limit']
        try:
            limit = int(limit)
        except ValueError:
            return jsonify(code=3, response="Wrong parameters")
    else:
        limit = None

    if "order" in req_params:
        order = req_params['order']
        if order != 'asc' and order != 'desc':
            return jsonify(code=3, response="Wrong parameters")
    else:
        order = 'desc'

    if "since" in req_params:
        since = req_params['since']
        try:
            datetime.strptime(since, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return jsonify(code=3, response="Wrong parameters")
    else:
        since = 0

    conn = mysql.get_db()
    cursor = conn.cursor()

    if not forum_exists(cursor, forum):
        return jsonify(code=1, response="No forum with such short name!")
    
    related_forum = False
    related_thread = False
    related_user = False
    if 'related' in req_params:
        related_list = request.args.getlist('related')
        for el in related_list:
            if el != 'forum' and el != 'user' and el != 'thread':
                return jsonify(code=3, response="Wrong parameters")

        if 'forum' in related_list:
            related_forum = True
        if 'thread' in related_list:
            related_thread = True
        if 'user' in related_list:
            related_user = True

    query = "SELECT id, thread, user, parent, message, DATE_FORMAT(date,'%%Y-%%m-%%d %%T') d," \
            "isApproved, isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points FROM Post " \
            "WHERE date>=%s AND forum=%s ORDER BY d "
    query += order
    query += " LIMIT %s" if limit is not None else ""

    sql_data = (since, forum, limit) if limit is not None else (since, forum)

    cursor.execute(query, sql_data)

    data = cursor.fetchall()

    resp = []
    for p in data:
        if related_forum:
            forum_info = forum_detail(cursor, forum)
        else:
            forum_info = forum
            
        if related_thread:
            thread_info = thread_details(cursor, p[1])
        else:
            thread_info = p[1]

        if related_user:
            user_info = user_details(cursor, p[2])
        else:
            user_info = p[2]
        post = {
            "id": p[0],
            "forum": forum_info,
            "thread": thread_info,
            "user": user_info,
            "parent": p[3],
            "message": p[4],
            "date": p[5],
            "isApproved": bool(p[6]),
            "isHighlighted": bool(p[7]),
            "isEdited": bool(p[8]),
            "isSpam": bool(p[9]),
            "isDeleted": bool(p[10]),
            "likes": p[11],
            "dislikes": p[12],
            "points": p[13]
        }
        resp.append(post)

    return jsonify(code=0, response=resp)


@forum_api.route('/listThreads/', methods=['GET'])
def forum_list_threads():
    req_params = request.args

    if not ('forum' in req_params):
        return jsonify(code=3, response="Wrong parameters")

    forum = req_params['forum']

    if "limit" in req_params:
        limit = req_params['limit']
        try:
            limit = int(limit)
        except ValueError:
            return jsonify(code=3, response="Wrong parameters")
    else:
        limit = None

    if "order" in req_params:
        order = req_params['order']
        if order != 'asc' and order != 'desc':
            return jsonify(code=3, response="Wrong parameters")
    else:
        order = 'desc'

    if "since" in req_params:
        since = req_params['since']
        try:
            datetime.strptime(since, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return jsonify(code=3, response="Wrong parameters")
    else:
        since = 0

    conn = mysql.get_db()
    cursor = conn.cursor()

    if not forum_exists(cursor, forum):
        return jsonify(code=1, response="No forum with such short name!")
    
    related_forum = False
    related_user = False
    if 'related' in req_params:
        related_list = request.args.getlist('related')

        for el in related_list:
            if el != 'forum' and el != 'user':
                return jsonify(code=3, response="Wrong parameters")

        if 'forum' in related_list:
            related_forum = True
        if 'user' in related_list:
            related_user = True

    query = "SELECT id, user, title, message, slug, DATE_FORMAT(date,'%%Y-%%m-%%d %%T') d, " \
            "isClosed, isDeleted, posts, likes, dislikes, points FROM Thread " \
            "WHERE date>=%s AND forum=%s ORDER BY d "
    query += order
    query += " LIMIT %s" if limit is not None else ""

    sql_data = (since, forum, limit) if limit is not None else (since, forum)

    cursor.execute(query, sql_data)

    data = cursor.fetchall()

    resp = []
    for t in data:
        if related_forum:
            forum_info = forum_detail(cursor, forum)
        else:
            forum_info = forum
            
        if related_user:
            user_info = user_details(cursor, t[1])
        else:
            user_info = t[1]
        post = {
            "id": t[0],
            "forum": forum_info,
            "user": user_info,
            "title": t[2],
            "message": t[3],
            "slug": t[4],
            "date": t[5],
            "isClosed": bool(t[6]),
            "isDeleted": bool(t[7]),
            "posts": t[8],
            "likes": t[9],
            "dislikes": t[10],
            "points": t[11]
        }
        resp.append(post)

    return jsonify(code=0, response=resp)


@forum_api.route('/listUsers/', methods=['GET'])
def forum_list_users():
    req_params = request.args

    if not ('forum' in req_params):
        return jsonify(code=3, response="Wrong parameters")

    forum = req_params['forum']

    if "limit" in req_params:
        limit = req_params['limit']
        try:
            limit = int(limit)
        except ValueError:
            return jsonify(code=3, response="Wrong parameters")
    else:
        limit = None

    if "order" in req_params:
        order = req_params['order']
        if order != 'asc' and order != 'desc':
            return jsonify(code=3, response="Wrong parameters")
    else:
        order = 'desc'

    if "since_id" in req_params:
        since_id = req_params['since_id']
        try:
            since_id = int(since_id)
        except ValueError:
            return jsonify(code=3, response="Wrong parameters")
    else:
        since_id = 0

    conn = mysql.get_db()
    cursor = conn.cursor()

    if not forum_exists(cursor, forum):
        return jsonify(code=1, response="No forum with such short name!")

    query = "SELECT DISTINCT U.id, U.about, U.email, U.isAnonymous, U.name, U.username FROM User U " \
            "JOIN Post P ON U.email=P.user " \
            "WHERE U.id>=%s AND forum=%s ORDER BY name "
    query += order
    query += " LIMIT %s" if limit is not None else ""

    sql_data = (since_id, forum, limit) if limit is not None else (since_id, forum)

    cursor.execute(query, sql_data)

    data = cursor.fetchall()

    resp = []
    for t in data:
        follow_info = get_followers(cursor, t[2])
        subs_list = get_subs(cursor, t[2])
        post = {
            "id": t[0],
            "about": t[1],
            "email": t[2],
            "isAnonymous": bool(t[3]),
            "name": t[4],
            "username": t[5],
            "followers": follow_info['followers'],
            "following": follow_info['following'],
            "subscriptions": subs_list
        }
        resp.append(post)

    return jsonify(code=0, response=resp)