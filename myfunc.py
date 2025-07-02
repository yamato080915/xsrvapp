from flask import abort, url_for as flask_url_for
from flask_login import current_user
from functools import wraps
from datetime import datetime

from models import User

def admin_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if not(current_user.is_authenticated):
			abort(401)
		if not current_user.is_admin:
			abort(403)
		return f(*args, **kwargs)
	return decorated_function

def url_for(endpoint, **values):
	url = flask_url_for(endpoint, **values)
	return url.replace("/index.cgi", "")

def get_username(user:int):
	return User.query.get(user).email.split("@")[0]

def format_datetime(date:datetime):
	return date.strftime("%Y/%m/%d %H:%M")