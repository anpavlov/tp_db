import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request
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

logging.basicConfig(filename='logs/tp_db_app.log', level=logging.INFO)
#
# usersLog = logging.getLogger('usersLog')
# fh = logging.FileHandler('logs/users.log')
# fh.setLevel(logging.INFO)
# fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))
# usersLog.addHandler(fh)
#
# emailLog = logging.getLogger('emailLog')
# fh2 = logging.FileHandler('logs/emails.log')
# fh2.setLevel(logging.INFO)
# fh2.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))
# emailLog.addHandler(fh2)
#

postLog = logging.getLogger('postLog')
fh2 = logging.FileHandler('logs/emails.log')
fh2.setLevel(logging.INFO)
fh2.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))
postLog.addHandler(fh2)

reqLog = logging.getLogger('reqLog')
rfh = RotatingFileHandler('logs/request.log', maxBytes=50000000, backupCount=5)
rfh.setLevel(logging.INFO)
rfh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))

reqLog.addHandler(rfh)
raise ValueError

@app.after_request
def aft(response):
    reqLog.info('Returning %s', response.data)
    return response


@app.before_request
def pre():
    reqLog.info('Request to %s with', request.url)
    reqLog.info('%s', request.data)


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


@app.route('/db/api/status/', methods=['GET'])
def status():
    conn = mysql.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Post")
    posts = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Thread")
    threads = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Forum")
    forums = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM User")
    users = cursor.fetchone()[0]

    resp = {
        "post": posts,
        "thread": threads,
        "forum": forums,
        "user": users
    }

    return jsonify(code=0, response=resp)

if __name__ == '__main__':
    app.run(debug=True)