from flask import Blueprint, render_template, jsonify, abort, request, redirect, url_for
import json
from datetime import datetime

from models import User, MathProblems, Submissions, Question, Event
from app import db

home = Blueprint("home", __name__, static_folder="static", template_folder="templates")

from perm import admin_required

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

def get_database(table, id=None, dict=True):
	if table=="User":
		TABLE = User
	elif table=="MathProblems":
		TABLE = MathProblems
	elif table=="Submissions":
		TABLE = Submissions
	elif table=="Question":
		TABLE = Question
	elif table=="Event":
		TABLE = Event
	else:
		abort(404)
	if id is not None:
		record = db.session.query(TABLE).get(id)
		if record is None:
			abort(404)
		if dict:
			return [record.to_dict(), record.data_type()]
		else:
			return record
	else:
		return [x.to_dict() for x in db.session.query(TABLE).all()]

def update_database(table, id, form):
	data = get_database(table, id, False)
	if "email" in form:data.email = form["email"]
	if "user" in form:data.user = form["user"]
	if "title" in form:data.title = form["title"]
	if "content" in form:data.content = form["content"]
	if "explanation" in form:data.explanation = form["explanation"]
	if "category" in form:data.category = form["category"]
	if "unit" in form:data.unit = form["unit"]
	if "score" in form:data.score = form["score"]
	if "problem" in form:data.problem = form["problem"]
	if "judged" in form:data.judged = form["judged"]
	if "resolved" in form:data.resolved = form["resolved"]
	db.session.commit()

@home.route("/db/<tablename>")
@admin_required
def database(tablename):
	data = get_database(tablename)
	return jsonify(data)

@home.route("/db/<tablename>/<int:id>")
@admin_required
def database_id(tablename, id):
	data = get_database(tablename, id)[0]
	return jsonify(data)

@home.route("/db/<tablename>/<int:id>/update", methods=["GET", "POST"])
@admin_required
def updater(tablename, id):
	if request.method=="GET":
		data = get_database(tablename, id)
		return render_template("update.html", data=data[0], keys=list(data[0].keys()), data_type=data[1])
	else:
		data = update_database(tablename, id, request.form)
		return ""

@home.route("/db/<tablename>/<int:id>/delete")
@admin_required
def deleter(tablename, id):
	data = get_database(tablename, id, False)
	db.session.delete(data)
	db.session.commit()
	return redirect(url_for("home.database", tablename=tablename))