import json
import datetime
import webapp2
from google.appengine.ext import ndb

## DataBase

class User(ndb.Model):
	user_id = ndb.IntegerProperty(auto_now_add=True)
	username = ndb.StringProperty(required=True)
	password = ndb.StringProperty(required=True)
	isProf = ndb.BooleanProperty(required=True)

class Group(ndb.Model):
	group_id = ndb.IntegerProperty(auto_now_add=True)
	name = ndb.StringProperty(required=True)
	admin = ndb.IntegerProperty(required=True)
	description = ndb.TextProperty(required=True)

class Question(ndb.Model):
	question_id = ndb.IntegerProperty(auto_now_add=True)
	group_id = ndb.IntegerProperty(required=True)
	content = ndb.TextProperty(required=True)
	status = ndb.IntegerProperty(required=True)
	###
	### status: 0 - ready, 1 - sent, 2 - ended
	###
	a = ndb.StringProperty(required=True)
	b = ndb.StringProperty(required=True)
	c = ndb.StringProperty(required=True)
	d = ndb.StringProperty(required=True)
	ra = ndb.IntegerProperty(required=True)
	rb = ndb.IntegerProperty(required=True)
	rc = ndb.IntegerProperty(required=True)
	rd = ndb.IntegerProperty(required=True)
	###
	### counter
	###
	answer = ndb.IntegerProperty(required=True)
	###
	### 0 - a, 1 - b, 2 - c, 3 - d
	###

class Subscription(ndb.Model):
	user_id = ndb.IntegerProperty(required=True)
	group_id = ndb.IntegerProperty(required=True)


## Auxiliar Methods

def checkUser(username, password): ##incomplete##
	return True or False

def checkLogin(): ##incomplete##
	return ["user_id", "isProf"] or False

def LogIn(username, password): ##incomplete##
	return ["user_id", "isProf"] or False

def existUser(username):
	res = ndb.gql("SELECT * FROM User WHERE username = '%(username)s'"%{"username": username})
	return bool(list(res))

def checkGroup(name):
	res = ndb.gql("SELECT * FROM Group WHERE name = '%s'"%(name))
	return bool(list(res))

def checkAdmin(user_id, group_id):
	res = ndb.gql("SELECT * FROM Group WHERE group_id = %(group_id)s AND admin = %(user_id)s"%({"group_id":group_id, "user_id":user_id}))
	return bool(list(res))

def checkLabel(label, group_id):
	res = ndb.gql("SELECT * FROM Question WHERE label = '%(label)s' AND admin = %(group_id)s"%({"label": label, "group_id":group_id}))
	return bool(list(res))


## Routes Handlers

class Home(webapp2.RequestHandler):
	def get(self):
		res = checkLogin()
		if res:
			if res[1]:
				query = ndb.gql("SELECT * FROM Group WHERE admin = %s"%(res[0]))
				groups = [(g.name, g.group_id) for g in query]
				return "PROFPAGE(groups)"
			else:
				subs = ndb.gql("SELECT * FROM Subscription WHERE user_id = %s"%(res[0]))
				subs = tuple(s.group_id for s in subs)
				query = ndb.gql("SELECT * FROM Group WHERE group_id IN %s"%(subs))
				groups = [(g.name, g.group_id) for g in query]
				return "ALUNOPAGE(groups)"
		else:
			return "LOGINPAGE"

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		if not username or not password:
			return

		res = LogIn(username, password)

		if res:
			self.response.headers['Content-Type'] = 'application/json'
			self.response.write(json.dumps({"status":True}))
			#return "REFRESH"
		else:
			self.response.headers['Content-Type'] = 'application/json'
			self.response.write(json.dumps({"status":False}))
			#return "LOGINPAGE+ERRO" ##missing templates in get request

class Register(webapp2.RequestHandler):
	def get(self):
		return "REGISTER PAGE"

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
			new_user = User(username=username, isProf=isProf, password=password)
			new_user.put()
			print "new user: " + str(username) + ("(prof)" if isProf else "")
			self.response.write(json.dumps({"status": True})) ##missing templates in get request

class ShowGroup(webapp2.RequestHandler):
	def get(self):
		res = checkLogin()
		if res:
			if res[1]:
				group_id = int(self.request.get("group_id"))
				questions = ndb.gql("SELECT * FROM Question WHERE group_id = %(group_id)s"%{"group_id": group_id})
				questions= [{"question_id": q.question_id, "content": q.content, "label" : q.label, "answers":q.answers} for q in questions]
				group = ndb.gql("SELECT * FROM Group WHERE group_id = %(group_id)s"%{"group_id": group_id})
				description = group.description
				if checkAdmin(res[0], group_id):
					return "ADD QUESTION FORM PAGE (description, questions)"
				else:
					self.error(401)
					#return "GROUP BELONGS TO OTHER USER"
			else:
				self.error(401)
				#return "NOT PROFESSOR"

		else:
			return "LOGINPAGE"

	def post(self):
		self.error(405) ##missing templates in get request

class AddGroup(webapp2.RequestHandler):

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
			#return "FALSE - GOTO LOGIN" ##missing templates in get request

class AddQuestion(webapp2.RequestHandler):
	def get(self):
		res = checkLogin()
		if res:
			if res[1]:
				group_id = int(self.request.get("group_id"))
				group = ndb.gql("SELECT * FROM Group WHERE group_id = %s"%(group_id))
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
						checka = self.request.get("checka")
						checkb = self.request.get("checkb")
						checkc = self.request.get("checkc")
						checkd = self.request.get("checkd")
						answer = 0 if checka == "True" else 1 if checkb == "True" else 2 if checkc == "True" else 3 if checkd == "True"
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
			#return "FALSE - GOTO LOGIN" ##missing templates in get request

class EnterGroup(webapp2.RequestHandler):
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
			group = ndb.gql("SELECT * FROM Group WHERE name = '%s'"%(name)).get()
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
			#return "GOTO LOGIN" ##missing templates in get request

class ShowQuestion(webapp2.RequestHandler): ##incomplete
	def get(self):
		res = checkLogin()
		if res:
			question_id = int(self.request.get("question_id"))
			question = ndb.gql("SELECT * FROM Question WHERE question_id = %s"%(question_id)).get()
			if res[1]:
				if question.status == 0:
					pass
				elif question.status == 1:
					pass
				elif question.status == 2:
					pass
			else:
				if question.status == 0:
					pass
				elif question.status == 1:
					pass
				elif question.status == 2:
					pass
		else:
			return "LOGINPAGE"

	def post(self):
		res = checkLogin()
		self.response.headers['Content-Type'] = 'application/json'
		if res:
			question_id = int(self.request.get("question_id"))
			question = ndb.gql("SELECT * FROM Question WHERE question_id = %s"%(question_id)).get()
			if res[1]:
				if question.status == 0:
					pass
				elif question.status == 1:
					pass
				elif question.status == 2:
					pass
			else:
				if question.status == 0:
					pass
				elif question.status == 1:
					pass
				elif question.status == 2:
					pass
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