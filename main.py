## Imports
import os
import json
import datetime
import webapp2
import jinja2
import hashlib
import hmac
import random
import string
from google.appengine.ext import db


## DataBase

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
							   autoescape = True)

def render_str(template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)

class LoginHandler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		return render_str(template, **params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def set_secure_cookie(self, name, val):
		cookie_val = make_secure_val(val)
		self.response.headers.add_header(
			'Set-Cookie',
			'%s=%s; Path=/' % (name, cookie_val))

	def read_secure_cookie(self, name):
		cookie_val = self.request.cookies.get(name)
		return cookie_val and check_secure_val(cookie_val)

	def login(self, user):
		self.set_secure_cookie('user_id', str(user.key().id()))

	def logout(self):
		self.response.delete_cookie('user_id')

	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		uid = self.read_secure_cookie('user_id')
		self.user = uid and User.by_id(int(uid))

SECRET = "muller3e3305d5c94558muts173dc874c366081abrailee9f64756631feb6932"

def make_secure_val(s):
		return "%s|%s" % (s, hmac.new(SECRET, s).hexdigest())

def check_secure_val(h):
		val = h.split('|')[0]
		if h == make_secure_val(val):
				return val

def make_salt():
	return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt=None):
	if not salt:
		salt=make_salt()
	h = hashlib.sha256(name + pw + salt).hexdigest()
	return '%s,%s' % (h, salt)

def valid_pw(name, pw, h):
	salt = h.split(',')[1]
	return h == make_pw_hash(name, pw, salt)

def users_key(group = 'default'):
	return db.Key.from_path('users', group)

def groups_key(group = 'default'):
	return db.Key.from_path('groups', group)

def questions_key(group = 'default'):
	return db.Key.from_path('questions', group)

class User(db.Model):
	username	= db.StringProperty(required = True)
	pw_hash = db.StringProperty(required = True)
	email = db.StringProperty()
	isProf  = db.BooleanProperty(required = True)

	@classmethod
	def by_id(cls, uid):
		return User.get_by_id(uid, parent = users_key())

	@classmethod
	def by_name(cls, username):
		u = User.all().filter('username =', username).get()
		return u

	@classmethod
	def register(cls, username, pw, isProf, email = None):
		pw_hash = make_pw_hash(name, pw)
		return User(parent = users_key(),
					username = username,
					pw_hash = pw_hash,
					isProf = isProf,
					email = email)

	@classmethod
	def login(cls, name, pw):
		u = cls.by_name(name)
		if u and valid_pw(username, pw, u.pw_hash):
			return u

class Group(db.Model):
	name = db.StringProperty(required=True)
	admin = db.IntegerProperty(required=True)
	description = db.TextProperty(required=True)

	@classmethod
	def by_id(cls, gid):
		return Group.get_by_id(gid, parent = groups_key())

class Question(db.Model):
	group_id = db.IntegerProperty(required=True)
	content = db.TextProperty(required=True)
	status = db.IntegerProperty(required=True)
	###
	### status: 0 - ready, 1 - sent, 2 - ended
	###
	a = db.StringProperty(required=True)
	b = db.StringProperty(required=True)
	c = db.StringProperty(required=True)
	d = db.StringProperty(required=True)
	ra = db.IntegerProperty(required=True)
	rb = db.IntegerProperty(required=True)
	rc = db.IntegerProperty(required=True)
	rd = db.IntegerProperty(required=True)
	###
	### counter
	###
	answer = db.IntegerProperty(required=True)
	###
	### 0 - a, 1 - b, 2 - c, 3 - d
	###

	def by_id(cls, qid):
		return Question.get_by_id(qid, parent = questions_key())

class Subscription(db.Model):
	user_id = db.IntegerProperty(required=True)
	group_id = db.IntegerProperty(required=True)

class Mark(db.Model):
	user_id = db.IntegerProperty(required=True)
	question_id = db.IntegerProperty(required=True)
	marked = db.IntegerProperty(required=True)


## Auxiliar Methods

def checkLogin(handler): ##incomplete#########################
	if handler.user:
		user_id = int(user)
		isProf = user.isProf
		return [user_id, isProf]

def LogIn(handler, username, password): ##incomplete#########################
	u = User.login(username, password)
	if u:
		handler.login(u)
		return ["user_id", "isProf"]
	else:
	  	return False


def existUser(username):
	res = db.gql("SELECT * FROM User WHERE username = '%(username)s'"%{"username": username})
	return bool(list(res))

def checkGroup(name):
	res = db.gql("SELECT * FROM Group WHERE name = '%s'"%(name))
	return bool(list(res))

