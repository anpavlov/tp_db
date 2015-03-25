from ext import mysql, user_exists, thread_exists, user_details, forum_details, thread_details as thread_detail, forum_exists
from flask import request, jsonify, Blueprint
from werkzeug.exceptions import BadRequest
from datetime import datetime

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

        for el in related_list:
            if el != 'forum' and el != 'user':
                return jsonify(code=3, response="Wrong parameters")

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


@thread_api.route('/list/', methods=['GET'])
def thread_list():
    req_params = request.args

    if not ('forum' in req_params or 'user' in req_params) or 'forum' in req_params and 'user' in req_params:
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
        entity = req_params['user']
        if not user_exists(cursor, entity):
            return jsonify(code=1, response="No user with such email!")

    query = "SELECT id, forum, user, title, message, slug, DATE_FORMAT(date,'%%Y-%%m-%%d %%T') d, " \
            "isClosed, isDeleted, posts, likes, dislikes, points FROM Thread " \
            "WHERE date>=%s AND "
    query += "forum" if is_by_forum else "user"
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
            "user": t[2],
            "title": t[3],
            "message": t[4],
            "slug": t[5],
            "date": t[6],
            "isClosed": bool(t[7]),
            "isDeleted": bool(t[8]),
            "posts": t[9],
            "likes": t[10],
            "dislikes": t[11],
            "points": t[12]
        }
        resp.append(post)

    return jsonify(code=0, response=resp)


