$(function() {

    var cart = $('#cart'),
        cart_overlay = $('#cart-overlay');

    //cart.affix({offset: {top: 190}});

    function bind_cart_events() {
        cart.hover(
            function() { cart.addClass('expanded'); }, 
            function() { cart.removeClass('expanded'); }
        );
        cart.find('.footer a').tooltip();
    }

    function update_cart(url, data, callback) {
        cart_overlay.css({
            top: cart.offset().top,
            height: cart.height()
        }).show();
        $.post(url, data, function(html) {
            cart.html(html);
            bind_cart_events();
            cart_overlay.hide();
            callback && callback(true);
        }).error(function(fail) {
            if (fail.status == 400) {
                flash('This product cannot be added to the cart at the moment', 'error');
            } else {
                flash('An error occured while adding the product to the cart, please try again later', 'error');
            }
            cart_overlay.hide();
            callback && callback(false);
        });
    }

    $.get('/cart', function(html) {
        cart.html(html);
        bind_cart_events();
    });

    $(window).on('scroll', function() {
        cart_overlay.css({top: cart.offset().top});
    });

    $('.buy-buttons a.add-to-cart').on('click', function(e) {
        var self = $(this), btn = self;
        if (!btn.hasClass('btn')) {
            btn = btn.parents('.btn-group').find('a.btn');
        }
        btn.addClass('disabled');
        update_cart(this.href, {"id": self.data('id')}, function() {
            btn.removeClass('disabled');
        });
        e.preventDefault();
    });

    $('.buy-buttons .btn-group .btn').on('click', function(e) {
        $(this).parent().find('a.add-to-cart').each(function() {
            var self = $(this), imageurl = self.data('imageurl');
            if (imageurl) {
                img = new Image();
                img.src = imageurl;
                self.popover({
                    trigger: 'hover',
                    content: '<img src="' + img.src + '" />',
                    html: true
                });
            }
        });
    });

    cart.on('keypress', '.quantity input', function(e) {
        if (e.which != 13) return;
        var self = this, url = $(this).parents('tr').data('modify-url');
        self.disabled = true;
        update_cart(url, {"quantity": this.value}, function() {
            self.disabled = false;
        });
    });

});
