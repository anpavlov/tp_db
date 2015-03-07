from ext import mysql
from flask import request, jsonify, Blueprint
from werkzeug.exceptions import BadRequest

forum_api = Blueprint('forum_api', __name__)