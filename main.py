import json
import datetime
import webapp2
from google.appengine.ext import ndb

#DataBase

class User(ndb.Model):
	user_id = ndb.IntegerProperty(auto_now_add=True)
	username = ndb.StringProperty(required=True)
	password = ndb.StringProperty(required=True)
	professor = ndb.BooleanProperty(required=True)
	#groups user attend
	groups = ndb.ListPoperty(ndb.Key)
	#groups user is admin
	admin = ndb.ListPoperty(ndb.Key)

class Group(ndb.Model):
	group_id = ndb.IntegerProperty(auto_now_add=True)
	name = ndb.StringProperty(required=True)
	admin = ndb.IntegerProperty(required=True)
	description = ndb.TextProperty(required=True)
	#questions in the group
	questions = ndb.ListPoperty(ndb.Key)

class Question(ndb.Model):
	question_id = ndb.IntegerProperty(auto_now_add=True)
	content = ndb.TextProperty(required=True)
	answers = ndb.StringProperty(required=True)


## Methods

def checkUser(username, password):
	return True or False

def checkLogin():
	return ["user_id", "isProf"] or False

def LogIn(username, password):
	return ["user_id", "isProf"] or False



##routes

class Home(webapp2.RequestHandler):
	def get(self):
		res = checkLogin()
		if res:
			if res[1]:
				return "PROFPAGE"
			else:
				return "ALUNOPAGE"
		else:
			return "LOGINPAGE"

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		if not username or not password:
			return

		res = LogIn(username, password)

		if res:
			if res[1]:
				return "PROFPAGE"
			else:
				return "ALUNOPAGE"
		else:
			return "LOGINPAGE+ERRO"

class Register(webapp2.RequestHandler):
	def existUser(username):
		res = ndb.gql("SELECT * FROM User WHERE username = '%(username)s'"%{"username": username})
		return bool(list(res))

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
			self.response.write(json.dumps({"status": True}))

class ShowGroup(webapp2.RequestHandler):
	def get(self):
		res = checkLogin()
		if res:
			if res[1]:
				group_id = self.request.get("group_id")
				questions = ndb.gql("SELECT * FROM Question WHERE group_id = '%(group_id)s'"%{"group_id": group_id})
				group_question = [{"question_id": q.question_id, "content": q.content, "label" : q.label, "answers":q.answers} for q in questions]
				if checkAdmin(res[0], group_id):
					return "ADD QUESTION FORM PAGE (group_question)"
				else:
					self.error(401)
					#return "GROUP BELONGS TO OTHER USER"
			else:
				self.error(401)

		else:
			return "LOGINPAGE"

	def post(self):
		res = checkLogin()
		self.response.headers['Content-Type'] = 'application/json'
		if res:
			if res[1]:
				label = self.request.get("label")
				content = self.request.get("content")
				answers = self.request.get("answers")
				group_id = self.request.get("group_id")

				if checkAdmin(res[0], group_id):
					if not checkLabel(label, group_id):
						## Add question and link to groups
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

class AddGroup(webapp2.RequestHandler):
	def checkGroup(name):
		res = ndb.gql("SELECT * FROM Group WHERE name = '%s'"%(name))
		return bool(list(res))

	def get(self):
		res = checkLogin()
		if res:
			if res[1]:
				return "ADD GROUP FORM PAGE"
			else:
				self.error(401)
		else:
			return "LOGINPAGE"

	def post(self):
		res = checkLogin()
		self.response.headers['Content-Type'] = 'application/json'
		if res:
			if res[1]:
				name = self.request.get("name")
				description = self.request.get("description")
				admin = 17
				#admin = self.request.get("admin")
				if not checkGroup():
					new_group = Group(name=name, description=description, admin=admin)
					new_group.put()
					user = ndb.gql("SELECT * WHERE user_id = %s"%(admin))
					#user = User.gql("WHERE user_id = %s"%(admin)).get()
					user.groups.append(new_group.key())
					user.put()
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

class AddQuestion(webapp2.RequestHandler):
	def checkAdmin(user_id, group_id):
		res = ndb.gql("SELECT * FROM Group WHERE group_id = %(group_id)s AND admin = %(user_id)s"%({"group_id":group_id, "user_id":user_id}))
		return bool(list(res))
	def checkLabel(label, group_id):
		res = ndb.gql("SELECT * FROM Question WHERE label = '%(label)s' AND admin = %(group_id)s"%({"label": label, "group_id":group_id}))
		return bool(list(res))

	def get(self):
		res = checkLogin()
		if res:
			if res[1]:
				group_id = self.request.get("group_id")
				if checkAdmin(res[0], group_id):
					return "ADD QUESTION FORM PAGE (group_id)"
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
				label = self.request.get("label")
				content = self.request.get("content")
				answers = self.request.get("answers")
				group_id = self.request.get("group_id")

				if checkAdmin(res[0], group_id):
					if not checkLabel(label, group_id):
						## Add question and link to groups
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

class EnterGroup(webapp2.RequestHandler):
	pass

class SendQuestion(webapp2.RequestHandler):
	pass

class AnswerQuestion(webapp2.RequestHandler):
	pass

if __name__ == '__main__':
	application = webapp2.WSGIApplication([
	('/', Home),
	('/register', Register),
	('/add', AddGroup),
	('/enter', EnterGroup),
	('/group', ShowGroup),
	('/question', ShowQuestion)
	], debug=True)