from flask import Blueprint, current_app, render_template, request, g, session, jsonify, abort, redirect, url_for
from amzstorefront.models import *
from amzstorefront.utils import *
from amzstorefront.amazon import Cart, InvalidCartItem
import time


blueprint = Blueprint('store', __name__)


@blueprint.before_request
def setup_request_globals():
    if 'cart_id' in session and 'cart_hmac' in session:
        g.cart = Cart.load(session['cart_id'], session['cart_hmac'], session.get('cart_assoc_tag'))
    else:
        g.cart = Cart()

    if 'afftag' in session and session['afftag_expiry'] < time.time():
        del(session['afftag'])
        del(session['afftag_expiry'])
        if not g.cart.created:
            session.permanent = False
            
    g.categories = Category.query.all()


@blueprint.after_request
def save_cart_after_request(response):
    if g.cart.created and g.cart.modified:
        session['cart_id'] = g.cart.id
        session['cart_hmac'] = g.cart.hmac
        session['cart_assoc_tag'] = g.cart.assoc_tag
        g.cart.persist(current_app.config['CART_TTL'])
    return response


@blueprint.route('/')
def home():
    return redirect(url_for('.all_products'))
    return render_template('store/index.html')


@blueprint.route('/all')
def all_products():
    products = Product.query.filter_by(parent_id=None).all()
    return render_template('store/product_list_page.html', list_title='All categories', 
        products=products)


@blueprint.route('/<slug>')
def show_category(slug):
    category = Category.find_by_slug(slug)
    if not category:
        return abort(404)
    g.active_category_id = category.id
    return render_template('store/product_list_page.html', list_title=category.name, 
            list_description=category.description, products=category.products)


@blueprint.route('/p/<int:product_id>-<slug>')
def show_product(product_id, slug):
    product = Product.find(product_id)
    if not product:
        return abort(404)

    if current_app.config['ALLOW_AFFILIATES'] and 'afftag' in request.args:
        allowed_tags = current_app.config['ALLOWED_AFFILIATE_TAGS']
        if allowed_tags is None or request.args['afftag'] in allowed_tags:
            session['afftag'] = request.args['afftag']
            session['afftag_expiry'] = time.time() + current_app.config['AFFILIATE_TAG_TTL']
            session.permanent = True

    g.active_category_id = product.category_id
    return render_template('store/product.html', product=product)


@blueprint.route('/cart')
def get_cart():
    return render_template('store/cart.html')


@blueprint.route('/cart/add', methods=['POST'])
def add_to_cart():
    product = Product.find(request.form['id'])
    if not product:
        return abort(404)

    if not g.cart.created and 'afftag' in session:
        g.cart.assoc_tag = session['afftag']

    try:
        g.cart.add_product(product)
    except InvalidCartItem as e:
        current_app.logger.debug(e)
        return abort(400)
    except Exception as e:
        current_app.logger.error(e)
        return abort(500)

    session.permanent = True
    return render_template('store/cart.html')


@blueprint.route('/cart/update/<item_id>', methods=['POST'])
def update_cart_item(item_id):
    quantity = request.form['quantity']
    if quantity == '':
        quantity = 0
    elif not quantity.isdigit():
        return abort(400)
    g.cart.update_item(item_id, int(quantity))
    return render_template('store/cart.html')


@blueprint.route('/cart/checkout')
def checkout():
    g.cart.refresh()
    if not g.cart.created:
        return redirect(url_for('.home'))
    return redirect(g.cart.purchase_url)
