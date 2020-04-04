//TODO: send message in a specific room. Leave chat. Display members in the chat. Display available chats.
    $(document).ready(function(){
        const username = '{{ username }}';
        $('#welcome').text(`Welcome, ${username}!`);
        const socket = io.connect(window.location.host);

        socket.on('connect', function () {
            socket.emit('join', {username: username, room: 'Lobby', timestamp: get_timestamp()});
        });

        socket.on('joinMessage', function(data){
            console.log(data);
            var msgTemplate = '<div class="message system-message-container"><div class="message message-header">System {{ timestamp }}</div><div class=" message message-text">{{ message }}</div></div>';
            var msgHTML = Mustache.to_html(msgTemplate, data);
            console.log(msgHTML);
           $('#message-window').append(msgHTML);
        });

        socket.on('message', function(data){
            console.log(data);
            var msgTemplate = '<div class="message message-container"><div class="message message-header">{{ username }} {{ timestamp }}</div><div class=" message message-text">{{ message }}</div></div>';
            var msgHTML = Mustache.to_html(msgTemplate, data);
            console.log(msgHTML);
           $('#message-window').append(msgHTML);
        });

        socket.on('disconnect', function () {
            socket.emit('disconnect', {username: username});
        });

        //=========ABOVE IS SOCKET BEHAVIOR
        //=========BELOW ARE FUNCTIONS

        function get_timestamp(){
            var d = new Date();
            //let h = d.getHours(), m = d.getMinutes(), s = d.getSeconds();
            const timestamp = d.toTimeString().substring(0,8);
            return timestamp;
        }

        function sendMessage(){
            if($('#message-input').val().length == 0){
                alert('Empty message.');
                return;
            }
            const timestamp = get_timestamp();
            const data = {username: username, timestamp: timestamp, message: $('#message-input').val()};
            //console.log(data);
            socket.send(data);
            $('#message-input').val('');
        };

        $('#message-input').keyup(function(event){
            if(event.which == 13){
                sendMessage();
            }
        });

        $('#sendButton').on('click', function(){
            sendMessage();
        });
    });