
$(document).ready(function() {

if ($('#debug-in-worker').length) {
    initDebugInWorker();
}

function initDebugInWorker() {
    var workerId = WORKER_ID,
        $log = $('#log'),
        $input = $('#console'),
        history = [],
        historyIdx = 0,
        socket = new io.Socket(window.location.hostname,
                               {port: 8889,
                                // resource: 'socket.io/debug/' + workerId,
                                resource: 'socket.io',
                                rememberTransport: false,
                                secure: false,  // TODO(Kumar) when we have SSL
                                // transports: ['xhr-polling']
                                }),
        keys = {ENTER: 13,
                UP: 38,
                DOWN: 40};
    socket.connect();

    socket.on('connect', function() {
        console.log('Connected to debug server');
    });

    socket.on('message', function(data) {
        var result;
        if (data.worker_id != workerId) {
            console.log('Ignoring message; wrong worker ID ' + data.worker_id);
            // TODO(Kumar) this is dumb
            return;
        }
        switch (data.action) {
            case 'result':
                $log.append('<p>> ' + data.code + '</p>');
                if (typeof data.exception !== 'undefined') {
                    result = '<i>' + data.exception + '</i>';
                } else if (typeof data.value === 'undefined') {
                    result = '<i>undefined</i>';
                } else {
                    result = '<pre>' + data.value + '</pre>';
                }
                $log.append(result);
                break;
            case 'worker_connected':
                $('#console-area').removeClass('loading');
                $('#console-area input').focus();
                break;
            default:
                console.log('Unhandled message: (' + typeof(data) + ') action=' + data.action)
                break;
        }
    });

    $input.bind('keydown', function(e) {
        var inputBuf = '';
        switch (e.which) {
            case keys.ENTER:
                history.push($input.val());
                socket.send({action: 'eval',
                             code: $input.val(),
                             worker_id: workerId});
                $input.val('');
                historyIdx = history.length;
                e.preventDefault();
                break;
            case keys.UP:
            case keys.DOWN:
                inputBuf = $input.val();
                if (e.which == keys.UP) {
                    historyIdx--
                } else {
                    historyIdx++
                }
                $input.val( history[historyIdx] || inputBuf);
                if (historyIdx > history.length) {
                    historyIdx = history.length;
                } else if (historyIdx < 0) {
                    historyIdx = 0;
                }
                break;
            default:
                break;
        }
    });
}

});
