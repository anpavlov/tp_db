from flask import Flask, jsonify
from ext import mysql

from api.user import user_api
from api.forum import forum_api
from api.post import post_api
from api.thread import thread_api

app = Flask(__name__)

# app.config["APPLICATION_ROOT"] = "/db/api"
app.config['MYSQL_DATABASE_USER'] = 'tp_db_user'
app.config['MYSQL_DATABASE_PASSWORD'] = 'qwe123'
app.config['MYSQL_DATABASE_DB'] = 'tp_db'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql.init_app(app)

app.register_blueprint(user_api, url_prefix='/db/api/user')
app.register_blueprint(forum_api, url_prefix='/db/api/forum')
app.register_blueprint(post_api, url_prefix='/db/api/post')
app.register_blueprint(thread_api, url_prefix='/db/api/thread')


@app.route('/db/api/clear/', methods=['POST'])
def clear():
    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute("SET foreign_key_checks = 0")
    cursor.execute("TRUNCATE TABLE Post")
    cursor.execute("TRUNCATE TABLE Subscriptions")
    cursor.execute("TRUNCATE TABLE Thread")
    cursor.execute("TRUNCATE TABLE Forum")
    cursor.execute("TRUNCATE TABLE Followers")
    cursor.execute("TRUNCATE TABLE User")
    cursor.execute("SET foreign_key_checks = 1")
    return jsonify(code=0, response="OK")

if __name__ == '__main__':
    app.run(debug=True)