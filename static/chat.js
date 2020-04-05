//TODO: Display members in the chat. Display available chats.
//TODO: trigger events: start chat, join chat, leave chat, leave app. Currently they can only be done in command line.
$(document).ready(function(){
    let username = $('#main-header').text();
    $('#main-header').text(`Welcome, ${username}!`);
    let socket = io.connect(window.location.host);
    let current_chat = 0, num_chats = 1;   //default to Lobby
    let listChats = {};     //[{chat_ID:, chat_name:, members:[]}]
    let first_time_lobby = true;

    socket.on('connect', function () {
        socket.emit('login', {username: username}, function(result) {
            if(result == 'reLogin'){
                console.log('Looks like we\'ve logged in before.');
                first_time_lobby = false;
            }
            else{
                console.log('Looks like it\'s the first time we\'ve logged in.');
                $('#alert-row').append('<div class="alert alert-info alert-dismissible fade show rounded-lg" role="alert" style=" position: absolute; top: 0; z-index: 9999; opacity: 90%;">\n' +
                    '            We don\'t use sessions so you can simulate multi-person chats on one host. For that reason, if you close the browser tag, you\'ll have to re-login using url \'/chat/&lt;username&gt;\'.\n' +
                    '          <button type="button" class="close" data-dismiss="alert" aria-label="Close">\n' +
                    '            <span aria-hidden="true">&times;</span>\n' +
                    '          </button>\n' +
                    '        </div>');
            }
            console.log('Trying to get joined chats');
            get_joined_chats(username, function(){
                console.log('We have now got joined chats');
                setCurrentChat(listChats[0].chat_ID);
                for(const i of Object.keys(listChats)){
                    //emits request and updates upon response.
                    get_chat_info(listChats[i].chat_ID);
                }
            });

        });
    });


    socket.on('systemMessage', function(data){
        let barrier = 0;
        const chat_ID = data.chat_ID;
        console.log('Received system message: ', data);
        if(jQuery.isEmptyObject(listChats) || listChats[chat_ID] == undefined){
            get_joined_chats(username, function(){
                barrier = Object.keys(listChats).length;
                for(const i of Object.keys(listChats)){
                    //emits request and updates upon response.
                    get_chat_info(listChats[i].chat_ID, handle);
                }
            });
        }
        else{
            do_work();
        }
        function handle(){
            //when all chats are updated, do the work. Otherwise do nothing.
            barrier--;
            if(barrier > 0) return;
            do_work();
        }
        function do_work(){

            const chat_ID = data.chat_ID, message = data.message;
            console.log('Handling system message: ', data);
            switch(data.msgType){
                case 'welcomeChat':
                    break;
                case 'joinChat':{
                    const members = listChats[chat_ID].members;
                    const index = members.indexOf(data.info.username);
                    if(index == -1){
                        members.push(data.info.username);
                    }
                    console.log('Now the members are: ', members);
                    //TODO: if is current chat, update display
                }
                    break;
                case 'leaveChat':{
                    const members = listChats[chat_ID].members;
                    const index = members.indexOf(data.info.username);
                    if(index > -1){
                        members.splice(index, 1);
                    }
                    console.log('Now the members are: ', members);
                    //TODO: if is current chat, update display
                }
                    break;
                case 'changeChatName':{
                    const this_chat = listChats[chat_ID];
                    this_chat.chat_name = data.info.newName;
                    if(current_chat == chat_ID){
                        $('#room-name').text(this_chat.chat_name);
                    }
                }
                    break;
            }
            listChats[chat_ID].chat_history.push({message: message, timestamp: data.timestamp, chat_ID: chat_ID, sender: 'System'});
            console.log('Now the chat_history looks like: ', listChats[chat_ID].chat_history);
            // TODO: display the message if is current chat

            // var msgTemplate = 'load from template';
            // var msgHTML = Mustache.to_html(msgTemplate, data);
           // $('#message-window').append(msgHTML);
        }
    });

    socket.on('chatMessage', function(data){
        const chat_ID = data.chat_ID, message = data.message, sender = data.sender, timestamp = data.timestamp;
        listChats[chat_ID].chat_history.push({message: message, timestamp: data.timestamp, chat_ID: chat_ID, sender: sender});
        //TODO: if is current chat, add message to window.
        console.log("Received: ", data);
    });

    socket.on('newChat', function(data){
        const chat_ID = data.chat_ID;
        join_chat(chat_ID);
        // console.log("New chat started: ", new_chat);
    });


    // socket.on('failed', function(msg){
    //     alert(msg);
    //     console.log('Failed: ', msg);
    // });


    //=========ABOVE IS SOCKET BEHAVIOR
    //=========BELOW ARE FUNCTIONS

    function start_chat(members){
        socket.emit('startChat', {members: members}, function(response){
            if(response.result == 'fail'){
                alert(response.message);
            }
            else{
                console.log('Starting chat with: ', members);
            }
        });
    }

    function join_chat(chat_ID) {
        socket.emit('join', {username:username, room: chat_ID.toString()}, function (data) {
            if(data.result == 'success'){
                console.log('Joined chat %d', chat_ID);
                listChats[chat_ID] = {chat_ID: chat_ID, chat_name: data.chat_info.chat_name, members: data.chat_info.members, chat_history: []};
            }
            else{
                alert(data.message);
            }
        });
    }

    function get_timestamp(){
        const d = new Date();
        //let h = d.getHours(), m = d.getMinutes(), s = d.getSeconds();
        const timestamp = d.toTimeString().substring(0,8);
        return timestamp;
    }

    //set the current chat in the chat window
    function setCurrentChat(chat_ID){
        current_chat = chat_ID;
        // if first time joining lobby, display a reminder.
        if(current_chat == 0 && first_time_lobby){
            first_time_lobby = false;
            $('#alert-row').append('<div class="alert alert-info alert-dismissible fade show rounded-lg" role="alert" style=" position: absolute; top: 0; z-index: 9990; opacity: 90%;">\n' +
                '            Welcome to the Lobby. You can start a chat with someone or join an existing chat, or just stay here!\n' +
                '          <button type="button" class="close" data-dismiss="alert" aria-label="Close">\n' +
                '            <span aria-hidden="true">&times;</span>\n' +
                '          </button>\n' +
                '        </div>')
        }
        const this_chat = listChats[chat_ID];
        $('#room-name').text(this_chat.chat_name);
        //TODO: load chat history in chat window. load chat members.
    }

    function sendMessage(chat_ID, message){
        if(message.length == 0){
            alert('Empty message.');
            return;
        }
        const timestamp = get_timestamp();
        const data = {sender: username, timestamp: timestamp, message: message, chat_ID: chat_ID};
        console.log("sending ", data);
        socket.emit('chatMessage', data);

        //for testing
        if(message.startsWith('sc')){
            const members = [username, message.substr(3)];
            console.log("Start chat detected in input. The other member is %s", members[1]);
            start_chat(members);
        }
        else if(message.startsWith('cc')){
            const chat_ID = parseInt(message.substr(3));
            setCurrentChat(chat_ID);
        }

        else if(message.startsWith('lc')){
            const chat_ID = parseInt(message.substr(3));
            leave_chat(chat_ID);
        }

        else if(message.startsWith('jc')){
            const chat_ID = parseInt(message.substr(3));
            join_chat(chat_ID);
        }
        else if(message === 'byebye'){
            leave_app();
        }


        $('#message-input').val('');
    };

    function get_chat_info(chat_ID, callback){
        socket.emit('chatInfo', {chat_ID: chat_ID}, function(data){
           //TODO: if is current chat, display the chat history
            const chat_ID = data.chat_ID/*, chat_history = data.chat_history*/;
            // listChats[chat_ID].chat_history = chat_history;
            if(listChats[chat_ID].chat_history == undefined){
                listChats[chat_ID].chat_history = [];
            }
            listChats[chat_ID].members = data.members;
            console.log("Received chat info of ", chat_ID);
            if(callback != undefined){
                callback();
            }
        });
    }

    function get_joined_chats(username, callback){
        console.log('Trying to get joined chats');
        socket.emit('joinedChats', {username: username}, function(data){
            console.log('Received joined chats.', data);
            listChats = data;
            if(listChats.length > 1){
                first_time_lobby = false;
            }
            if(callback != undefined){
                callback();
            }
        });
    }

    function leave_chat(chat_ID){
        socket.emit('leaveChat', {username: username, chat_ID: chat_ID});
        delete listChats[chat_ID];
        console.log('Now listChat looks like this: ', listChats);
    }

    function leave_app(){
      if (confirm("Are you sure you want to quit the app?")) {
          socket.emit('byebye', {username:username});
      }
    }

    function change_chat_name(chat_ID, newName){
        socket.emit('changeChatName', {username:username, chat_ID:chat_ID, newName:newName});
    }
    $('#button-send-message').keyup(function(event){
        if(event.which == 13){
            sendMessage(current_chat, $('#message-input').val());
        }
    });

    $('#button-send-message').on('click', function(event){
        console.log($(this));
        event.preventDefault();
        sendMessage(current_chat, $('#message-input').val());
    });

});
