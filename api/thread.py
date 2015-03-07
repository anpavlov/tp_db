from ext import mysql
from flask import request, jsonify, Blueprint
from werkzeug.exceptions import BadRequest

thread_api = Blueprint('thread_api', __name__)