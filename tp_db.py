from flask import Flask

app = Flask(__name__)

# app.config["APPLICATION_ROOT"] = "/db/api"
app.config['MYSQL_DATABASE_USER'] = 'tp_db_user'
app.config['MYSQL_DATABASE_PASSWORD'] = 'qwe123'
app.config['MYSQL_DATABASE_DB'] = 'tp_db'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

from ext import mysql

mysql.init_app(app)

from api.user import user_api

app.register_blueprint(user_api, url_prefix='/db/api/user')


@app.route('/')
def hello_world():
    a = 5
    txt = "asfasda"
    return 'Hello World!'


@app.route('/a')
def a():
    conn = mysql.connect()
    cursor = conn.cursor()
    # cursor.execute("insert into tbl values (null,'abcsa')")
    cursor.execute("create table tbl2 ( id1 int PRIMARY KEY AUTO_INCREMENT, field1 varchar(10) )")
    # conn.commit()

    # data = cursor.fetchone()
    return 'aHello World!'


@app.route('/b')
def b():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("insert into tbl2 values (null,'abcsa')")
    # cursor.execute("create table tbl2 ( id1 int PRIMARY KEY AUTO_INCREMENT, field1 varchar(10) )")
    conn.commit()
    # data = cursor.fetchone()
    return 'bHello World!'


@app.route('/t')
def t():
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("truncate tbl2")
    # cursor.execute("create table tbl2 ( id1 int PRIMARY KEY AUTO_INCREMENT, field1 varchar(10) )")
    # conn.commit()
    # data = cursor.fetchone()
    return 'tHello World!'


if __name__ == '__main__':
    app.run(debug=True)