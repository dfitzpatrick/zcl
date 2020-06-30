var qs = new URLSearchParams(document.location.search);
var connection = new WebSocket(ws_connection_string());
const endScreen = document.getElementById("endScreen");
var nextMatch = document.getElementById("next");
nextMatch.style.display = 'none';
// Hide this view unless it has a show parameter
if (qs.has('show')) {
    console.log('Showing');
    setTimeout(() => {
        nextMatch.style.display = 'block'
    }, 10000);

    setTimeout(() => {
        endScreen.classList.add('animated', 'fadeOut');
        setTimeout(() => {
            endScreen.style.display = 'none';
        }, 3000)
                }, 60000);
} else {
    endScreen.style.display = 'none';
}
// Show we are connected
connection.onopen = function(event) {
    console.log("Connected");
};

connection.onmessage = function(event) {
    const obj = JSON.parse(event.data);
    if (obj.type == 'match_end') {
        // Match has ended. We reload to get updated context from the server.
        // But give the server some time to process
        window.location.href = window.location.protocol + "//" + window.location.host + window.location.pathname + '?show=' + obj.game_id;
    }
};
