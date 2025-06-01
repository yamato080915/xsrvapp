from app import app, login_manager
from models import User
from flask import render_template

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from controllers import home
app.register_blueprint(home, url_prefix="/")

from controllers.steam import steam
app.register_blueprint(steam, url_prefix="/steam")

from controllers.account import account
app.register_blueprint(account, url_prefix="/")

from controllers.math import math
app.register_blueprint(math, url_prefix="/math")

login_manager.blueprint_login_views = {
	"account": "login",
	"steam": "account.login",
    "math": "account.login"
}

@app.errorhandler(400)
def bad_request(e):
    return render_template("error/400.html"), 400

@app.errorhandler(401)
def unauthorized(e):
    return render_template("error/401.html"), 401

@app.errorhandler(403)
def forbidden(e):
    return render_template("error/403.html"), 403

@app.errorhandler(404)
def not_found(e):
    return render_template("error/404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error/500.html"), 500