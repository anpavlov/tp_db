from flaskext.mysql import MySQL

mysql = MySQL()


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


def user_details(email):
    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM User WHERE email='" + email + "'")
    user_data = cursor.fetchone()

    if user_data is None:
        return None

    cursor.execute("SELECT follower_email FROM Followers WHERE followee_email='" + email + "'")
    data = cursor.fetchall()

    followers_list = []
    for t in data:
        followers_list.append(t[0])

    cursor.execute("SELECT followee_email FROM Followers WHERE follower_email='" + email + "'")
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
    return resp