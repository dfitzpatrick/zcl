function ws_connection_string() {
    var hostname = document.location.hostname;
    if (document.location.port) {
        hostname = hostname + ":" + document.location.port
    }
    var stream_id = document.location.pathname.match('\\d+')[0];
    var result ="ws://" + hostname + "/ws/obs/" + stream_id + "/";
    console.log(result);
    return result;
}