@thread_api.route('/listPosts/', methods=['GET'])
def thread_list_posts():
    req_params = request.args

    if not ('thread' in req_params):
        return jsonify(code=3, response="Wrong parameters")

    thread = req_params['thread']
    try:
        thread = int(thread)
    except ValueError:
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

    if "sort" in req_params:
        sort = req_params['sort']
        if sort != 'flat' and sort != 'tree' and sort != 'parent_tree':
            return jsonify(code=3, response="Wrong parameters")
    else:
        sort = 'flat'

    conn = mysql.get_db()
    cursor = conn.cursor()

    if not thread_exists(cursor, thread):
        return jsonify(code=1, response="No thread with such id!")

    if sort == 'flat':
        # flat
        query = "SELECT id, forum, user, parent, message, DATE_FORMAT(date,'%%Y-%%m-%%d %%T') d," \
                "isApproved, isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points FROM Post " \
                "WHERE date>=%s AND thread=%s ORDER BY d "
        query += order
        query += " LIMIT %s" if limit is not None else ""
        sql_data = (since, thread, limit) if limit is not None else (since, thread)

        cursor.execute(query, sql_data)
        data = cursor.fetchall()

    elif sort == 'tree':
        #  tree
        if order == 'asc':
            # tree -> asc
            query = "SELECT id, forum, user, parent, message, DATE_FORMAT(date,'%%Y-%%m-%%d %%T') d," \
                    "isApproved, isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points FROM Post " \
                    "WHERE date>=%s AND thread=%s ORDER BY path ASC"
            query += " LIMIT %s" if limit is not None else ""
            sql_data = (since, thread, limit) if limit is not None else (since, thread)

            cursor.execute(query, sql_data)
            data = cursor.fetchall()
        else:
            # tree -> desc
            query = "SELECT id, forum, user, parent, message, DATE_FORMAT(date,'%%Y-%%m-%%d %%T') d," \
                    "isApproved, isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points, path, childrenAmnt FROM Post " \
                    "WHERE date>=%s AND thread=%s AND parent IS NULL ORDER BY path DESC"
            query += " LIMIT %s" if limit is not None else ""
            sql_data = (since, thread, limit) if limit is not None else (since, thread)

            cursor.execute(query, sql_data)
            roots = cursor.fetchall()
            data = []
            if limit is not None:
                # tree -> desc -> limit
                posts = 0
                for root in roots:
                    if posts < limit:
                        data.append(root)
                        posts += 1
                        if posts < limit:
                            parent_path = root[14] + '.%'
                            query = "SELECT id, forum, user, parent, message, DATE_FORMAT(date,'%%Y-%%m-%%d %%T') d," \
                                    "isApproved, isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points FROM Post " \
                                    "WHERE path LIKE %s ORDER BY path ASC LIMIT %s"
                            sql_data = (parent_path, limit)
                            cursor.execute(query, sql_data)
                            children = cursor.fetchall()
                            for child in children:
                                if posts < limit:
                                    data.append(child)
                                    posts += 1
            else:
                # tree -> desc -> no limit
                for p in roots:
                    data.append(p)
                    parent_path = p[14] + '.%'
                    query = "SELECT id, forum, user, parent, message, DATE_FORMAT(date,'%%Y-%%m-%%d %%T') d," \
                            "isApproved, isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points FROM Post " \
                            "WHERE path LIKE %s ORDER BY path ASC"
                    sql_data = (parent_path,)
                    cursor.execute(query, sql_data)
                    data2 = cursor.fetchall()
                    for p1 in data2:
                        data.append(p1)

    else:
        # parent_tree
        query = "SELECT id, forum, user, parent, message, DATE_FORMAT(date,'%%Y-%%m-%%d %%T') d," \
                "isApproved, isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points, path FROM Post " \
                "WHERE date>=%s AND thread=%s AND parent IS NULL ORDER BY d "
        query += order
        query += " LIMIT %s" if limit is not None else ""
        sql_data = (since, thread, limit) if limit is not None else (since, thread)
        cursor.execute(query, sql_data)
        data1 = cursor.fetchall()
        data = []
        for p in data1:
            data.append(p)
            parent_path = p[14] + '.%'
            query = "SELECT id, forum, user, parent, message, DATE_FORMAT(date,'%%Y-%%m-%%d %%T') d," \
                    "isApproved, isHighlighted, isEdited, isSpam, isDeleted, likes, dislikes, points FROM Post " \
                    "WHERE path LIKE %s ORDER BY path ASC"
            sql_data = (parent_path,)
            cursor.execute(query, sql_data)
            data2 = cursor.fetchall()
            for p1 in data2:
                data.append(p1)

    resp = []
    for p in data:
        post = {
            "id": p[0],
            "forum": p[1],
            "thread": thread,
            "user": p[2],
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

    if data[0] == 0:
        cursor.execute("UPDATE Thread SET isClosed=TRUE WHERE id=%s", (thread_id,))
        conn.commit()

    resp = {
        "thread": thread_id
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/open/', methods=['POST'])
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

    if data[0] == 1:
        cursor.execute("UPDATE Thread SET isClosed=FALSE WHERE id=%s", (thread_id,))
        conn.commit()

    resp = {
        "thread": thread_id
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/remove/', methods=['POST'])
def thread_remove():
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

    if data[0] == 0:
        cursor.execute("UPDATE Thread SET isDeleted=1, posts=0 WHERE id=%s", (thread_id,))
        cursor.execute("UPDATE Post SET isDeleted=1 WHERE thread=%s", (thread_id,))
        conn.commit()

    resp = {
        "thread": thread_id
    }

    return jsonify(code=0, response=resp)


@thread_api.route('/restore/', methods=['POST'])
def thread_restore():
    # TODO: (?) restore all posts
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

    if data[0] == 1:
        cursor.execute("UPDATE Thread SET isDeleted=0, posts=(SELECT COUNT(*) FROM Post WHERE thread=%s) WHERE id=%s",
                       (thread_id, thread_id))
        cursor.execute("UPDATE Post SET isDeleted=0 WHERE thread=%s", (thread_id,))
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
    cursor.execute("UPDATE Thread SET message=%s, slug=%s WHERE id=%s", sql_data)
    conn.commit()

    resp = thread_detail(cursor, thread_id)

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

    resp = thread_detail(cursor, thread_id)

    return jsonify(code=0, response=resp)