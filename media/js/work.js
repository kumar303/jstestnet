(function() {

// relies on global var WORKER_ID

var updateRate = 10, timeoutRate = 180,
    testTimeout, pauseTimer, testResults = {},
    workQueueId, workerId=WORKER_ID;

jQuery( doWork );

if ( window.addEventListener ) {
    window.addEventListener( "message", handleMessage, false );
} else if ( window.attachEvent ) {
    window.attachEvent( "onmessage", handleMessage );
}

var cmds = {
    run_test: function(params) {
        testResults = {};
        workQueueId = params.work_queue_id;
        log("Running: " +
            params.name + " at " + params.url +
            " [" + workQueueId.toString() + "]");

        var iframe = document.createElement("iframe");
        iframe.width = 1000;
        iframe.height = 600;
        iframe.className = "test";
        iframe.src = params.url + '?_=' + (new Date).getTime();
        jQuery("#iframes").append( iframe );

        var loadTimeout = 10000;
        var failedToLoad = setTimeout(function() {
            runtimeError('Failed to load the test suite in ' + loadTimeout/1000 + ' seconds');
        }, loadTimeout);

        jQuery(iframe).load(function(e) {
            clearTimeout(failedToLoad);
        });

        // The iframe must communicate back to us
        // with window.top.postMessage.
        // See handleMessage() for how those are received.

        // Timeout after a period of time
        testTimeout = setTimeout(function() {
            runtimeError('Timed out waiting for test results');
        }, timeoutRate * 1000 );
    },
    restart: function() {
        var noCache = true;
        window.location.reload(noCache);
    },
    change_rate: function( num ) {
        updateRate = parseInt( num );
    }
};

function doWork() {
    workQueueId = null;
    msg("Getting work from server...");
    retrySend("/work/query",
              {worker_id: workerId, user_agent: navigator.userAgent},
               doWork, doServerCmd);
}

function doServerCmd( data ) {
    if ( data.cmd ) {
        if ( typeof cmds[ data.cmd ] === "function" ) {
            cmds[ data.cmd ].apply( cmds, data.args );
        } else {
            log("Received an unknown command: " + data.cmd);
        }
    } else {
        clearTimeout( pauseTimer );

        var run_msg = data.desc || "No command from server.";

        msg(run_msg);

        var timeLeft = updateRate;

        pauseTimer = setTimeout(function leftTimer(){
            msg(run_msg + " Checking again in " + timeLeft + " seconds.");
            if ( timeLeft-- >= 1 ) {
                pauseTimer = setTimeout( leftTimer, 1000 );
            } else {
                doWork();
            }
        }, 1000);
    }
}

function done() {
    cancelTest();
    setTimeout(doWork, 3);
}

function cancelTest() {
    if ( testTimeout ) {
        clearTimeout( testTimeout );
        testTimeout = 0;
    }

    jQuery("iframe").remove();
}

function runtimeError(msg) {
    cancelTest();
    var msg = {
        test_run_error: true,
        test_run_error_msg: msg
    }
    log(msg.job_error_msg);
    retrySend('/work/submit_results', {
            work_queue_id: workQueueId,
            results: JSON.stringify(msg)
        },
        runtimeError, doWork );
}

function parseQueryStr(qs) {
    var obj = {},
        vars = qs.split("&");
    jQuery.each(vars, function(i, val) {
        var parts = val.split('=');
        obj[parts[0]] = decodeURI(parts[1]);
    });
    return obj;
}

function handleMessage(msg){
    var obj = parseQueryStr(msg.data);
    switch (obj.action) {
        case 'hello':
            testResults.user_agent = obj.user_agent;
            break;
        case 'set_test':
            testResults._current_test = obj.name;
            break;
        case 'set_module':
            testResults._current_module = obj.name;
            break;
        case 'log':
            if (typeof(testResults.tests) === 'undefined') {
                testResults.tests = [];
            }
            testResults.tests.push({
                module: testResults._current_module,
                test: testResults._current_test,
                result: obj.result == 'true' ? true: false,
                message: obj.message,
                stacktrace: obj.stacktrace
            });
            break;
        case 'done':
            log("failures: " + obj.failures + "; total: " + obj.total);
            testResults.failures = parseInt(obj.failures, 10);
            testResults.total = parseInt(obj.total, 10);
            retrySend( '/work/submit_results',
                        {work_queue_id: workQueueId,
                         results: JSON.stringify(testResults)},
                        function() {
                            handleMessage(msg);
                        }, done );
            break;
        default:
            throw new Error("Unknown action: " + obj.action);
            break;
    }
}

var errorOut = 0;

function retrySend( url, data, retry, success ) {
    jQuery.ajax({
        type: "POST",
        url: url,
        timeout: 10000,
        cache: false,
        data: data,
        error: function() {
            if ( errorOut++ > 4 ) {
                cmds.restart();
            } else {
                msg("Error connecting to server, retrying...");
                setTimeout( retry, 15000 );
            }
        },
        success: function(){
            errorOut = 0;
            msg("Sent data to server successfully");
            success.apply( this, arguments );
        },
        dataType: 'json'
    });
}

function log( txt ) {
    jQuery("#history").prepend( "<li><strong>" +
        (new Date).toString().replace(/^\w+ /, "").replace(/:[^:]+$/, "") +
        ":</strong> " + txt + "</li>" );
    msg( txt );
}

function msg( txt ) {
    jQuery("#msg").html( "[worker=" + workerId.toString() + "] " + txt );
}

})();
