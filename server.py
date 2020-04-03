# Part of this I'm following the tutorial at
# https://www.youtube.com/watch?v=RdSrkkrj3l4&t=565s
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import time, datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app, cors_allowed_origins="*")
list_users = []


@socketio.on('message')
def handleMessage(msg):
    print("Message: ", msg)
    send(msg, broadcast=True)


@socketio.on('activeUsers')
def handleActiveUsers():
    print('Received active users request.')
    print('Active userlist: ', list_users)
    emit('activeUsers', [{'username': username} for username in list_users])


@socketio.on('login')
def handleLogin(data):
    # socket.
    pass


# here join means joining a room, while later in this file on handling url, join means something different (see below)
@socketio.on('join')
def handleJoin(data):
    username, room = data['username'], data['room']
    join_room(room)
    emit('joinMessage', {'timestamp': data['timestamp'], 'message': "Welcome %s." % username, 'room': room}, room=room)
    print("%s has joined %s" % (username, room))


# ================================= ABOVE IS SOCKET IO.
# ================================= BELOW IS FLASK ROUTING.

# just to test css
@app.route('/template')
def template():
    return render_template('template.html')

@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')


@app.route('/chat')
@app.route('/chat/<username>')
def chat(username=None):
    if username is None or username not in list_users:
        return render_template('redirect.html', message="Username doesn't exist or is incorrect.",
                               location="welcome page", url=url_for('index'))
    return render_template('chat.html', username=username)


# here join means joining the chat lobby, not any room.
@app.route('/join', methods=['POST'])
def join():
    # logic: if username already exists, send ('join-result', 'alreadyExists')
    # else create a session and redirect user to chat.html
    username = request.form['username']
    print('Trying to join: ' + username)
    if username in list_users:
        print('Name %s already exists. Rejected.' % username)
        return jsonify({'result': False, 'username': username}), 201
    else:
        print('Taking %s to chat.' % username)
        list_users.append(username)
        print(request.base_url)
        return jsonify({'result': True, 'username': username}), 201


if __name__ == '__main__':
    socketio.run(app)
