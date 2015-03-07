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
