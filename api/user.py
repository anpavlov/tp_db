# TODO: listPosts
# TODO: return subscriptions
# TODO: check for extra *_data = data after query

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
    # TODO: check isAnon param
    new_user_is_anon = bool(req_json.get('isAnonymous', False))

    cursor.execute("SELECT 1 FROM User WHERE email='" + new_user_email + "' OR username='" + new_user_username + "'")
    data = cursor.fetchone()
    if data is not None:
        return jsonify(code=5, response="User with such email or username already exists!")

    cursor.execute("INSERT INTO User VALUES (null,'" + new_user_about + "','" + new_user_email + "','" +
                   str(new_user_is_anon) + "','" + new_user_name + "','" + new_user_username + "')")
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
        "id": new_user_id,
        "followers": [],
        "following": []
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

    user_data = data

    cursor.execute("SELECT follower_email FROM Followers WHERE followee_email='" + user_email + "'")
    data = cursor.fetchall()

    # if data is not None:
    followers_list = []
    for t in data:
        followers_list.append(t[0])

    cursor.execute("SELECT followee_email FROM Followers WHERE follower_email='" + user_email + "'")
    data = cursor.fetchall()

    # if data is not None:
    following_list = []
    for t in data:
        following_list.append(t[0])

    resp = {
        "id": user_data[0],
        "about": user_data[1],
        "email": user_data[2],
        "isAnonymous": bool(user_data[3]),
        "name": user_data[4],
        "username": user_data[5],
        "followers": followers_list,
        "following": following_list
    }
    return jsonify(code=0, response=resp)


