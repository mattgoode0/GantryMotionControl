# classRant
# by: Evan Pratten <ewpratten>

import devRantSimple as dRS

# api requires an app id
# get it from dRS
appId = dRS.appid

class User(object):
	# Takes in a username, generates all other data
	def __init__(self, username):
		# Gets all of the data about the user from the api
		raw = dRS.getUserData(dRS.getUserId(username), {"app":appId})
		
		# Store all of the usefull data in vars
		self.username = raw["profile"]["username"]
		self.user_score = raw["profile"]["score"]
		self.about = raw["profile"]["about"]
		self.skills = raw["profile"]["skills"]
		self.isdevRantPlusPlus = bool(raw["profile"]["dpp"])
	# End __init__
# End User

class Comment(object):
	# Takes in comment ddata from api, parses data
	def __init__(self, commentdata):
		# Store all usefull data in vars
		self.body = commentdata["body"]
		self.commentId = commentdata["id"]
		self.rantId = commentdata["rant_id"]
		self.score = commentdata["score"]
		self.user = User(commentdata["user_username"])
		self.username = self.user.username
	# End __init__
# End Comment

class Notif(object):
	# Takes in data from api, parses
	def __init__(self, notif):
		item = notif	# This is part of a bugfix for a diffrent program. Not required for ahything else.
		self.timeCreated = item["created_time"]
		self.contentType = item["type"]
		self.isRead = bool(item["read"])
		self.rantId = item["rant_id"]
		self.userId = item["uid"]
		# We know the user id but not the username. The api can tell us what we need
		self.username = dRS.getUserData(self.userId, {"app":appId})["profile"]["username"]
		
		# Set content type to an enum instead of string
		if self.contentType == "rant_sub":
			self.contentType = dRS.NotifType.sub
		if self.contentType == "comment_content":
			self.contentType = dRS.NotifType.content
		if self.contentType == "content_vote":
			self.contentType = dRS.NotifType.vote
		if self.contentType == "comment_mention":
			self.contentType = dRS.NotifType.mention
		
		# Set a comment id if the notif contains one
		if self.contentType == dRS.NotifType.content or self.contentType == dRS.NotifType.mention:
			self.commentId = item["comment_id"]
	# End __init__
# End Notif
	

class Rant(object):
	# Takes in rant id, parses data
	def __init__(self, rantid):
		self.rantid = rantid
		self.rantCode = dRS.genRantCode(rantid)
		rant = dRS.getRantFromId(self.rantid)
		self.body = rant["text"]
		self.score = rant["score"]
		self.username = rant["username"]
		self.user = User(self.username)
		self.tags = rant["tags"]
		self.comments = rant["comments"]
		# Api knows the capitalization. we don't
		self.username = self.user.username
	# End __init__
	
	def loadComments(self):
		# This takes a while. reassure the user that the program has not crashed
		print("Fetching Comments. Please Wait...", end="")
		comments = self.comments
		self.comments = []
		i = 0
		while i < len(comments):
			self.comments.append(Comment(comments[i]))
			i+=1
	# End loadComments
	
	def printComments(self):
		# \r is to make things look nice. spaces are to clear text
		if len(self.comments) == 0:
			print("\rNo Comments On Current Rant.              ")
		else:
			print("\rComments:                          ")
			i = 0
			while i < len(self.comments):
				if self.comments[i].user.isdevRantPlusPlus:
					dpp = " ++"
				else:
					dpp = ""
				
				print("-------")
				# @username ++ | Score:99
				print("@" + self.comments[i].user.username + dpp + " | Score:" + str(self.comments[i].score))
				print(self.comments[i].body)
				i+=1
	# End printComments
	
	def printAndLoadComments(self):
		if len(self.comments) == 0:
			print("\rNo Comments On Current Rant.              ")
		else:
			print("\rComments:                          ")
			i = 0
			while i < len(self.comments):
				comment = Comment(self.comments[i])
				if comment.user.isdevRantPlusPlus:
					dpp = " ++"
				else:
					dpp = ""
				
				print("-------")
				# @username ++ | Score:99
				print("@" + comment.user.username + dpp + " | Score:" + str(comment.score))
				print(comment.body)
				i+=1
	# End printAndLoadComments
	
	def getTags(self):
		i = 0
		ret = ""
		while i < len(self.tags):
			ret += self.tags[i] + ", "
			i+=1
		return ret
	# End getTags
# End Rant

class NewRant(object):
	# Takes in body and tags. used for storing data before post
	def __init__(self, body, tags):
		self.body = body
		self.tags = tags
	# End __init__
# End NewRant