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
	isProf  = db.IntegerProperty(required = True)

	@classmethod
	def by_id(cls, uid):
		return User.get_by_id(uid, parent = users_key())

	@classmethod
	def by_name(cls, username):
		u = User.all().filter('username =', username).get()
		return u

	@classmethod
	def register(cls, username, pw, isProf, email = None):
		pw_hash = make_pw_hash(username, pw)
		return User(parent = users_key(),
					username = username,
					pw_hash = pw_hash,
					isProf = isProf,
					email = email)

	@classmethod
	def login(cls, name, pw):
		u = cls.by_name(name)
		if u and valid_pw(name, pw, u.pw_hash):
			return u

class Group(db.Model):
	name = db.StringProperty(required=True)
	admin = db.IntegerProperty(required=True)
	description = db.TextProperty(required=True)

	@classmethod
	def by_id(cls, gid):
		return Group.get_by_id(gid)

class Question(db.Model):
	group_id = db.IntegerProperty(required=True)
	content = db.TextProperty(required=True)
	status = db.IntegerProperty(required=True)
	label = db.StringProperty(required=True)
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
		return Question.get_by_id(qid)

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
		user_id = handler.user.key().id()
		isProf = handler.user.isProf
		return [user_id, isProf]

def LogIn(handler, username, password): ##incomplete#########################
	u = User.login(username, password)
	if u:
		handler.login(u)
		return ["user_id", "isProf"]
	else:
	  	return False


def existUser(username):
	res = db.GqlQuery("SELECT * FROM User WHERE username = '%(username)s'"%{"username": username})
	return bool(list(res))

def checkGroup(name):
	res = db.GqlQuery("SELECT * FROM Group WHERE name = '%s'"%(name))
	return bool(list(res))

def checkAdmin(user_id, group_id):
	group = Group.by_id(group_id)
	return group.admin == user_id

def checkLabel(label, group_id):
	res = db.GqlQuery("SELECT * FROM Question WHERE label = '%(label)s' AND group_id = %(group_id)s"%({"label": label, "group_id":group_id}))
	return bool(list(res))

def checkMark(user_id, question_id):
	mark = db.GqlQuery("SELECT * FROM Mark WHERE user_id = %(user_id)s AND question_id = %(question_id)s" %({"user_id": user_id, "question_id": question_id}))
	return bool(list(mark))


## Routes Handlers

## imcomplete: change radio button to click

class Home(LoginHandler):## missing templates in get request
	def get(self):
		res = checkLogin(self)
		if res:
			if res[1]:
				query = db.GqlQuery("SELECT * FROM Group WHERE admin = %s"%(res[0]))
				groups = [(g.name, g.key().id()) for g in query]
				#return "PROFPAGE(groups)"
				self.render('home.html', groups=groups)
			else:
				subs = db.GqlQuery("SELECT * FROM Subscription WHERE user_id = %s"%(res[0]))
				query = []
				for s in subs:
					query.append(Group.by_id(s.group_id))
				groups = [(g.name, g.key().id()) for g in query]
				#return "ALUNOPAGE(groups)"
				self.render('home.html', groups=groups)
		else:
			#return "LOGINPAGE"
			self.render('login.html')

	def post(self):
		action = self.request.get('action')
		print "action: " + action
		if action == "Login":
			username = self.request.get('username')
			password = self.request.get('password')
			if not username or not password:
				return
	
			res = LogIn(self, username, password)
	
			self.redirect('/') 
		else:
			print "action: " + action
			self.logout()
			self.redirect('/')

class Register(LoginHandler):## missing templates in get request
	def get(self):
		return self.render('register.html')

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		isProf = self.request.get('isProf')

		if isProf == "isProf":
			isProf = 1
		else:
			isProf = 0

		if not username or not password:
			return


		if existUser(username):
			self.render("register.html")
		else:
			u = User.register(username, password, isProf, email = "")
			u.put()
			self.login(u)
			print "new user: " + str(username) + ("(prof)" if isProf else "")
			self.redirect("/")

class ShowGroup(LoginHandler):## missing templates in get request
	def get(self):
		res = checkLogin(self)
		if res:
			if res[1]:
				group_id = int(self.request.get("group_id"))
				questions = db.GqlQuery("SELECT * FROM Question WHERE group_id = %(group_id)s"%{"group_id": group_id})
				questions= [(q.label, q.key().id()) for q in questions]
				group = Group.by_id(group_id)
				#group = db.GqlQuery("SELECT * FROM Group where __key__ = KEY('Group', %s)"%(group_id)).get()
				print "---------------------------------------------------------------------------------"
				print group
				print "---------------------------------------------------------------------------------"
				description = group.description
				name = group.name
				if checkAdmin(res[0], group_id):
					return self.render('group.html', description = description, name = name, questions = questions, group_id=group_id)
				else:
					self.error(401)
					#return "GROUP BELONGS TO OTHER USER"
			else:
				self.error(401)
				#return "NOT PROFESSOR"

		else:
			self.redirect('/')
			#return "LOGINPAGE"

	def post(self):
		self.error(405) 

class AddGroup(LoginHandler): ## missing templates in get request

	def get(self):
		res = checkLogin(self)
		if res:
			if res[1]:
				self.render('form_group.html')
				#return "ADD GROUP FORM PAGE"
			else:
				self.error(401)
				#return "STUDENT CANNOT ADD GROUP"
		else:
			self.redirect('/')
			#return "LOGINPAGE"

	def post(self):
		res = checkLogin(self)
		if res:
			if res[1]:
				name = self.request.get("name")
				description = self.request.get("description")
				#admin = self.request.get("admin")
				if not checkGroup(name):
					new_group = Group(name=name, description=description, admin=res[0])
					new_group.put()
					self.redirect('/')
					#return "TRUE + goto home"
				else:
					self.redirect("/add_group")
					#return "FALSE + ja existe nome de grupo"
			else:
				self.error(401)
				#return "ERROR, only profs allowed"
		else:
			self.redirect('/')
			#return "FALSE - GOTO LOGIN"

