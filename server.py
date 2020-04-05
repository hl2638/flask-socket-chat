# Part of this I'm following the tutorial at
# https://www.youtube.com/watch?v=RdSrkkrj3l4&t=565s
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from chatAndMessageClass import Chat, Message
from datetime import datetime
import time, json, threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app, cors_allowed_origins="*")
list_users = []  # [username]
logged_in = {}  # {username: boolean}
# chat_ID is the index of the list, also the room name (to string)
list_chats = [Chat(chat_ID=0, list_members=[], name='Lobby')]   # [Chat object]
# {user: [chat_ID]}
list_joined_chats = {}  # {username: [chat_ID]}
num_chats = 1
started_broadcast = False

# TODO: change chat name.


def chat_ID_to_room(chat_ID):
    if chat_ID == 0:
        return 'Lobby'
    else:
        return str(chat_ID)


def room_to_chat_ID(room):
    if room == 'Lobby':
        return 0
    else:
        return int(room)


def time_to_string(timestamp):
    return timestamp.strftime("%H:%M:%S")


def string_to_time(string):
    return datetime.strptime(string, "%H:%M:%S")


# broadcast to welcome page: list of active users
def welcome_broadcast():
    print("Start broadcasting to welcome page")
    while True:
        time.sleep(1)
        # print('emitting activeUsers')
        socketio.emit('activeUsers', [{'username': username} for username in list_users], room='Welcome')


# make sure we're only doing the thread once
def start_welcome_broadcast():
    global started_broadcast
    if started_broadcast:
        return
    else:
        print("starting broadcast to welcome page")
        started_broadcast = True
        socketio.start_background_task(target=welcome_broadcast)


# send system message to a room
def send_system_message(msgType, info, message, chat_ID):
    timestamp = datetime.now()
    data = {'msgType': msgType, 'info': info, 'message': message, 'timestamp': time_to_string(timestamp), 'chat_ID': chat_ID}
    emit('systemMessage', data, room=chat_ID_to_room(chat_ID))
    list_chats[chat_ID].new_message(data['message'], sender='System', time=timestamp)
    print("Sending system message: '%s' to room %s." % (message, chat_ID_to_room(chat_ID)))


# forward message sent by user to the whole room
def forward_chat_message(message, timestamp, sender, chat_ID):
    data = {'message': message, 'timestamp': time_to_string(timestamp), 'chat_ID': chat_ID, 'sender': sender}
    emit('chatMessage', data, room=chat_ID_to_room(chat_ID))
    list_chats[chat_ID].new_message(message, sender=sender, time=timestamp)
    print("Forwarding system message: \"%s\" to room %s." % (message, chat_ID_to_room(chat_ID)))


def leave_chat(username, chat_ID):
    list_chats[chat_ID].remove_member(username)
    send_system_message("leaveChat", {'username': username, 'chat_ID': chat_ID}, "%s has left the chat." % username, chat_ID)


@socketio.on('visit')
def handleVisit():
    print("Someone has visited the homepage.")
    join_room('Welcome')
    start_welcome_broadcast()  # Don't worry. We're only doing the broadcast thread once.


# when someone logs in to the chat page
@socketio.on('login')
def handleLogin(data):
    username = data['username']
    # exception handling
    if logged_in.get(username) is None:
        return

    # if re-logging in, just respond with a message.
    if logged_in[username]:
        print("%s has re-logged in." % username)
        return 'reLogin'
    else:
        logged_in[username] = True
        send_system_message('joinChat', {'username': username}, "Welcome %s." % username, 0)
        list_joined_chats[username] = [0]   # joined Lobby
        join_room(username)     # join own private room for system messages.
        join_room('Lobby')
        list_chats[0].add_member(username)  # add user to member list of lobby.
        print("%s has logged in and joined the Lobby." % username)
        return 'firstTime'


