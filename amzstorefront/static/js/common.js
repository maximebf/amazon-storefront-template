
function flash(message, type) {
    var alert = $('<div class="alert alert-' + type + '">' +
        '<button type="button" class="close" data-dismiss="alert">&times;</button>' +
        message + '</div>');
    $('#flash-messages').append(alert);
    setTimeout(function() { alert.fadeOut(); }, 5000);
}


$(function() {
    $('#flash-messages .alert').each(function() {
        var self = $(this);
        setTimeout(function() { self.fadeOut(); }, 5000);
    });
});
