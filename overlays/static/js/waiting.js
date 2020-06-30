var connection = new WebSocket(ws_connection_string());
const container = document.getElementById("waitingScreen");
const checkins = document.getElementById('checkins');

//Uses {{ status }} context variable to see if a match is in progress


connection.onopen = function(event) {
    console.log('opened');

    //Page could have been refreshed. Send a request to the bot for checkins
    msg = {'type': 'request_checkins'};
    msg = JSON.stringify(msg);
    connection.send(msg);

};
function remove_checkins() {
    while (checkins.firstChild) {
        checkins.removeChild(checkins.firstChild);

    }
}

connection.onmessage = function(event) {
    const data = event.data;
    console.log(data);
    const obj = JSON.parse(data);
    if (obj.type == 'match_checkin') {
        appendCheckin(obj);

    }
    if (obj.type == 'match_checkout') {
        const player_checkin = document.getElementById(obj.player_id);
        player_checkin.remove();
    }
    if (obj.type == 'match_start') {
        remove_checkins();
        container.classList.add('animated', 'fadeOut');
        setTimeout(() => {
            container.style.display = 'none';
        }, 3000)
    }
    if (obj.type == 'response_checkins') {
        if (obj.hasOwnProperty('checkins')) {
            remove_checkins();
            obj.checkins.forEach(item => {
               appendCheckin(item);
            });
        }
    }
    if (obj.type == 'match_end') {
        //Have a delay to minimize the "flash" between scene transitions of match_end
        setTimeout(() => {
            // Refresh to grab updated context
            document.location.reload();
        },5000)

    }
};
function appendCheckin(obj) {
    var span = document.createElement("span");
    span.className = "checkins badge badge-light";
    span.id = obj.player_id;
    span.innerHTML = make_badge(obj);
    checkins.appendChild(span)
}
function make_badge(event) {
    const result = `
<div id="${event.player_id}" style="display: inline-flex; align-items: center;">
<div style="display: inline-flex; margin: 0 10px">
<img src="${event.player_avatar}" style="width: 30px; height: 30px; border-radius: 50%">
</div>
<div style="display: inline-block; vertical-align: middle">
   ${event.player}
</div>
        
</div>
    `;
    return result;
}