def checkAdmin(user_id, group_id):
	group = Group.by_id(group_id)
	return group.admin == user_id

def checkLabel(label, group_id):
	res = db.gql("SELECT * FROM Question WHERE label = '%(label)s' AND group_id = %(group_id)s"%({"label": label, "group_id":group_id}))
	return bool(list(res))

def checkMark(user_id, question_id):
	mark = db.gql("SELECT * FROM Mark WHERE user_id = %(user_id)s AND question_id = %(question_id)s" %({"user_id": user_id, "question_id": question_id}))
	return bool(list(mark))


## Routes Handlers

## imcomplete: change radio button to click

class Home(LoginHandler):## missing templates in get request
	def get(self):
		res = checkLogin()
		if res:
			if res[1]:
				query = db.gql("SELECT * FROM Group WHERE admin = %s"%(res[0]))
				groups = [(g.name, g.group_id) for g in query]
				#return "PROFPAGE(groups)"
				self.render('home.html', groups)
			else:
				subs = db.gql("SELECT * FROM Subscription WHERE user_id = %s"%(res[0]))
				query = []
				for s in subs:
					query.append(Group.by_id(s.group_id))
				groups = [(g.name, g.group_id) for g in query]
				#return "ALUNOPAGE(groups)"
				self.render('home.html', groups)
		else:
			#return "LOGINPAGE"
			self.render('login.html')

	def post(self):
		self.response.headers['Content-Type'] = 'application/json'
		action = self.request.get('action')
		if action == 'logout':
			self.logout()
			self.response.write(json.dumps({"status":True, "redirect": True}))
		else:
			username = self.request.get('username')
			password = self.request.get('password')
			if not username or not password:
				return
	
			res = LogIn(username, password)
	
			if res:
				self.response.write(json.dumps({"status":True}))
				#return "REFRESH"
			else:
				self.response.write(json.dumps({"status":False}))
				#return "LOGINPAGE+ERRO" 

class Register(LoginHandler):## missing templates in get request
	def get(self):
		return self.render('register.html')

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		isProf = bool(self.request.get('isProf'))
		self.response.headers['Content-Type'] = 'application/json'

		if not username or not password:
			return

		if existUser(username):
			self.response.write(json.dumps({"status": False}))
		else:
			##change password for hash
			u = User.register(username, password, email = "", isProf)
			u.put()
			self.login(u)
			print "new user: " + str(username) + ("(prof)" if isProf else "")
			self.response.write(json.dumps({"status": True})) 

class ShowGroup(LoginHandler):## missing templates in get request
	def get(self):
		res = checkLogin()
		if res:
			if res[1]:
				group_id = int(self.request.get("group_id"))
				questions = db.gql("SELECT * FROM Question WHERE group_id = %(group_id)s"%{"group_id": group_id})
				questions= [{"question_id": q.key().id(), "content": q.content, "label" : q.label, "answers":q.answers} for q in questions]
				group = Group.by_id(group_id)
				description = group.description
				if checkAdmin(res[0], group_id):
					return self.render('formquestion.html', description = description, groups = groups)
				else:
					self.error(401)
					#return "GROUP BELONGS TO OTHER USER"
			else:
				self.error(401)
				#return "NOT PROFESSOR"

		else:
			return "LOGINPAGE"

	def post(self):
		self.error(405) 

class AddGroup(LoginHandler): ## missing templates in get request

	def get(self):
		res = checkLogin()
		if res:
			if res[1]:
				return "ADD GROUP FORM PAGE"
			else:
				self.error(401)
				#return "STUDENT CANNOT ADD GROUP"
		else:
			return "LOGINPAGE"

	def post(self):
		res = checkLogin()
		self.response.headers['Content-Type'] = 'application/json'
		if res:
			if res[1]:
				name = self.request.get("name")
				description = self.request.get("description")
				#admin = self.request.get("admin")
				if not checkGroup():
					new_group = Group(name=name, description=description, admin=res[0])
					new_group.put()
					self.response.write(json.dumps({"status": True}))
					#return "TRUE + goto groups"
				else:
					self.response.write(json.dumps({"status": False, "redirect": False}))
					#return "FALSE + ja existe nome de grupo"
			else:
				self.error(401)
				#return "ERROR, only profs allowed"

		else:
			self.response.write(json.dumps({"status": False, "redirect": True}))
			#return "FALSE - GOTO LOGIN"

