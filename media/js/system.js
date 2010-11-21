
$(document).ready(function() {

    $('.start-tests').click(function(e) {
        var el = $(this);
        $.ajax({
    		type: "GET",
    		url: el.attr('href'),
    		timeout: 10000,
    		cache: false,
    		error: function() {
                throw new Error("server error, do something!");
    		},
    		success: function(data) {
    		    var oldText = el.text();
                el.text("tests started, job_id=" + data.job_id);
                setTimeout(function() { el.text(oldText) }, 10);
    		},
    		dataType: 'json'
        });
        e.preventDefault();
    });

});
