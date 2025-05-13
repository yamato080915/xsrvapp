from app import app, login_manager

from controllers import home
app.register_blueprint(home, url_prefix="/")

from controllers.steam import steam
app.register_blueprint(steam, url_prefix="/steam")

from controllers.account import account
app.register_blueprint(account, url_prefix="/")

from controllers.math import math
app.register_blueprint(math, url_prefix="/math")

login_manager.blueprint_login_views = {
	"steam": "account.login",
	"account": "login"
}