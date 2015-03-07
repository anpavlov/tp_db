from ext import mysql
from flask import request, jsonify, Blueprint
from werkzeug.exceptions import BadRequest

post_api = Blueprint('post_api', __name__)