class AddQuestion(webapp2.RequestHandler):## missing templates in get request
	def get(self):
		res = checkLogin()
		if res:
			if res[1]:
				group_id = int(self.request.get("group_id"))
				group = Group.by_id(group_id)
				name = group.name
				if checkAdmin(res[0], group_id):
					return "ADD QUESTION FORM PAGE (name, group_id)"
				else:
					self.error(401)
					#return "GROUP BELONGS TO OTHER USER"
			else:
				self.error(401)
				#return "ERROR, only profs allowed"

		else:
			return "LOGINPAGE"

	def post(self):
		res = checkLogin()
		self.response.headers['Content-Type'] = 'application/json'
		if res:
			if res[1]:
				if checkAdmin(res[0], group_id):
					label = self.request.get("label")
					group_id = int(self.request.get("group_id"))
					if not checkLabel(label, group_id):
						content = self.request.get("content")
						answers = self.request.get("answers")
						a = self.request.get("a")
						b = self.request.get("b")
						c = self.request.get("c")
						d = self.request.get("d")
						ra = 0
						rb = 0
						rc = 0
						rd = 0
						answer = int(self.request.get('marked'))
						status = 0
						new_question = Question(group_id=group_id, content=content, status=status, a=a, b=b, c=c, d=d, ra=0,rb=0, rc=0, rd=0, answer=answer)
						new_question.put()
						self.response.write(json.dumps({"status" : True}))
						#return "TRUE + go to group_id"
					else:
						self.response.write(json.dumps({"status": False, "redirect": False}))
						#return "FALSE + ja existe essa label no grupo"
				else:
					self.error(401)
					#return "GROUP BELONGS TO OTHER USER"
			else:
				self.error(401)
				#return "ERROR, only profs allowed"
		else:
			self.response.write(json.dumps({"status": False, "redirect": True}))
			#return "FALSE - GOTO LOGIN" 

class EnterGroup(webapp2.RequestHandler): ##missing templates in get request
	def get(self):
		res = checkLogin()
		if res:
			if res[1]:
				self.error(401)
				#return "PAGE FOR STUDENTS"
			else:
				return "FORM FOR INPUT GROUP NAME"
		else:
			return "LOGINPAGE"

	def post(self):
		res = checkLogin()
		self.response.headers['Content-Type'] = 'application/json'
		if res:
			name = self.request.get("name")
			group = db.gql("SELECT * FROM Group WHERE name = '%s'"%(name)).get()
			if group:
				new_sub = Subscription(group_id=group.group_id, user_id=res[0])
				new_sub.put()
				self.response.write(json.dumps({"status": True}))
				#return "TRUE GO BACK"
			else:
				self.response.write(json.dumps({"status": False, "redirect" : False}))
				#return "GROUP DOES NOT EXIST"
		else:
			sel.response.write(json.dumps({"status":False, "redirect" : True}))
			#return "GOTO LOGIN" 

class ShowQuestion(webapp2.RequestHandler): ##incomplete
	def get(self):
		res = checkLogin()
		if res:
			question_id = int(self.request.get("question_id"))
			question = Question.by_id(question_id)
			if res[1]:
				return "SHOW QUESTION(question)(button = [start, stop, STATISTICS])"
			else:
				if question.status == 0:
					self.error(401)
				elif question.status == 1:
					if not checkMark():
						return "SHOW QUESTION READY TO ANSWER"
					else:
						return "GOTO GROUP"
				elif question.status == 2:
					return "SHOW ANSWERED QUESTION"
		else:
			return "LOGINPAGE"

	def post(self):
		res = checkLogin()
		self.response.headers['Content-Type'] = 'application/json'
		if res:
			question_id = int(self.request.get("question_id"))
			question = Question.by_id(question_id)
			if res[1]:
				if question.status == 0:
					question.status = 1
					question.put()
					self.response.write(json.dumps({"status": True}))
				elif question.status == 1:
					question.status = 2
					question.put()
					self.response.write(json.dumps({"status": True}))
				elif question.status == 2:
					self.error(400)
					#IMPOSSIBLE TO GET HERE
			else:
				if question.status == 0:
					self.error(401)
				elif question.status == 1:
					marked = int(self.request.get('marked'))
					new_mark = Mark(user_id=res[0], question_id=question.key().id(), marked=marked)
					self.response.write(json.dumps({"status": True}))
					pass
				elif question.status == 2:
					self.error(400)
					#impossible
		else:
			self.response.write(json.dumps({"status": False, "redirect" : True}))
			#return "LOGINPAGE"


## Main

if __name__ == '__main__':
	application = webapp2.WSGIApplication([
	('/', Home),
	('/register', Register),
	('/add', AddGroup),
	('/enter', EnterGroup),
	('/group', ShowGroup),
	('/question', ShowQuestion)
	], debug=True)