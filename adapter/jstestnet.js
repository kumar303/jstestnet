//
// Adapter for JS TestNet
// https://github.com/kumar303/jstestnet
//
// Be sure this file is loaded *after* qunit/testrunner.js or whatever else
// you're using

(function() {

    var canPost = false;
    try {
        canPost = !!window.top.postMessage;
    } catch(e){}
    if (!canPost) {
        return;
    }

    function postMsg(data) {
        var msg = '';
        for (var k in data) {
            if (msg.length > 0) {
                msg += '&';
            }
            msg += k + '=' + encodeURI(data[k]);
        }
        window.top.postMessage(msg, '*');
    }

    function replaceChars(aStr) {
        aStr = aStr.replace(/&amp;/g, '&');
        aStr = aStr.replace(/&gt;/g, '>');
        aStr = aStr.replace(/&lt;/g, '<');
        aStr = aStr.replace(/<[^>]+>/g, '');
				aStr = aStr.replace(/\n/g,'');
        return aStr;
    }
    window.onerror = function(errorMsg, url, lineNumber) {
        var msg = {
            action: 'log',
            result: false, // failure
            message: 'Exception: ' + errorMsg + ' at ' + url + ':' + lineNumber,
            // TODO(Kumar) add stacktrace on platforms that support it
            // (like Firefox)
            stacktrace: null
        };
        postMsg(msg);
    };
    

    if ( typeof doctest !== "undefined") {
        this.doctestReporterHook = {
            init : function (reporter,verbosity) {
                postMsg({
                        action: 'hello',
                        user_agent: navigator.userAgent
                });
								postMsg({
                				action: 'set_module',
                				name: window.location.pathname
            		});
            },
            reportSuccess : function (example, output) {
                var example_out = replaceChars(example.output);
                var output_out = replaceChars(output);
                var msg = {
                            action: 'log',
                            result: true,
                            message: example.htmlID,
                            stacktrace: null
                };
                postMsg({
                  action: 'set_test',
                  name: example.htmlID
                });
                msg.actual = output_out;
                msg.expected = example_out;
                postMsg(msg);
            },
            reportFailure : function (example, output) {
                var example_out = replaceChars(example.output);
                var output_out = replaceChars(output);
                var msg = {
                            action: 'log',
                            result: false,
                            message: example.htmlID,
                            stacktrace: null
                };
                msg.actual = output_out;
                msg.expected = example_out;
                postMsg(msg);
            }, 
            finish: function(reporter) {
                postMsg({
                    action: 'done',
                    failures: reporter.failure,
                    total: reporter.failure + reporter.success
                });
            }
        };
    }
    // QUnit (jQuery)
    // http://docs.jquery.com/QUnit
    else if ( typeof QUnit !== "undefined" ) {

        QUnit.begin = function() {
            postMsg({
                action: 'hello',
                user_agent: navigator.userAgent
            });
        };

        QUnit.done = function(failures, total) {

            postMsg({
                action: 'done',
                failures: failures,
                total: total
            });
        };

        QUnit.log = function(details) {
            // Strip out html:
            var message = details.message;
            var result = details.result;
          
            message = message.replace(/&amp;/g, '&');
            message = message.replace(/&gt;/g, '>');
            message = message.replace(/&lt;/g, '<');
            message = message.replace(/<[^>]+>/g, '');
            var msg = {
                action: 'log',
                result: result,
                message: message,
                stacktrace: null
            };
            if (details) {
                if (typeof(details.source) !== 'undefined') {
                    msg.stacktrace = details.source;
                }
                if(typeof(details.actual) !== 'undefined' &&
                   typeof(details.expected) !== 'undefined') {
                    msg.actual = details.actual;
                    msg.expected = details.expected;
                }
            }
            postMsg(msg);
        };

        QUnit.moduleStart = function(name) {
            postMsg({
                action: 'set_module',
                name: name
            });
        };

        QUnit.testStart = function(name) {
            postMsg({
                action: 'set_test',
                name: name
            });
        };

        // window.TestSwarm.serialize = function(){
        //  // Clean up the HTML (remove any un-needed test markup)
        //  remove("nothiddendiv");
        //  remove("loadediframe");
        //  remove("dl");
        //  remove("main");
        //
        //  // Show any collapsed results
        //  var ol = document.getElementsByTagName("ol");
        //  for ( var i = 0; i < ol.length; i++ ) {
        //      ol[i].style.display = "block";
        //  }
        //
        //  return trimSerialize();
        // };
    } else {
        throw new Error("Cannot adapt to jstestnet: Unknown test runner");
    }

})();
