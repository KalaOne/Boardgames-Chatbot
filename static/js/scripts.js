let tag_message = "";
let tag_map = {
    "Choice": "{TAG:Yes/No}",
    "InfoType" : "{TAG:S/G}",
    "GENRE" : "{TAG:GENRE}",
    "NUM_PLAYERS":"{TAG:PLAYERS}",
    "PLAY_TIME" : "{TAG:TIME}",
    "CATEGORY": "{TAG:CATEGORY}",
        
    
}

// const sdk = window.SpeechSDK
// const speechConfig = sdk.SpeechConfig.fromSubscription("be0b6d81b60844a084339d50a0b79832", "uksouth");
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
        // console.log("Making a AJAX call");
        e.preventDefault();
        let message = getMessageText();
        makeAjaxCall(tag_message + " " + message);
        sendMessage(message);
    });

    $('.send_message').on("click", function () {
        let message = getMessageText();
        makeAjaxCall(tag_message + " " + message);
        sendMessage(message);
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
     tag_message = "";
    // create message object to be displayed in the chat area
    var msg = new Message({
        text: '',
        message_side: 'left'
    })
    // console.log("Message received in makeAjaxCall "+ user_input);
    // request to the backend
    $.ajax({
        type: 'POST',
        url: '/',
        datatype: "json",
        data: {"message_input" : user_input},
        success: function(output){
            msg.text = output.message;
            msg.response_required = output.response_required;
            console.log("background image???: " + output.background);
            if (output.background != false ){
                setBackgroundImage(output.background)
            };
            getControlTags(output.message);
            console.log("output to write:" + output.message)
            if (output.message) {
                setTimeout(() => {
                    msg.write();
                    scrollToBottom();    
                }, 500);
            }
            
            if(output.response_required === false){
                makeAjaxCall("BOTRESPONSE");
            }
            scrollToBottom();
        },
        error: function(e){
            console.log("Unable to send data to backend! " + e)
        }
    })
    console.log("User has written: " + user_input )
}

// Takes message and displays it to "messages" area
function Message(arg) {
    // console.log("text in Message object: " + arg.text);
    this.text = arg.text, this.message_side = arg.message_side;
    let author;
    
    if (this.message_side === 'left') { author = "bot";}
    else { author = "human"; }
    this.write = function (_this) {
        return function () {
            let $message;
            $message = $($('.message_template').clone().html());
            if (_this.text.message) {
                $message.addClass(_this.message_side).find('.text').html(_this.text.message.replace(/\s?\{[^}]+\}/g, ''));
            } else {
                $message.addClass(_this.message_side).find('.text').html(_this.text.replace(/\s?\{[^}]+\}/g, ''));
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

function setBackgroundImage(imageURL) {
    $('body').css("background", " url('"+imageURL+"') repeat").css("background-size", "450px, 450px");
}

// async function synthesizeSpeech(text) {
//     text = text.replace("AKOBot", "akobot")
//     text = text.replace("<br/>", "").replace("<br>", "").replace("</i>", "").replace("<i>", "")
//     let ssml = `<speak version="1.0" xmlns="https://www.w3.org/2001/10/synthesis" xml:lang="en-GB">
//                 <voice name="en-GB-RyanNeural">${text}</voice></speak>`
//     const audioConfig = sdk.AudioConfig.fromDefaultSpeakerOutput();
//     const synthesizer = new sdk.SpeechSynthesizer(speechConfig, audioConfig);
//     audioConfig.privDestination.privAudio.addEventListener("ended", function (){speaking=false})
//     while(speaking){
//         await sleep(200);
//     }
//     speaking = true;
//     synthesizer.speakSsmlAsync(
//         ssml,
//         result => {
//             if (result) {
//                 console.log(JSON.stringify(result));
//             }
//             console.log(synthesizer)
//             synthesizer.close();
//         },
//         error => {
//             console.log(error);
//             synthesizer.close();
//         });
// }

// function fromMic(){
//     let audioConfig = sdk.AudioConfig.fromDefaultMicrophoneInput();
//     let recognizer = new sdk.SpeechRecognizer(speechConfig, audioConfig);
    
//     $('.record-speech').addClass('animate');
//     recognizer.recognizeOnceAsync(result => {
//         console.log(`RECOGNIZED: Text=${result.text}`);
//         $('.record-speech').removeClass('animate');
//         $('.left-box').val(result.text); 
//         setTimeout(() => {
//             $('.send-message').click()
//         }, 1000);
//     });
// }

// Друга функция която може да извършва подобно нещо... Не е тествана, ама е нещо малко което може да го ТУРИШ
// Пробвай, може да стане, знае ли човек...
// Сорс - https://www.studytonight.com/post/javascript-speech-recognition-example-speech-to-text

// // new speech recognition object
// var SpeechRecognition = SpeechRecognition || webkitSpeechRecognition;
// var recognition = new SpeechRecognition();
            
// // This runs when the speech recognition service starts
// recognition.onstart = function() {
//     console.log("We are listening. Try speaking into the microphone.");
// };

// recognition.onspeechend = function() {
//     // when user is done speaking
//     recognition.stop();
// }
              
// // This runs when the speech recognition service returns result
// recognition.onresult = function(event) {
//     var transcript = event.results[0][0].transcript;
//     var confidence = event.results[0][0].confidence;
// };
              
// // start recognition
// recognition.start();