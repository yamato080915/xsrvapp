from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(db.Model, UserMixin):
	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String, unique=True, index=True)
	password_hash = db.Column(db.String)
	created_at = db.Column(db.DateTime, default=datetime.now)
	updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)
	
	@property
	def password(self):
		raise AttributeError("読み取り不可")
	
	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)

class Auth(db.Model):
	__tablename__ = "auth"
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String, unique=True, index=True)
	authcode = db.Column(db.Integer)
	password_hash = db.Column(db.String)
	at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

	@property
	def password(self):
		raise AttributeError("読み取り不可")
	
	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)
	
class MathProblems(db.Model, UserMixin):
	__tablename__ = "mathproblems"
	id = db.Column(db.Integer, primary_key=True, index=True)
	user = db.Column(db.String)
	content = db.Column(db.String)
	category = db.Column(db.Integer)
	unit = db.Column(db.Integer)
	created_at = db.Column(db.DateTime, default=datetime.now)