import os
import json
import bottle
import shelve
import hashlib
import datetime

from bottle import route, request, response

hostname = 'localhost'
port = 80

game = {}

game_inital = {
	"gameid": None,
	"userid": []
}

def auth():
	userid = request.get_cookie('userid')
	if not userid:
		userid = hashlib.md5(datetime.datetime.now().isoformat().encode('utf-8')).hexdigest()[:16]
		response.set_cookie('userid', userid)
	return userid

def enter(userid):
	gameid = None
	for k, v in game.items():
		if userid in v['userid']:
			gameid = k
	if not gameid:
		for k, v in game.items():
			if len(v['userid']) == 1:
				gameid = k
				v['userid'].append(userid)
		if not gameid:
			gameid = hashlib.md5(datetime.datetime.now().isoformat().encode('utf-8')).hexdigest()
			game[gameid] = game_inital
			game[gameid]['gameid'] = gameid
			game[gameid]['userid'] = [userid]
	return gameid

@route('/logout')
def logout():
	response.delete_cookie('userid')
	return "logout"

@route('/test')
def test():
	userid = auth()
	gameid = enter(userid)
	return {'userid': userid,'game': game[gameid]}

@route('/')
@route('/<filename:path>')
def root(filename='index.html'):
	return bottle.static_file(filename, root='static')

bottle.run(host=hostname, port=int(os.environ.get('PORT', port)))