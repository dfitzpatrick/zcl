
function ws_connection_string() {
    var hostname = document.location.hostname;
    if (document.location.port) {
        hostname = hostname + ":" + document.location.port
    }
    var stream_id = document.location.pathname.match('\\d+')[0];
    var result ="ws://" + hostname + "/events/" + stream_id + "/";
    console.log(result);
    return result;
}
var connection = new WebSocket(ws_connection_string());
var queue = new MessageQueue("#msgDisplay", null, {
            startAnimation: 'fadeInLeft',
            endAnimation: 'fadeOutLeft',
            animatedElement: '#animatedElement',
            avatar: '#avatar'
        });


connection.onopen = function(event) {
    console.log("Connected");
};
connection.onmessage = function(event) {

    const obj = JSON.parse(event.data);
        console.log(obj);
    if (obj.hasOwnProperty('payload')) {
        if (obj.payload.hasOwnProperty('alert_message')) {
          console.log("Adding object to queue")
          var msg = obj.payload.alert_avatar + ';' + obj.payload.alert_message;
          queue.addMessages(msg);
        }

    }
};
