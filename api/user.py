from ext import mysql, get_followers, user_exists, get_subs
from flask import request, jsonify, Blueprint
from werkzeug.exceptions import BadRequest
from datetime import datetime

user_api = Blueprint('user_api', __name__)


@user_api.route('/create/', methods=['POST'])
def user_create():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('username' in req_json and 'about' in req_json and 'name' in req_json and 'email' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    new_user_username = req_json['username']
    new_user_about = req_json['about']
    new_user_name = req_json['name']
    new_user_email = req_json['email']

    if 'isAnonymous' in req_json:
        if req_json['isAnonymous'] is not False and req_json['isAnonymous'] is not True:
            return jsonify(code=3, response="Wrong parameters")
        new_user_is_anon = req_json['isAnonymous']
    else:
        new_user_is_anon = False

    conn = mysql.get_db()
    cursor = conn.cursor()

    if user_exists(cursor, new_user_email):
        return jsonify(code=5, response="User with such email already exists!")

    sql_data = (new_user_about, new_user_email, new_user_is_anon, new_user_name, new_user_username)
    cursor.execute('INSERT INTO User VALUES (null,%s,%s,%s,%s,%s)', sql_data)
    conn.commit()

    resp = {
        "email": new_user_email,
        "username": new_user_username,
        "about": new_user_about,
        "name": new_user_name,
        "isAnonymous": new_user_is_anon,
        "id": cursor.lastrowid,
    }

    return jsonify(code=0, response=resp)


@user_api.route('/details/', methods=['GET'])
def user_details():
    req_params = request.args

    if not ('user' in req_params):
        return jsonify(code=3, response="Wrong parameters")

    user_email = req_params['user']

    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM User WHERE email=%s', (user_email,))
    user_data = cursor.fetchone()

    if user_data is None:
        return jsonify(code=1, response="No user with such email!")

    follow_info = get_followers(cursor, user_email)
    subs_list = get_subs(cursor, user_email)

    resp = {
        "id": user_data[0],
        "about": user_data[1],
        "email": user_data[2],
        "isAnonymous": bool(user_data[3]),
        "name": user_data[4],
        "username": user_data[5],
        "followers": follow_info['followers'],
        "following": follow_info['following'],
        "subscriptions": subs_list
    }
    return jsonify(code=0, response=resp)


@user_api.route('/follow/', methods=['POST'])
def user_follow():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('follower' in req_json and 'followee' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    follower_email = req_json['follower']
    followee_email = req_json['followee']

    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM User WHERE email=%s', (follower_email,))
    follower_data = cursor.fetchone()

    if follower_data is None:
        return jsonify(code=1, response="No user with such email!")

    if not user_exists(cursor, followee_email):
        return jsonify(code=1, response="No user with such email!")

    cursor.execute("INSERT IGNORE INTO Followers VALUES (%s, %s)", (follower_email, followee_email))
    conn.commit()

    follow_info = get_followers(cursor, follower_email)
    subs_list = get_subs(cursor, follower_email)

    resp = {
        "id": follower_data[0],
        "about": follower_data[1],
        "email": follower_data[2],
        "isAnonymous": bool(follower_data[3]),
        "name": follower_data[4],
        "username": follower_data[5],
        "followers": follow_info['followers'],
        "following": follow_info['following'],
        "subscriptions": subs_list
    }

    return jsonify(code=0, response=resp)


@user_api.route('/listFollowers/', methods=['GET'])
def user_list_followers():
    req_params = request.args

    if not ('user' in req_params):
        return jsonify(code=3, response="Wrong parameters")

    user_email = req_params['user']

    if "since_id" in req_params:
        since_id = req_params['since_id']
        try:
            since_id = int(since_id)
        except ValueError:
            return jsonify(code=3, response="Wrong parameters")
    else:
        since_id = 0

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

    conn = mysql.get_db()
    cursor = conn.cursor()

    if not user_exists(cursor, user_email):
        return jsonify(code=1, response="No user with such email!")

    query = "SELECT id, about, email, isAnonymous, name, username FROM Followers F " +\
            "JOIN User U ON F.follower_email=U.email WHERE id>=%s AND followee_email=%s ORDER BY name "
    query += order
    query += " LIMIT %s" if limit is not None else ""

    sql_data = (since_id, user_email, limit) if limit is not None else (since_id, user_email)

    cursor.execute(query, sql_data)

    data = cursor.fetchall()

    resp = []
    for f in data:
        follow_info = get_followers(cursor, f[2])
        subs_list = get_subs(cursor, f[2])
        user = {
            "id": f[0],
            "about": f[1],
            "email": f[2],
            "isAnonymous": bool(f[3]),
            "name": f[4],
            "username": f[5],
            "followers": follow_info['followers'],
            "following": follow_info['following'],
            "subscriptions": subs_list
        }
        resp.append(user)

    return jsonify(code=0, response=resp)


@user_api.route('/listFollowing/', methods=['GET'])
def user_list_following():
    req_params = request.args

    if not ('user' in req_params):
        return jsonify(code=3, response="Wrong parameters")

    user_email = req_params['user']

    if "since_id" in req_params:
        since_id = req_params['since_id']
        try:
            since_id = int(since_id)
        except ValueError:
            return jsonify(code=3, response="Wrong parameters")
    else:
        since_id = 0

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

    conn = mysql.get_db()
    cursor = conn.cursor()

    if not user_exists(cursor, user_email):
        return jsonify(code=1, response="No user with such email!")

    query = "SELECT id, about, email, isAnonymous, name, username FROM Followers F " +\
            "JOIN User U ON F.followee_email=U.email WHERE id>=%s AND follower_email=%s ORDER BY name "
    query += order
    query += " LIMIT %s" if limit is not None else ""

    sql_data = (since_id, user_email, limit) if limit is not None else (since_id, user_email)

    cursor.execute(query, sql_data)

    data = cursor.fetchall()

    resp = []
    for f in data:
        follow_info = get_followers(cursor, f[2])
        subs_list = get_subs(cursor, f[2])
        user = {
            "id": f[0],
            "about": f[1],
            "email": f[2],
            "isAnonymous": bool(f[3]),
            "name": f[4],
            "username": f[5],
            "followers": follow_info['followers'],
            "following": follow_info['following'],
            "subscriptions": subs_list
        }
        resp.append(user)

    return jsonify(code=0, response=resp)


@user_api.route('/listPosts/', methods=['GET'])
def user_list_posts():
    req_params = request.args

    if not ('user' in req_params):
        return jsonify(code=3, response="Wrong parameters")

    user_email = req_params['user']

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

    if not user_exists(cursor, user_email):
        return jsonify(code=1, response="No user with such email!")

    query = "SELECT id, forum, thread, parent, message, DATE_FORMAT(date,'%%Y-%%m-%%d %%T') d," \
            "isApproved, isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points FROM Post " \
            "WHERE date>=%s AND user=%s ORDER BY d "
    query += order
    query += " LIMIT %s" if limit is not None else ""

    sql_data = (since, user_email, limit) if limit is not None else (since, user_email)

    cursor.execute(query, sql_data)

    data = cursor.fetchall()

    resp = []
    for p in data:
        post = {
            "id": p[0],
            "forum": p[1],
            "thread": p[2],
            "user": user_email,
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


@user_api.route('/unfollow/', methods=['POST'])
def user_unfollow():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('follower' in req_json and 'followee' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    follower_email = req_json['follower']
    followee_email = req_json['followee']

    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM User WHERE email=%s", (follower_email,))
    follower_data = cursor.fetchone()

    if follower_data is None:
        return jsonify(code=1, response="No user with such email!")

    if not user_exists(cursor, followee_email):
        return jsonify(code=1, response="No user with such email!")

    cursor.execute("DELETE FROM Followers WHERE follower_email=%s AND followee_email=%s",
                   (follower_email, followee_email))
    conn.commit()

    follow_info = get_followers(cursor, follower_email)
    subs_list = get_subs(cursor, follower_email)

    resp = {
        "id": follower_data[0],
        "about": follower_data[1],
        "email": follower_data[2],
        "isAnonymous": bool(follower_data[3]),
        "name": follower_data[4],
        "username": follower_data[5],
        "followers": follow_info['followers'],
        "following": follow_info['following'],
        "subscriptions": subs_list
    }

    return jsonify(code=0, response=resp)


@user_api.route('/updateProfile/', methods=['POST'])
def user_update_profile():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('user' in req_json and 'about' in req_json and 'name' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    user_email = req_json['user']
    new_user_about = req_json['about']
    new_user_name = req_json['name']

    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, isAnonymous FROM User WHERE email=%s", (user_email,))
    user_data = cursor.fetchone()
    if user_data is None:
        return jsonify(code=1, response="No user with such email!")

    sql_data = (new_user_about, new_user_name, user_email)
    cursor.execute("UPDATE User SET about=%s, name=%s WHERE email=%s", sql_data)
    conn.commit()

    follow_info = get_followers(cursor, user_email)
    subs_list = get_subs(cursor, user_email)

    resp = {
        "email": user_email,
        "username": user_data[1],
        "about": new_user_about,
        "name": new_user_name,
        "isAnonymous": bool(user_data[2]),
        "id": user_data[0],
        "followers": follow_info['followers'],
        "following": follow_info['following'],
        "subscriptions": subs_list
    }

    return jsonify(code=0, response=resp)