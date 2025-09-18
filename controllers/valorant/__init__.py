from flask import Blueprint, render_template
from myfunc import url_for
import json

valorant = Blueprint(
	"valorant", 
	__name__, 
	static_folder="statics", 
	template_folder="templates"
)

@valorant.route("/")
def index():
	return "Valorant Controller Index"

@valorant.route("/vct")
def vct():
	return "Valorant Controller VCT"

@valorant.route("/vct/<int:year>/champions")
def vct_year(year):
	with open(f'controllers{url_for("valorant.static", filename=f"vct/{year}.json")}', encoding="utf-8") as f:
		data = json.load(f)
	with open(f'controllers{url_for("valorant.static", filename="vct/teams.json")}', encoding="utf-8") as f:
		teams = json.load(f)
	name = f"valorant champions {data['champions']}".upper()
	data = data["tournament"][f"champions {data['champions']}"]
	return render_template("valorant/champions.html", name=name, tournament=data, teams=teams)

@valorant.route("/vct/<int:year>/champions/pickem")
def pickem(year):
	with open(f'controllers{url_for("valorant.static", filename=f"vct/pick\'em.json")}', encoding="utf-8") as f:
		data = json.load(f)
	with open(f'controllers{url_for("valorant.static", filename="vct/teams.json")}', encoding="utf-8") as f:
		teams = json.load(f)
	name = f"valorant champions {data['champions']}".upper()
	data = data["tournament"][f"champions {data['champions']}"]
	return render_template("valorant/champions.html", name=name, tournament=data, teams=teams)