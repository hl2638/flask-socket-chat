$(document).ready(function() {
    var socket = io.connect(window.location.host);
    socket.on('connect', function () {
        socket.send('A new user has visited the welcome page!');
    });

    setInterval(function(){
        console.log('Sending activeusers request.');
        socket.emit('activeUsers');
    }, 1000);

    socket.on('activeUsers', function (data) {
        console.log('received active users.');
        console.log(data);
        if(data.length > 0){
            $("#active-user-list").html('');
            for(var i=0; i<data.length; i++){
                var msgTemplate = '<li class="list-group-item rounded">{{ username }}</li>';
                var msgHTML = Mustache.to_html(msgTemplate, data[i]);
                $("#active-user-list").append(msgHTML);
            }
        }
        else{
            $("#active-user-list").html('<li class="list-group-item rounded">No active users for now...</li>');
        }

    });

    $('#join-form').submit(function (event) {
        console.log('submitting form');
        $.ajax({
            url: '/join',
            data: $(this).serialize(),
            type: 'POST',
            success: function(response) {
                console.log($(this).serialize());
                console.log(response);
                console.log(response["result"]);
                if(!response.result){
                    alert('Username ' + response.username + ' has already been used.');
                }
                else{
                    window.location.href = 'chat/' + response.username;
                }
            },
            error: function(error){
                alert(error);
                console.log(error);
            }
        });
        event.preventDefault();
    });
});