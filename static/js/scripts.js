
// Document.ready
$(function () {

    var openinMessage = new Message({
        // text: "Greetings user! I can help with any board game related topic. Let me know what you desire.",
        text: "Greetings user! I can give you information about Chess. Go ahead and ask your questions. E.g. 'How to play' or 'Information'.",
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

    // var imageBot = document.createElement("img");
    // var imageYou = document.createElement("img");
    // var imageLocation = $("avatar");
    // imageBot.src = "C:/Users/Home/Desktop/Uni work/Year 3/Project/Boardgames Chatbot/static/images/bot.png";
    
});

// Sends the actual input to be displayed.
function getMessageText() {
    var $message_input = $('.message_input');
    return $message_input.val();
};

function sendMessage(text) {
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
    message.write();
    return $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 300);
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
            console.log(output.message);
            msg.text = output.message;
            msg.response_required = output.response_required;
            if (user_input) {
                msg.write();
            }
            if(msg.response_required === false){
                makeAjaxCall("BOTRESPONSE");
            }
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
            console.log($message);
            $('.messages').append($message);
            return setTimeout(function () {
                return $message.addClass('appeared');
            }, 0);
        };
    }(this);
    return this;
};