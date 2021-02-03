(function () {
    var Message;
    // var imageBot = document.createElement("img");
    // var imageYou = document.createElement("img");
    // var imageLocation = $("avatar");
    // imageBot.src = "C:/Users/Home/Desktop/Uni work/Year 3/Project/Boardgames Chatbot/bot.png";
    
    // Takes message and displays it to "messages" area
    Message = function (arg) {
        this.text = arg.text, this.message_side = arg.message_side;
        this.draw = function (_this) {
            return function () {
                var $message;
                $message = $($('.message_template').clone().html());
                $message.addClass(_this.message_side).find('.text').html(_this.text);
                $('.messages').append($message);
                // if (this.message_side === "left") {
                //     imageLocation.append(imageBot);
                // }
                // else if(this.message_side === "right") {
                //     imageLocation.append(imageYou);
                // }
                return setTimeout(function () {
                    return $message.addClass('appeared');
                }, 0);
            };
        }(this);
        return this;
    };
    // sends user input to backend for processing
    sendInputData = function (user_input) {
        // create message object to be displayed in the chat area
        var msg = new Message({
            text: '',
            message_side: 'left'
        })
        // request to the backend
        $.ajax({
            type: 'POST',
            url: '/bot',
            data: user_input,
            success: function(output){
                console.log(output);
                msg.text = output;
                if (user_input) {
                    msg.draw();
                }
            },
            error: function(e){
                console.log("Unable to send data to backend! " + e)
            }
        })
        console.log(user_input)
    }

    // Sends the actual input to be displayed.
    $(function () {
        var getMessageText, sendMessage;
        getMessageText = function () {
            var $message_input;
            $message_input = $('.message_input');
            return $message_input.val();
        };
        sendMessage = function (text) {
            var $messages, message;
            if (text.trim() === '') {
                return;
            }
            $('.message_input').val('');
            $messages = $('.messages');
            message = new Message({
                text: text,
                message_side: 'right'
            });
            message.draw();
            return $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 300);
        };
        $('.send_message').click(function () {
            sendInputData(getMessageText());
            return sendMessage(getMessageText());
        });
        $('.message_input').keyup(function (e) {
            if (e.which === 13) {
                sendInputData(getMessageText());
                return sendMessage(getMessageText());
            }
        });
        sendMessage('Hello Bot! :)');
    });
}.call(this));