@user_api.route('/follow', methods=['POST'])
def user_follow():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('follower' in req_json and 'followee' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.connect()
    cursor = conn.cursor()

    follower_email = conn.escape_string(req_json['follower'])
    followee_email = conn.escape_string(req_json['followee'])

    cursor.execute("SELECT * FROM User WHERE email='" + follower_email + "'")
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No user with such email!")

    follower_data = data

    cursor.execute("SELECT 1 FROM User WHERE email='" + followee_email + "'")
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No user with such email!")

    cursor.execute("INSERT IGNORE INTO Followers VALUES ('" + follower_email + "','" + followee_email + "')")
    conn.commit()

    cursor.execute("SELECT follower_email FROM Followers WHERE followee_email='" + follower_email + "'")
    data = cursor.fetchall()

    # if data is not None:
    followers_list = []
    for t in data:
        followers_list.append(t[0])

    cursor.execute("SELECT followee_email FROM Followers WHERE follower_email='" + follower_email + "'")
    data = cursor.fetchall()

    # if data is not None:
    following_list = []
    for t in data:
        following_list.append(t[0])

    resp = {
        "id": follower_data[0],
        "about": follower_data[1],
        "email": follower_data[2],
        "isAnonymous": bool(follower_data[3]),
        "name": follower_data[4],
        "username": follower_data[5],
        "followers": followers_list,
        "following": following_list
    }

    return jsonify(code=0, response=resp)


@user_api.route('/listFollowers', methods=['GET'])
def user_list_followers():
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

    user_data = data

    since_id = req_params.get('since_id')
    if since_id is not None:
        try:
            since_id = int(since_id)
        except ValueError:
            return jsonify(code=3, response="Wrong parameters")
    else:
        since_id = 0

    order = req_params.get('order')
    if order is not None:
        if order != 'asc' and order != 'desc':
            return jsonify(code=3, response="Wrong parameters")
    else:
        order = 'desc'

    limit = req_params.get('limit')
    if limit is not None:
        try:
            limit = int(limit)
        except ValueError:
            return jsonify(code=3, response="Wrong parameters")

        cursor.execute("SELECT email FROM User WHERE id>" + str(since_id) +
                       " AND email IN (SELECT follower_email FROM Followers WHERE followee_email='" +
                       user_email + "') ORDER BY name " + order + " LIMIT " + str(limit))
    else:
        cursor.execute("SELECT email FROM User WHERE id>" + str(since_id) +
                       " AND email IN (SELECT follower_email FROM Followers WHERE followee_email='" +
                       user_email + "') ORDER BY name " + order)

    data = cursor.fetchall()

    followers_list = []
    for t in data:
        followers_list.append(t[0])

    cursor.execute("SELECT followee_email FROM Followers WHERE follower_email='" + user_email + "'")
    data = cursor.fetchall()

    following_list = []
    for t in data:
        following_list.append(t[0])

    resp = {
        "id": user_data[0],
        "about": user_data[1],
        "email": user_data[2],
        "isAnonymous": bool(user_data[3]),
        "name": user_data[4],
        "username": user_data[5],
        "followers": followers_list,
        "following": following_list
    }
    return jsonify(code=0, response=resp)


@user_api.route('/listFollowing', methods=['GET'])
def user_list_following():
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

    user_data = data

    cursor.execute("SELECT follower_email FROM Followers WHERE followee_email='" + user_email + "'")
    data = cursor.fetchall()

    followers_list = []
    for t in data:
        followers_list.append(t[0])

    since_id = req_params.get('since_id')
    if since_id is not None:
        try:
            since_id = int(since_id)
        except ValueError:
            return jsonify(code=3, response="Wrong parameters")
    else:
        since_id = 0

    order = req_params.get('order')
    if order is not None:
        if order != 'asc' and order != 'desc':
            return jsonify(code=3, response="Wrong parameters")
    else:
        order = 'desc'

    limit = req_params.get('limit')
    if limit is not None:
        try:
            limit = int(limit)
        except ValueError:
            return jsonify(code=3, response="Wrong parameters")

        cursor.execute("SELECT email FROM User WHERE id>" + str(since_id) +
                       " AND email IN (SELECT followee_email FROM Followers WHERE follower_email='" +
                       user_email + "') ORDER BY name " + order + " LIMIT " + str(limit))
    else:
        cursor.execute("SELECT email FROM User WHERE id>" + str(since_id) +
                       " AND email IN (SELECT followee_email FROM Followers WHERE follower_email='" +
                       user_email + "') ORDER BY name " + order)

    data = cursor.fetchall()

    following_list = []
    for t in data:
        following_list.append(t[0])

    resp = {
        "id": user_data[0],
        "about": user_data[1],
        "email": user_data[2],
        "isAnonymous": bool(user_data[3]),
        "name": user_data[4],
        "username": user_data[5],
        "followers": followers_list,
        "following": following_list
    }
    return jsonify(code=0, response=resp)


@user_api.route('/unfollow', methods=['POST'])
def user_unfollow():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('follower' in req_json and 'followee' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.connect()
    cursor = conn.cursor()

    follower_email = conn.escape_string(req_json['follower'])
    followee_email = conn.escape_string(req_json['followee'])

    cursor.execute("SELECT * FROM User WHERE email='" + follower_email + "'")
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No user with such email!")

    follower_data = data

    cursor.execute("SELECT 1 FROM User WHERE email='" + followee_email + "'")
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No user with such email!")

    cursor.execute("DELETE FROM Followers WHERE follower_email='" + follower_email +
                   "' AND followee_email='" + followee_email + "'")
    conn.commit()

    cursor.execute("SELECT follower_email FROM Followers WHERE followee_email='" + follower_email + "'")
    data = cursor.fetchall()

    # if data is not None:
    followers_list = []
    for t in data:
        followers_list.append(t[0])

    cursor.execute("SELECT followee_email FROM Followers WHERE follower_email='" + follower_email + "'")
    data = cursor.fetchall()

    # if data is not None:
    following_list = []
    for t in data:
        following_list.append(t[0])

    resp = {
        "id": follower_data[0],
        "about": follower_data[1],
        "email": follower_data[2],
        "isAnonymous": bool(follower_data[3]),
        "name": follower_data[4],
        "username": follower_data[5],
        "followers": followers_list,
        "following": following_list
    }

    return jsonify(code=0, response=resp)


@user_api.route('/updateProfile', methods=['POST'])
def user_update_profile():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('user' in req_json and 'about' in req_json and 'name' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.connect()
    cursor = conn.cursor()

    user_email = conn.escape_string(req_json['user'])
    new_user_about = conn.escape_string(req_json['about'])
    new_user_name = conn.escape_string(req_json['name'])

    cursor.execute("SELECT id, username, isAnonymous FROM User WHERE email='" + user_email + "'")
    data = cursor.fetchone()
    if data is None:
        return jsonify(code=1, response="No user with such email!")

    user_data = data

    cursor.execute("UPDATE User SET about='" + new_user_about + "', name='" + new_user_name +
                   "' WHERE email='" + user_email + "'")
    conn.commit()

    cursor.execute("SELECT follower_email FROM Followers WHERE followee_email='" + user_email + "'")
    data = cursor.fetchall()

    # if data is not None:
    followers_list = []
    for t in data:
        followers_list.append(t[0])

    cursor.execute("SELECT followee_email FROM Followers WHERE follower_email='" + user_email + "'")
    data = cursor.fetchall()

    # if data is not None:
    following_list = []
    for t in data:
        following_list.append(t[0])

    resp = {
        "email": user_email,
        "username": user_data[1],
        "about": new_user_about,
        "name": new_user_name,
        "isAnonymous": bool(user_data[2]),
        "id": user_data[0],
        "followers": followers_list,
        "following": following_list
    }

    return jsonify(code=0, response=resp)