# when someone starts a chat
@socketio.on('startChat')
def handleStartChat(data):
    # remove duplicates
    members = list(set(data['members']))  # [username]
    success = True
    error_message = ""
    if len(members) == 1:
        success = False
        error_message = "You can't start a chat with yourself."
    else:
        for user in members:
            if user not in list_users:
                success = False
                error_message = 'Failed to start chat. Some of the users don\'t exist or have quit.'
                break

    if success:
        global num_chats
        # set members to empty list. Flask-socketio is a shit lib that doesn't support managing random sockets. We have to let the users join by themselves. If user was already in members then join would fail
        new_chat = Chat(num_chats, name='New Chat')
        list_chats.append(new_chat)
        num_chats += 1
        chat_info = {'chat_ID': new_chat.chat_ID, 'chat_name': new_chat.name, 'members': members}
        for user in members:
            emit('newChat', chat_info, room=user)
            # list_joined_chats[user].append(new_chat.chat_ID)
        # send_system_message('welcomeChat', {}, "Welcome to the new chat.", chat_ID=new_chat.chat_ID)
        print("New Chat started: ", chat_info)
        return {'result': 'success'}
    else:
        print("Failed to start chat. Some of the users don\'t exist or have quit.")
        return {'result': 'fail', 'message': error_message}


# here join means joining a room, while later in this file on handling url for flask, join means something different (see below)
@socketio.on('join')
def handleJoin(data):
    username, room = data['username'], data['room']
    chat_ID = room_to_chat_ID(room)
    if chat_ID in list_joined_chats[username]:
        print('Failed to join chat. Already in the chat.')
        return {'result': 'fail', 'message': 'Failed to join chat. Already in the chat.'}
    elif list_chats[room_to_chat_ID(room)]:
        list_chats[chat_ID].add_member(username)
        list_joined_chats[username].append(chat_ID)
        send_system_message('joinChat', {'username': username, 'chat_ID': chat_ID}, "Welcome %s." % username, chat_ID)
        join_room(room)
        print("%s has joined %s" % (username, room_to_chat_ID(chat_ID)))
        chat_info = {'chat_ID': chat_ID, 'chat_name': list_chats[chat_ID].name, 'members': list_chats[chat_ID].list_members}
        return {'result': 'success', 'chat_info': chat_info}
    else:
        print('Failed to join chat. Chat no longer exists.')
        return {'result': 'fail', 'message': 'Failed to join chat. Chat no longer exists.'}


# when use leaves a chat
@socketio.on('leaveChat')
def handleLeave(data):
    username, chat_ID = data['username'], data['chat_ID']
    list_joined_chats[username].remove(chat_ID)
    leave_room(chat_ID_to_room(chat_ID))
    leave_chat(username, chat_ID)


@socketio.on('byebye')
def handleByebye(data):
    username = data['username']
    for chat_ID in list_joined_chats[username]:
        list_chats[chat_ID].remove_member(username)
    list_joined_chats.pop(username)
    logged_in.pop(username)
    list_users.remove(username)
    print('A user has said byebye. We still have: ', list_users)


@socketio.on('chatMessage')
def handleChatMessage(data):
    chat_ID, sender, timestamp, message = data['chat_ID'], data['sender'], string_to_time(data['timestamp']), data[
        'message']
    forward_chat_message(message, timestamp, sender, chat_ID)


@socketio.on('changeChatName')
def handleChangeChatName(data):
    username, chat_ID, newName = data['username'], data['chat_ID'], data['newName']
    if chat_ID == 0:  # Lobby can't be changed
        return
    this_chat = list_chats[chat_ID]
    this_chat.change_name(newName)
    send_system_message('changeChatName', {'username': username, 'chat_ID': chat_ID, 'newName': newName}, "%s changes chat name to %s." % (username, this_chat.name), chat_ID)
    print("%s changes %d name to %s." % (username, chat_ID, this_chat.name))


# when client wants to reload chat list
@socketio.on('joinedChats')
def handleJoinedChats(data):
    username = data['username']
    user_joined_chats = [list_chats[cid].to_data() for cid in list_joined_chats[username]]
    return user_joined_chats
    print("%s requesting joined chats. Responded." % username)


@socketio.on('chatInfo')
def handleChatInfo(data):
    chat_ID = data['chat_ID']
    # chat_history = [message.to_data() for message in list_chats[chat_ID].chat_history]
    # print("chat history looks like: ", chat_history)
    # return {'chat_ID': chat_ID, 'chat_history': chat_history, 'members': list_chats[chat_ID].list_members}
    return {'chat_ID': chat_ID, 'members': list_chats[chat_ID].list_members}

# ================================= ABOVE IS SOCKET IO.
# ================================= BELOW IS FLASK ROUTING.


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
        print('Name "%s" already exists. Rejected.' % username)
        return jsonify({'result': False, 'username': username}), 201
    else:
        print('Taking %s to chat.' % username)
        list_users.append(username)
        logged_in[username] = False
        print(request.base_url)
        return jsonify({'result': True, 'username': username}), 201


if __name__ == '__main__':
    socketio.run(app)
