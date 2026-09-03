from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS

import os, json

app = Flask(__name__)
app.json.ensure_ascii = False
CORS(app, resources={
	r"/api/valorant/team-shuffle/.*": {
		"origins": [
			origin.strip() for origin in os.getenv(
				"TEAM_SHUFFLE_ALLOWED_ORIGINS", "https://yamato080915.github.io"
			).split(",") if origin.strip()
		],
		"methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
		"allow_headers": ["Content-Type", "Authorization"],
		"supports_credentials": False
	},
	r"/.*": {"origins": "*"}
})

from config import main
app.config.from_object(main)
if os.getenv("FLASK_DEBUG"):
	config_ = os.environ
else:
	with open("/home/yamato0915/yamato0915.xsrv.jp/steam.env", "r", encoding="utf-8") as f:
		config_ = json.load(f)
app.config["SECRET_KEY"] = config_["SECRET_KEY"]
app.config["MAIL_SERVER"] = config_["MAIL_SERVER"]
app.config["MAIL_PORT"] = config_["MAIL_PORT"]
app.config["MAIL_USE_TLS"] = config_["MAIL_USE_TLS"]
app.config["MAIL_USERNAME"] = config_["MAIL_USERNAME"]
app.config["MAIL_PASSWORD"] = config_["MAIL_PASSWORD"]
app.config["MAIL_DEFAULT_SENDER"] = config_["MAIL_DEFAULT_SENDER"]
app.config["SQLALCHEMY_DATABASE_URI"] = config_["SQLALCHEMY_DATABASE_URI"]
app.config["OPENAI_API_KEY"] = config_["OPENAI_API_KEY"]

db = SQLAlchemy()

db.init_app(app)
Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)

mail = Mail(app)

from myfunc import url_for, get_username, format_datetime, rank, keys, values, enmrt, max_key, min_key, team_region
app.jinja_env.globals["url_for"] = url_for
app.jinja_env.globals["get_username"] = get_username
app.jinja_env.globals["format_datetime"] = format_datetime
app.jinja_env.globals["rank"] = rank
app.jinja_env.globals["keys"] = keys
app.jinja_env.globals["values"] = values
app.jinja_env.globals["enumerate"] = enmrt
app.jinja_env.globals["max_key"] = max_key
app.jinja_env.globals["min_key"] = min_key
app.jinja_env.globals["team_region"] = team_region

import www
