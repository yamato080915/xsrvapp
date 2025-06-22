from flask import Blueprint, render_template, jsonify, abort
from flask_login import login_required, current_user
import json
from functools import wraps
from datetime import datetime

from models import User, MathProblems, Submissions, Question
from app import db

home = Blueprint("home", __name__, static_folder="static", template_folder="templates")

def admin_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if not(current_user.is_authenticated):
			abort(401)
		if not current_user.is_admin:
			abort(403)
		return f(*args, **kwargs)
	return decorated_function

def get(file):
	with open(file, "r", encoding="utf-8") as f:
		data = f.read()
		data = json.loads(data)

	data = [x for x in data if x["IsRated"]]
	for i in data:
		i["Place"] = str(i["Place"])
		dt = datetime.fromisoformat(i["EndTime"])
		i["EndTime"] = f"{dt.year}/{dt.month}/{dt.day}"
		if i["NewRating"]<400:i["Rank"]="gray"
		elif i["NewRating"]<800:i["Rank"]="brown"
		elif i["NewRating"]<1200:i["Rank"]="green"
		elif i["NewRating"]<1600:i["Rank"]="cyan"
		elif i["NewRating"]<2000:i["Rank"]="blue"
		elif i["NewRating"]<2400:i["Rank"]="yellow"
		elif i["NewRating"]<2800:i["Rank"]="orange"
		else:i["Rank"]="red"
		if not "ContestScreenName" in i.keys():
			i["ContestScreenName"] = i["ContestName"]
	return data

@home.route("/")
def index():
	atcoder = get("./atcoder.json")
	omc = get("./omc.json")
	return render_template("home.html", atcoder=atcoder, omc=omc)

@home.route("/api/atcoder/rating")
def AtcoderRating():
	data = get("./atcoder.json")
	return jsonify(data)

@home.route("/api/omc/rating")
def omcRating():
	data = get("./omc.json")
	return jsonify(data)

def get_database(table, id=None):
	if table=="User":
		TABLE = User
	elif table=="MathProblems":
		TABLE = MathProblems
	elif table=="Submissions":
		TABLE = Submissions
	elif table=="Question":
		TABLE = Question
	else:
		abort(404)
	if id is not None:
		record = db.session.query(TABLE).get(id)
		if record is None:
			abort(404)
		return record.to_dict()
	else:
		return [x.to_dict() for x in db.session.query(TABLE).all()]

@home.route("/db/<tablename>")
@admin_required
def database(tablename):
	data = get_database(tablename)
	return jsonify(data)

@home.route("/db/<tablename>/<int:id>")
@admin_required
def database_id(tablename, id):
	data = get_database(tablename, id)
	return jsonify(data)

@home.route("/db/<tablename>/<int:id>/update")
@admin_required
def updater(tablename, id):
	data = get_database(tablename, id)
	return render_template("update.html", data=data, keys=list(data.keys()))