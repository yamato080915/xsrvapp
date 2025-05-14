from flask import Blueprint, render_template, jsonify
import json
from datetime import datetime

home = Blueprint("home", __name__, static_folder="static", template_folder="templates")

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
	return data

@home.route("/")
def index():
	atcoder = get("./atcoder.json")
	omc = get("./omc.json")
	return render_template("home.html", atcoder=atcoder, omc=omc)

@home.route(f"/api/atcoder/rating")
def AtcoderRating():
	data = get("./atcoder.json")
	return jsonify(data)

@home.route(f"api/omc/rating")
def omcRating():
	data = get("./omc.json")
	return jsonify(data)