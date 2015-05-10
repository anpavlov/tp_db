from ext import mysql, user_exists, forum_exists, thread_exists,\
    post_exists, user_details, forum_details, thread_details, post_details as post_detail
from flask import request, jsonify, Blueprint
from werkzeug.exceptions import BadRequest
from datetime import datetime

post_api = Blueprint('post_api', __name__)


@post_api.route('/create/', methods=['POST'])
def post_create():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('date' in req_json and 'thread' in req_json and 'message' in req_json
            and 'user' in req_json and 'forum' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    new_post_forum = req_json['forum']
    new_post_thread = req_json['thread']
    new_post_user = req_json['user']
    new_post_date = req_json['date']
    new_post_message = req_json['message']

    if 'isApproved' in req_json:
        if req_json['isApproved'] is not False and req_json['isApproved'] is not True:
            return jsonify(code=3, response="Wrong parameters")
        new_post_is_approved = req_json['isApproved']
    else:
        new_post_is_approved = False

    if 'isHighlighted' in req_json:
        if req_json['isHighlighted'] is not False and req_json['isHighlighted'] is not True:
            return jsonify(code=3, response="Wrong parameters")
        new_post_is_highlighted = req_json['isHighlighted']
    else:
        new_post_is_highlighted = False

    if 'isEdited' in req_json:
        if req_json['isEdited'] is not False and req_json['isEdited'] is not True:
            return jsonify(code=3, response="Wrong parameters")
        new_post_is_edited = req_json['isEdited']
    else:
        new_post_is_edited = False

    if 'isSpam' in req_json:
        if req_json['isSpam'] is not False and req_json['isSpam'] is not True:
            return jsonify(code=3, response="Wrong parameters")
        new_post_is_spam = req_json['isSpam']
    else:
        new_post_is_spam = False

    if 'isDeleted' in req_json:
        if req_json['isDeleted'] is not False and req_json['isDeleted'] is not True:
            return jsonify(code=3, response="Wrong parameters")
        new_post_is_deleted = req_json['isDeleted']
    else:
        new_post_is_deleted = False

    if 'parent' in req_json:
        new_post_parent = req_json['parent']
    else:
        new_post_parent = None

    try:
        new_post_thread = int(new_post_thread)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.get_db()
    cursor = conn.cursor()

    if not user_exists(cursor, new_post_user):
        return jsonify(code=1, response="No user with such email!")

    if not forum_exists(cursor, new_post_forum):
        return jsonify(code=1, response="No forum with such short name!")

    if not thread_exists(cursor, new_post_thread):
        return jsonify(code=1, response="No thread with such id!")

    cursor.execute("SELECT 1 FROM Thread WHERE id=%s AND forum=%s", (new_post_thread, new_post_forum))
    data = cursor.fetchone()
    if data is None:
        return jsonify(code=3, response="No such thread in this forum")

    if new_post_parent is None:
        cursor.execute("SELECT posts FROM Thread WHERE id=%s", (new_post_thread,))
        posts_in_thread = int(cursor.fetchone()[0])
        new_post_path = '{0:011d}'.format(posts_in_thread + 1)
    else:
        try:
            new_post_parent = int(new_post_parent)
        except ValueError:
            return jsonify(code=3, response="Wrong parameters")
        if not post_exists(cursor, new_post_parent):
            return jsonify(code=1, response="No post with such id!")
        cursor.execute("SELECT childrenAmnt, path FROM Post WHERE id=%s", (new_post_parent,))
        data = cursor.fetchone()
        new_post_path = data[1] + '.' + '{0:011d}'.format(int(data[0]) + 1)
        cursor.execute("UPDATE Post SET childrenAmnt=childrenAmnt+1 WHERE id=%s", (new_post_parent,))
        conn.commit()

    sql_data = (new_post_forum, new_post_thread, new_post_user, new_post_parent, new_post_path,
                new_post_message, new_post_date, new_post_is_approved, new_post_is_highlighted,
                new_post_is_edited, new_post_is_spam, new_post_is_deleted)
    #                                                              V - children amount
    cursor.execute("INSERT INTO Post VALUES (null, %s, %s, %s, %s, 0, %s, %s, %s, %s, %s, %s, %s, %s, 0, 0, 0)",
                   sql_data)
    new_post_id = cursor.lastrowid
    cursor.execute("UPDATE Thread SET posts=posts+1 WHERE id=%s", (new_post_thread,))
    conn.commit()

    resp = {
        "date": new_post_date,
        "forum": new_post_forum,
        "id": new_post_id,
        "isApproved": new_post_is_approved,
        "isHighlighted": new_post_is_highlighted,
        "isEdited": new_post_is_edited,
        "isSpam": new_post_is_spam,
        "isDeleted": new_post_is_deleted,
        "message": new_post_message,
        "parent": new_post_parent,
        "thread": new_post_thread,
        "user": new_post_user
    }

    return jsonify(code=0, response=resp)


@post_api.route('/details/', methods=['GET'])
def post_details():
    req_params = request.args

    if not ('post' in req_params):
        return jsonify(code=3, response="Wrong parameters")

    post_id = req_params['post']
    try:
        post_id = int(post_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute("""SELECT forum, thread, user, parent, message, DATE_FORMAT(date,'%%Y-%%m-%%d %%T'),
                      isApproved, isHighlighted, isEdited, isSpam, isDeleted, likes,
                      dislikes, points FROM Post WHERE id=%s""", (post_id,))
    data = cursor.fetchone()
    if data is None:
        return jsonify(code=1, response="No post with such id!")

    if 'related' in req_params:
        related_list = request.args.getlist('related')

        for el in related_list:
            if el != 'forum' and el != 'user' and el != 'thread':
                return jsonify(code=3, response="Wrong parameters")

        if 'forum' in related_list:
            forum_info = forum_details(cursor, data[0])
        else:
            forum_info = data[0]

        if 'thread' in related_list:
            thread_info = thread_details(cursor, data[1])
        else:
            thread_info = data[1]

        if 'user' in related_list:
            user_info = user_details(cursor, data[2])
        else:
            user_info = data[2]

    else:
        forum_info = data[0]
        thread_info = data[1]
        user_info = data[2]

    resp = {
        "id": post_id,
        "forum": forum_info,
        "thread": thread_info,
        "user": user_info,
        "parent": data[3],
        "message": data[4],
        "date": data[5],
        "isApproved": bool(data[6]),
        "isHighlighted": bool(data[7]),
        "isEdited": bool(data[8]),
        "isSpam": bool(data[9]),
        "isDeleted": bool(data[10]),
        "likes": data[11],
        "dislikes": data[12],
        "points": data[13]
    }
    return jsonify(code=0, response=resp)


@post_api.route('/list/', methods=['GET'])
def post_list():
    req_params = request.args

    if not ('forum' in req_params or 'thread' in req_params) or 'forum' in req_params and 'thread' in req_params:
        return jsonify(code=3, response="Wrong parameters")

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

    is_by_forum = 'forum' in req_params
    if is_by_forum:
        entity = req_params['forum']
        if not forum_exists(cursor, entity):
            return jsonify(code=1, response="No forum with such short name!")
    else:
        entity = req_params['thread']
        try:
            entity = int(entity)
        except ValueError:
            return jsonify(code=3, response="Wrong parameters")
        if not thread_exists(cursor, entity):
            return jsonify(code=1, response="No thread with such id!")

    query = "SELECT id, forum, thread, user, parent, message, DATE_FORMAT(date,'%%Y-%%m-%%d %%T') d," \
            "isApproved, isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points FROM Post " \
            "WHERE date>=%s AND "
    query += "forum" if is_by_forum else "thread"
    query += "=%s ORDER BY d "
    query += order
    query += " LIMIT %s" if limit is not None else ""

    sql_data = (since, entity, limit) if limit is not None else (since, entity)

    cursor.execute(query, sql_data)

    data = cursor.fetchall()

    resp = []
    for t in data:
        post = {
            "id": t[0],
            "forum": t[1],
            "thread": t[2],
            "user": t[3],
            "parent": t[4],
            "message": t[5],
            "date": t[6],
            "isApproved": bool(t[7]),
            "isHighlighted": bool(t[8]),
            "isEdited": bool(t[9]),
            "isSpam": bool(t[10]),
            "isDeleted": bool(t[11]),
            "likes": t[12],
            "dislikes": t[13],
            "points": t[14]
        }
        resp.append(post)

    return jsonify(code=0, response=resp)


@post_api.route('/remove/', methods=['POST'])
def post_remove():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('post' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    post_id = req_json['post']
    try:
        post_id = int(post_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT thread FROM Post WHERE id=%s", (post_id,))
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No post with such id!")

    # if data[0] == 0:
    cursor.execute("UPDATE Post SET isDeleted=1 WHERE id=%s", (post_id,))
    cursor.execute("UPDATE Thread SET posts=posts-1 WHERE id=%s", (data[0],))
    conn.commit()

    resp = {
        "post": post_id
    }

    return jsonify(code=0, response=resp)


@post_api.route('/restore/', methods=['POST'])
def post_restore():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('post' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    post_id = req_json['post']
    try:
        post_id = int(post_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT thread FROM Post WHERE id=%s", (post_id,))
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No post with such id!")

    # if data[0] == 1:
    cursor.execute("UPDATE Post SET isDeleted=0 WHERE id=%s", (post_id,))
    cursor.execute("UPDATE Thread SET posts=posts+1 WHERE id=%s", (data[0],))
    conn.commit()

    resp = {
        "post": post_id
    }

    return jsonify(code=0, response=resp)


@post_api.route('/update/', methods=['POST'])
def post_update():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('post' in req_json and 'message' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    post_id = req_json['post']
    try:
        post_id = int(post_id)
    except ValueError:
        return jsonify(code=3, response="Wrong parameters")

    new_post_message = req_json['message']

    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute("""SELECT forum, thread, user, parent, DATE_FORMAT(date,'%%Y-%%m-%%d %%T'),
                      isApproved, isHighlighted, isEdited, isSpam, isDeleted, likes,
                      dislikes, points FROM Post WHERE id=%s""", (post_id,))
    data = cursor.fetchone()

    if data is None:
        return jsonify(code=1, response="No post with such id!")

    cursor.execute("UPDATE Post SET message=%s WHERE id=%s", (new_post_message, post_id))
    conn.commit()

    resp = {
        "id": post_id,
        "forum": data[0],
        "thread": data[1],
        "user": data[2],
        "parent": data[3],
        "message": new_post_message,
        "date": data[4],
        "isApproved": bool(data[5]),
        "isHighlighted": bool(data[6]),
        "isEdited": bool(data[7]),
        "isSpam": bool(data[8]),
        "isDeleted": bool(data[9]),
        "likes": data[10],
        "dislikes": data[11],
        "points": data[12]
    }

    return jsonify(code=0, response=resp)


@post_api.route('/vote/', methods=['POST'])
def post_vote():
    try:
        req_json = request.get_json()
    except BadRequest:
        return jsonify(code=2, response="Cant parse json")

    if not ('post' in req_json and 'vote' in req_json):
        return jsonify(code=3, response="Wrong parameters")

    post_id = req_json['post']
    try:
        post_id = int(post_id)
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

    if not post_exists(cursor, post_id):
        return jsonify(code=1, response="No post with such id!")

    if vote == 1:
        cursor.execute("UPDATE Post SET likes=likes+1 WHERE id=%s", (post_id,))
    else:
        cursor.execute("UPDATE Post SET dislikes=dislikes+1 WHERE id=%s", (post_id,))

    cursor.execute("UPDATE Post SET points=points+%s WHERE id=%s", (vote, post_id))
    conn.commit()

    resp = post_detail(cursor, post_id)

    return jsonify(code=0, response=resp)