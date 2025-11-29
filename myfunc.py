from flask import abort, url_for as flask_url_for
from flask_login import current_user
from functools import wraps
from datetime import datetime
import json

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

def rank(rating:int):
	if rating<400:return "gray"
	elif rating<800:return "brown"
	elif rating<1200:return "green"
	elif rating<1600:return "cyan"
	elif rating<2000:return "blue"
	elif rating<2400:return "yellow"
	elif rating<2800:return "orange"
	else:return "red"

def keys(d:dict):
	li = list(d.keys())
	if len(li)<=1:
		li=["TBD","TBD"]
	return li

def values(d:dict):
	return list(d.values())

def max_key(d:dict):
	return None if None in d.values() or d=={} else max(d, key=d.get)

def min_key(d:dict):
	return None if None in d.values() or d=={} else min(d, key=d.get)

def enmrt(list):
	return enumerate(list)

def team_region(team):
	with open('controllers/valorant/statics/vct/teams.json', encoding="utf-8") as f:
		teams = json.load(f)
	if team == "TBD":
		return "TBD"
	return "Pacific" if team in teams["Pacific"]["list"] else "EMEA" if team in teams["EMEA"]["list"] else "Americas" if team in teams["Americas"]["list"] else "China" if team in teams["China"]["list"] else None