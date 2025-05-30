from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from email_validator import validate_email, EmailNotValidError
import random, os

from app import db, mail
from models import User, Auth
from www import load_user

account = Blueprint(
	"account", 
	__name__, 
	static_folder="static",
	template_folder="./templates"
)

@account.route("/register", methods=["GET", "POST"])
def register():
	global code
	if request.method=="POST" or (request.args.get("resend") and session["auth code"]):
		if "email" in request.form:
			email = request.form["email"]
			password = request.form["password"]

			flag = email==""
			try:validate_email(email)
			except EmailNotValidError:flag = True

			exists = User.query.filter_by(email=email).first()

			session["register_error"] = {
				"account_exists": True if exists else False,
				"email": " is-invalid" if flag else "", 
				"password": " is-invalid" if len(password)<10 else ""
			}
			session["register_email"] = email
			if session["register_error"]["account_exists"]:
				session.pop("register_email", None)
				session["register_error"]["email"] = " is-invalid"
			if not(session["register_error"]["email"] or session["register_error"]["password"] or session["register_error"]["account_exists"]):
				code = random.randint(100000, 999999)
				send_auth(email, code, password)
		elif request.args.get("resend"):
			code = random.randint(100000, 999999)
			send_auth(session["register_email"], code)
		else:
			auth = Auth.query.filter_by(email=session["register_email"]).first()
			if str(auth.authcode)==request.form["authcode"]:
				user = User(email=auth.email)
				user.password_hash = auth.password_hash
				db.session.add(user)
				db.session.query(Auth).filter_by(email=auth.email).delete()
				db.session.commit()
				session.pop("register_error", None)
				session.pop("register_email", None)
				session.pop("auth code", None)
				session.pop("auth error", None)
				return redirect(url_for("account.login").replace('index.cgi/', ''))
			else:
				session["auth error"] = " is-invalid"
	else:
		session.pop("auth code", None)
		session.pop("register_error", None)
		session.pop("register_email", None)
		session.pop("auth error", None)
	return render_template("account/register.html")

def send_auth(email, code, password=None):
	if Auth.query.filter_by(email=email).first() and password!=None:
		db.session.query(Auth).filter_by(email=email).delete()
		db.session.commit()
	msg = Message("Authcode", recipients=[email], sender="No-Reply@yamato0915.xsrv.jp")
	msg.body = f"Authcode = {code}"
	mail.send(msg)
	session["auth code"] = 1
	if password==None:
		user = db.session.query(Auth).filter_by(email=email).first()
		user.authcode = code
		db.session.add(user)
		db.session.commit()
	else:
		authcode = Auth(email=email)
		authcode.authcode = code
		if password:
			authcode.password = password
		db.session.add(authcode)
		db.session.commit()

@account.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		email = request.form["email"]
		password = request.form["password"]
		remember = "remember" in request.form

		flag = email==""
		try:validate_email(email)
		except EmailNotValidError:flag = True

		exists = User.query.filter_by(email=email).first()
		
		if exists and not(exists.verify_password(password)):
			flag = True

		session["login_error"] = " is-invalid" if flag or not(exists) else ""
		session["login_email"] = email
		if not(flag) and exists:
			session.pop("login_error", None)
			session.pop("login_email", None)
			login_user(exists, remember=remember)
			if request.args.get("next")==None or "logout" in request.args.get("next"):
				return redirect(url_for("home.index").replace('index.cgi/', ''))
			else:
				return redirect(request.args.get("next").replace('index.cgi/', ''))
	else:
		session.pop("login_email", None)
		session.pop("login_error", None)
	return render_template("account/login.html")

@account.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for("account.login").replace('index.cgi/', ''))

@account.route("/reset-password", methods=["GET", "POST"])
def forget():
	if request.method == "POST":
		if "email" in request.form:
			email = request.form["email"]
			flag = email==""
			try:validate_email(email)
			except EmailNotValidError:flag=True
			exists = User.query.filter_by(email=email).first()
			session["reset"] = {
				"valid": " is-invalid" if flag else "",
				"exists": "" if exists else " is-invalid", 
				"email": email}
			if not(" is-invalid" in session["reset"].values()):
				code = os.urandom(5).hex()
				send_auth(email, code, False)
		else:
			auth = Auth.query.filter_by(email=session["reset"]["email"]).first()
			session["reset"] = {
				"valid": " is-invalid" if str(auth.authcode)!=request.form["authcode"] else "",
				"pswd": " is-invalid" if len(request.form["newpswd"])<9 else "",
				"email": session["reset"]["email"]
			}
			if not " is-invalid" in session["reset"].values():
				user = db.session.query(User).filter_by(email=session["reset"]["email"]).first()
				user.password = request.form["newpswd"]
				db.session.add(user)
				db.session.commit()
				session.pop("reset", None)
				session.pop("auth code", None)
				print(session)
				return redirect(url_for("account.login").replace('index.cgi/', ''))
	else:
		session.pop("reset", None)
		session.pop("auth code", None)
	return render_template("account/forget.html")

@account.route("/account", methods=["GET", "POST"], endpoint="account")
@login_required
def account_view():
	if request.method == "POST":
		if "oldpswd" in request.form:
			oldpswd = request.form["oldpswd"]
			newpswd = request.form["newpswd"]
			user = User.query.get(current_user.get_id())
			session["chpswd_error"] = {
				"old": " is-invalid" if not(user.verify_password(oldpswd)) else "",
				"new": " is-invalid" if len(newpswd)<10 else ""
			}
			if not(session["chpswd_error"]["old"] or session["chpswd_error"]["new"]):
				user = db.session.query(User).filter_by(id=current_user.get_id()).first()
				user.password = newpswd
				db.session.add(user)
				db.session.commit()
				session.pop("chpswd_error", None)
				session.pop("chpswd", None)
				return redirect(url_for("account.account", status="complete").replace('index.cgi/', ''))
		else:
			session["chpswd"] = True
	else:
		session.pop("chpswd_error", None)
		session.pop("chpswd", None)
	return render_template("account/account.html")