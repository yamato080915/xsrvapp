from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(db.Model, UserMixin):
	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String, unique=True, index=True)
	password_hash = db.Column(db.String)
	is_admin = db.Column(db.Boolean, default=False, nullable=False)
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
		
	def to_dict(self):
		return {
			"id": self.id,
			"email": self.email
		}
	
	def data_type(self):
		return {
			"email": "email"
		}

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
	
class MathProblems(db.Model):
	__tablename__ = "mathproblems"
	id = db.Column(db.Integer, primary_key=True, index=True)
	user = db.Column(db.Integer)
	title = db.Column(db.String)
	content = db.Column(db.String)
	explanation = db.Column(db.String)
	category = db.Column(db.Integer)
	unit = db.Column(db.Integer)
	score = db.Column(db.String)
	created_at = db.Column(db.DateTime, default=datetime.now)

	def to_dict(self):
		return {
			"id": self.id,
			"user": self.user,
			"title": self.title,
			"content": self.content,
			"explanation": self.explanation,
			"category": self.category,
			"unit": self.unit,
			"score": self.score
		}
	
	def data_type(self):
		return {
			"user": "text",
			"title": "text",
			"content": "textarea",
			"explanation": "textarea",
			"category": "text",
			"unit": "text",
			"score": "text"
		}

class Submissions(db.Model):
	__tablename__ = "submissions"
	id = db.Column(db.Integer, primary_key=True, index=True)
	problem = db.Column(db.Integer)
	user = db.Column(db.Integer)
	content = db.Column(db.String)
	score = db.Column(db.String)
	judged = db.Column(db.Boolean, default=False, nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.now)
	
	def to_dict(self):
		return {
			"id": self.id,
			"problem": self.problem,
			"user": self.user,
			"content": self.content,
			"score": self.score,
			"judged": self.judged
		}
	
	def data_type(self):
		return {
			"problem": "text",
			"user": "text",
			"content": "textarea",
			"score": "text",
			"judged": "text"
		}

class Question(db.Model):
	__tablename__ = "question"
	id = db.Column(db.Integer, primary_key=True, index=True)
	user = db.Column(db.Integer)
	content = db.Column(db.String)
	category = db.Column(db.String)
	resolved = db.Column(db.Boolean, default=False, nullable=False)

	def to_dict(self):
		return {
			"id": self.id,
			"user": self.user,
			"content": self.content,
			"category": self.category,
			"resolved": self.resolved
		}
	
	def data_type(self):
		return {
			"user": "text",
			"content": "textarea",
			"category": "text",
			"resolved": "text"
		}