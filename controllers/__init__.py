from flask import Blueprint, render_template, jsonify
import json
from datetime import datetime

home = Blueprint("home", __name__, static_folder="static", template_folder="templates")

def get():
	with open("./atcoder.json", "r", encoding="utf-8") as f:
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
	return data

@home.route("/")
def index():
	data = get()
	return render_template("home.html", data=data)

@home.route(f"/api/rating")
def ApiRating():
	data = get()
	return jsonify(data)