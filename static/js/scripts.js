
let tag_map = {
    "choice": "{TAG:Yes/No}",
    
}

// Document.ready
$(function () {

    var openinMessage = new Message({
        // text: "Greetings user! I can help with any board game related topic. Let me know what you desire.",
        text: "Greetings user! I can give you information for a few board games (for now). \
                Specify a game and continue with your questions. If you want to know the \
                supported list of games, type 'help'.",
        message_side: 'left'
    });

    // Send opening message to UI
    makeAjaxCall("");

    // openinMessage.write();
    $('#form-id').submit(function (e) {
        console.log("Making a AJAX call");
        e.preventDefault();
        let message = getMessageText();
        makeAjaxCall(message);
        sendMessage(message);
    });

    $('.send_message').on("click", function () {
        makeAjaxCall(getMessageText());
        return sendMessage(getMessageText());
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

function sendMessage(text, first = false) {
    var message;
    if (text.trim() === '' && !first) {
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
            if (output.message) {
                setTimeout(() => {
                    msg.write();    
                }, 500);
            }
            console.log("Message received with tag: "+output.message);
            getControlTags(output.message);
            if(output.response_required === false){
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

function getControlTags(messageText){
    // Handles tags in the message, where user needs to response for specific question.
    let regex = new RegExp('{([^}]+)}', 'g');
    let results = [...messageText.matchAll(regex)]
    results.forEach(function(element){
        let tagArr = element[1].split(":");
        let tag = tagArr[0], value = tagArr[1];
        switch (tag){
            case 'REQ':
                tag_message += tag_map[value];
                break;
            default:
                break;
        }
    });
}