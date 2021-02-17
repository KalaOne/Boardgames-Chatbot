
// Document.ready
$(function () {

    var openinMessage = new Message({
        text: "Greetings user! I can help with any board game related topic. Let me know what you desire.",
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
    console.log("getMessage")
    var $message_input = $('.message_input');
    return $message_input.val();
};

function sendMessage(text) {
    console.log("Send message")
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
     console.log("Send input data")
    // create message object to be displayed in the chat area
    var msg = new Message({
        text: '',
        message_side: 'left'
    })
    // request to the backend
    $.ajax({
        type: 'POST',
        url: '/',
        datatype: "json",
        data: {"message_input" : user_input},
        success: function(output){
            console.log(output);
            msg.text = output;
            if (user_input) {
                msg.write();
            }
        },
        error: function(e){
            console.log("Unable to send data to backend! " + e)
        }
    })
}

// Takes message and displays it to "messages" area
function Message(arg) {
    this.text = arg.text, this.message_side = arg.message_side;
    let author;
    if (this.message_side === 'left') { author = "bot";}
    else { author = "human"; }
    this.write = function (_this) {
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