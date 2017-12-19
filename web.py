import os
import json
import bottle
import shelve
import hashlib
import datetime

from bottle import route, request, response

hostname = '0.0.0.0'
port = 80

user = {}
game = {}

session = {}

def isodatetime():
    return datetime.datetime.now().isoformat().encode('utf-8')

def auth():
    session_id = request.get_cookie('session_id')
    user_id = None
    if (not session_id) or (session_id not in session):
        user_id = 'user_' + hashlib.md5(isodatetime()).hexdigest()
        user[user_id] = dict(
            user_name = 'guest_' + (hashlib.md5(isodatetime()).hexdigest()[8:14])
        )
        session_id = 'session_' + hashlib.md5(isodatetime()).hexdigest()
        session[session_id] = dict(
            user_id = user_id
        )
        response.set_cookie('session_id', session_id)
    else:
        user_id = session[session_id]['user_id']
    return user_id

def enter(user_id):
    game_id = next((k for k, v in game.items() if user_id in v['user_data']), None)
    if not game_id:
        game_id = next((k for k, v in game.items() if len(v['user_data'])==1), None)
        if not game_id:
            game_id = 'game_' + hashlib.md5(isodatetime()).hexdigest()
            game[game_id] = dict(
                user_data = {},
                status = 'waiting',
                turn = 0
            )
        game[game_id]['user_data'][user_id] = dict(
            next_action = '',
            prev_result = '',
            win_count = 0
        )
        if len(game[game_id]['user_data']) == 2:
            game[game_id]['status'] = 'in battle'
            game[game_id]['turn'] = 1
    return game_id

def progress(game_id, user_id):
    if game[game_id]['status'] != 'in battle':
        return
    if 'next_action' in request.query:
        game[game_id]['user_data'][user_id]['next_action'] = request.query.next_action
    if any(v['next_action'] == '' for k, v in game[game_id]['user_data'].items()):
        return
    g = game[game_id]
    ud = g['user_data']
    p1 = ud[list(ud.keys())[0]]
    p2 = ud[list(ud.keys())[1]]
    pw = None
    pl = None
    if p1['next_action'] > p2['next_action']:
        pw = p1
        pl = p2
    else:
        pw = p2
        pl = p1
    pw['win_count'] += 1
    g['turn'] += 1
    p1['next_action'] = ''
    p2['next_action'] = ''
    return

@route('/logout')
def logout():
    response.delete_cookie('session_id')
    return "logout"

@route('/game')
def game_main():
    user_id = auth()
    game_id = enter(user_id)
    progress(game_id, user_id)
    return dict(
        user_id = user_id,
        game_id = game_id,
        debug_info = dict(
            game = game,
            session = session,
            user = user
        )
    )

@route('/')
@route('/<filename:path>')
def root(filename='index.html'):
    return bottle.static_file(filename, root='static')

bottle.run(host=hostname, port=int(os.environ.get('PORT', port)))
