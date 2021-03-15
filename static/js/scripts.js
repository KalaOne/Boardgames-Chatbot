
// Document.ready
$(function () {

    var openinMessage = new Message({
        // text: "Greetings user! I can help with any board game related topic. Let me know what you desire.",
        text: "Greetings user! I can give you information for a few board games (for now). \
                Specify a game and continue with your questions. If you want to know the \
                supported list of games, type 'help'.",
        message_side: 'left'
    });
    openinMessage.write();

    $('.send_message').on("click", function () {
        makeAjaxCall(getMessageText());
        return sendMessage(getMessageText());
    });
    $('.message_input').on("keyup", function (e) {
        if (e.which === 13) {
            makeAjaxCall(getMessageText());
            return sendMessage(getMessageText());
        }
    });

});

function scrollToBottom() {
    $messages = $('.messages');
    return $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 300);
}

// Sends the actual input to be displayed.
function getMessageText() {
    var $message_input = $('.message_input');
    return $message_input.val();
};

function sendMessage(text) {
    var message;
    if (text.trim() === '') {
        return;
    }
    $('.message_input').val('');
    message = new Message({
        text: text,
        message_side: 'right'
    });
    message.write();
    return scrollToBottom();
};

 // sends user input to backend for processing
 function makeAjaxCall(user_input) {
    // create message object to be displayed in the chat area
    var msg = new Message({
        text: '',
        message_side: 'left'
    })
    console.log("Message received in makeAjaxCall "+ user_input);
    // request to the backend
    $.ajax({
        type: 'POST',
        url: '/',
        datatype: "json",
        data: {"message_input" : user_input},
        success: function(output){
            msg.text = output.message;
            msg.response_required = output.response_required;
            if (user_input) {
                msg.write();
            }
            if(output.response_required === false){
                console.log("HEY BOT");
                makeAjaxCall("BOTRESPONSE");
            }
            scrollToBottom();
        },
        error: function(e){
            console.log("Unable to send data to backend! " + e)
        }
    })
    
}

// Takes message and displays it to "messages" area
function Message(arg) {
    console.log("text in Message object: " + arg.text);
    this.text = arg.text, this.message_side = arg.message_side;
    let author;
        
    if (this.message_side === 'left') { author = "bot";}
    else { author = "human"; }
    this.write = function (_this) {
        return function () {
            var $message;
            $message = $($('.message_template').clone().html());
            if (_this.text.message) {
                $message.addClass(_this.message_side).find('.text').html(_this.text.message);
            } else {
                $message.addClass(_this.message_side).find('.text').html(_this.text);
            }
        
            $('.messages').append($message);
            return setTimeout(function () {
                return $message.addClass('appeared');
            }, 0);
        };
    }(this);
    return this;
};