from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail

import os, json

app = Flask(__name__)
app.json.ensure_ascii = False

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

db = SQLAlchemy()

db.init_app(app)
Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)

mail = Mail(app)

import www