class AddQuestion(LoginHandler):## missing templates in get request
	def get(self):
		res = checkLogin(self)
		if res:
			if res[1]:
				group_id = int(self.request.get("group_id"))
				group = Group.by_id(group_id)
				name = group.name
				if checkAdmin(res[0], group_id):
					self.render('form_question.html', group_id=group_id)
					#return "ADD QUESTION FORM PAGE (name, group_id)"
				else:
					self.error(401)
					#return "GROUP BELONGS TO OTHER USER"
			else:
				self.error(401)
				#return "ERROR, only profs allowed"

		else:
			self.redirect('/')
			#return "LOGINPAGE"

	def post(self):
		res = checkLogin(self)
		if res:
			if res[1]:
				group_id = int(self.request.get("group_id"))
				if checkAdmin(res[0], group_id):
					label = self.request.get("label")
					print "---------------------------------"
					print "label : " + label
					print "---------------------------------"
					if not checkLabel(label, group_id):
						content = self.request.get("content")
						answer = int(self.request.get("answer"))
						a = self.request.get("a")
						b = self.request.get("b")
						c = self.request.get("c")
						d = self.request.get("d")
						ra = 0
						rb = 0
						rc = 0
						rd = 0
						status = 0
						new_question = Question(label=label, group_id=group_id, content=content, status=status, a=a, b=b, c=c, d=d, ra=0,rb=0, rc=0, rd=0, answer=answer)
						new_question.put()
						for i in range(1000000): #sleep
							pass
						self.redirect('group?group_id=' + str(group_id))
						#return "TRUE + go to group_id"
					else:
						self.redirect('add_question')
						#return "FALSE + ja existe essa label no grupo"
				else:
					self.error(401)
					#return "GROUP BELONGS TO OTHER USER"
			else:
				self.error(401)
				#return "ERROR, only profs allowed"
		else:
			self.redirect('/')
			#return "FALSE - GOTO LOGIN" 

class EnterGroup(LoginHandler): ##missing templates in get request
	def get(self):
		res = checkLogin(self)
		if res:
			if res[1]:
				self.error(401)
				#return "PAGE FOR STUDENTS"
			else:
				query = db.GqlQuery("SELECT * FROM Group")
				groups = [(g.name, g.group_id) for g in query]
				self.render('get_group.html', groups)
				#return "FORM FOR INPUT GROUP NAME"
		else:
			self.redirect('/')
			#return "LOGINPAGE"

	def post(self):
		res = checkLogin(self)
		if res:
			group_id = int(self.request.get("group_id"))
			group = Group.by_id(group_id)
			new_sub = Subscription(group_id=group.key().id(), user_id=res[0])
			new_sub.put()
			self.redirect('/')
			#return "TRUE GO BACK"
			
		else:
			self.redirect('/')
			#return "GOTO LOGIN" 

class ShowQuestion(LoginHandler): ##incomplete
	def get(self):
		res = checkLogin(self)
		if res:
			question_id = int(self.request.get("question_id"))
			question = Question.by_id(question_id)
			label = question.label
			a = question.a
			b = question.b
			c = question.c
			d = question.d
			ra = question.ra
			rb = question.rb
			rc = question.rc
			rd = question.rd
			status = question.status
			answer = question.answer
			content = question.content

			if res[1]:
				self.render('question.html', isProf=res[1], answer=answer, label=label, content=content, a=a, b=b, c=c, d=d, ra=ra, rb=rb, rc=rc, rd=rd, status=status)
				#return "SHOW QUESTION(question)(button = [start, stop, STATISTICS])"
			else:
				if question.status == 0:
					self.error(401)
				elif question.status == 1: 	
					if not checkMark():
						return "SHOW QUESTION READY TO ANSWER"
					else:
						self.redirect('/group')
						#return "GOTO GROUP"
				elif question.status == 2:
					return "SHOW ANSWERED QUESTION"
		else:
			self.redirect('/')
			#return "LOGINPAGE"

	def post(self):
		res = checkLogin(self)
		if res:
			question_id = int(self.request.get("question_id"))
			question = Question.by_id(question_id)
			if res[1]:
				if question.status == 0:
					question.status = 1
					question.put()
					self.redirect("/question?question_id=" + str(question_id))
				elif question.status == 1:
					question.status = 2
					question.put()
					self.redirect("/question?question_id=" + str(question_id))
					
				elif question.status == 2:
					self.error(400)
					#IMPOSSIBLE TO GET HERE
			else:
				if question.status == 0:
					self.error(401)
				elif question.status == 1:
					marked = int(self.request.get('marked'))
					new_mark = Mark(user_id=res[0], question_id=question.key().id(), marked=marked)
					self.redirect("/question?question_id=" + str(question_id))
					pass
				elif question.status == 2:
					self.error(400)
					#impossible
		else:
			self.redirect('/')
			#return "LOGINPAGE"


## Main
app = webapp2.WSGIApplication([('/', Home),
	('/register', Register),
	('/add', AddGroup),
	('/enter', EnterGroup),
	('/group', ShowGroup),
	('/addQuestion', AddQuestion),
	('/question', ShowQuestion)], debug=True)