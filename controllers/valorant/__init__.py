from flask import Blueprint, render_template, make_response, send_file
from myfunc import url_for
import json, os

valorant = Blueprint(
	"valorant", 
	__name__, 
	static_folder="statics", 
	template_folder="templates"
)
@valorant.route("/manifest.json")
def manifest():
	return send_file("controllers/valorant/statics/manifest.json", mimetype="application/manifest+json")

@valorant.route("/fonts/<font>")
def serve_fonts(font):
	if font in ["Foundry-Gridnik-ExtraBold.otf", "valorant.ttf"]:
		response = make_response(valorant.send_static_file(f"fonts/{font}"))
		response.headers["Cache-Control"] = 'public, max-age=31536000'
		return response

@valorant.route("/icons/<team>")
def serve_icons(team:str):
	if team.upper() == "VCT":
		response = make_response(valorant.send_static_file("vct/icons/vct.png"))
		response.headers["Cache-Control"] = 'public, max-age=31536000'
		return response
	elif f"{team.upper()}.png" in os.listdir("controllers/valorant/statics/vct/icons"):
		response = make_response(valorant.send_static_file(f"vct/icons/{team.upper()}.png"))
		response.headers["Cache-Control"] = 'public, max-age=31536000'
		return response

@valorant.route("/vct/<int:year>/champions")
def champions(year):
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