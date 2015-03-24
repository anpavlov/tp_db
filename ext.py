from flaskext.mysql import MySQL

mysql = MySQL()
posts = 0


def tuple_of_users_to_arr(data):
    users = []
    for user in data:
        user_map = {
            "id": user[0],
            "about": user[1],
            "email": user[2],
            "isAnonymous": bool(user[3]),
            "name": user[4],
            "username": user[5],
        }
        users.append(user_map)
    return users


def user_exists(cursor, email):
    cursor.execute("SELECT 1 FROM User WHERE email=%s", (email,))
    data = cursor.fetchone()

    return False if data is None else True


def forum_exists(cursor, forum):
    cursor.execute("SELECT 1 FROM Forum WHERE short_name=%s", (forum,))
    data = cursor.fetchone()

    return False if data is None else True


def thread_exists(cursor, thread_id):
    cursor.execute("SELECT 1 FROM Thread WHERE id=%s", (thread_id,))
    data = cursor.fetchone()

    return False if data is None else True


def post_exists(cursor, post_id):
    cursor.execute("SELECT 1 FROM Post WHERE id=%s", (post_id,))
    data = cursor.fetchone()

    return False if data is None else True


def user_details(cursor, email):
    cursor.execute("SELECT * FROM User WHERE email=%s", (email,))
    user_data = cursor.fetchone()

    if user_data is None:
        return None

    follow_info = get_followers(cursor, email)
    subs_list = get_subs(cursor, email)

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
    return resp


def get_followers(cursor, user_email):
    cursor.execute("SELECT follower_email FROM Followers WHERE followee_email=%s", (user_email,))
    data = cursor.fetchall()

    followers_list = []
    for t in data:
        followers_list.append(t[0])

    cursor.execute("SELECT followee_email FROM Followers WHERE follower_email=%s", (user_email,))
    data = cursor.fetchall()

    following_list = []
    for t in data:
        following_list.append(t[0])

    return {'followers': followers_list, 'following': following_list}


def get_subs(cursor, user_email):
    cursor.execute("SELECT thread FROM Subscriptions WHERE user=%s", (user_email,))
    data = cursor.fetchall()

    subs_list = []
    for s in data:
        subs_list.append(s[0])

    return subs_list


def forum_details(cursor, forum_short_name):
    cursor.execute("SELECT * FROM Forum WHERE short_name=%s", (forum_short_name,))
    data = cursor.fetchone()

    resp = {
        "id": data[0],
        "name": data[1],
        "short_name": data[2],
        "user": data[3]
    }
    return resp


def thread_details(cursor, thread_id):
    cursor.execute("SELECT forum, user, title, message, slug, DATE_FORMAT(date,'%%Y-%%m-%%d %%T'),"
                   "isClosed, isDeleted, posts, likes, dislikes, points FROM Thread WHERE id=%s", (thread_id,))
    data = cursor.fetchone()

    resp = {
        "id": thread_id,
        "forum": data[0],
        "user": data[1],
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

    return resp


def post_details(cursor, post_id):
    cursor.execute("""SELECT forum, thread, user, parent, message, DATE_FORMAT(date,'%%Y-%%m-%%d %%T'),
                      isApproved, isHighlighted, isEdited, isSpam, isDeleted, likes,
                      dislikes, points FROM Post WHERE id=%s""", (post_id,))
    data = cursor.fetchone()

    resp = {
        "id": post_id,
        "forum": data[0],
        "thread": data[1],
        "user": data[2],
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

    return resp