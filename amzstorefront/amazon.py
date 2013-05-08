from models import *
from utils import *
from amzstorefront import app
from amazonproduct import API as ProductAdvertisingAPI
from amazonproduct.api import InvalidCartItem
from werkzeug import cached_property
import datetime

try:
    from cPickle import pickle
except ImportError:
    import pickle


api = ProductAdvertisingAPI(app.config['AWS_KEY'], 
                            app.config['AWS_SECRET'], 
                            app.config['AMAZON_LOCALE'])


def find_item(asin, response_group='Large', parent_only=False, assoc_tag=None):
    assoc_tag = assoc_tag or app.config['AMAZON_ASSOC_TAG']
    app.logger.debug('Fetching %s for %s' % (response_group, asin))
    try:
        r = api.item_lookup(asin, ResponseGroup=response_group, AssociateTag=assoc_tag)
    except Exception as e:
        app.logger.error(e.message)
        return
    item = r.Items.Item
    if parent_only and hasattr(item, 'ParentASIN') and item.ASIN.pyval != item.ParentASIN.pyval:
        app.logger.debug('%s is a variation' % asin)
        return find_item(item.ParentASIN.pyval, response_group, assoc_tag=assoc_tag)
    return item


def find_product(asin, parent_only=True, assoc_tag=None):
    item = find_item(asin, parent_only=parent_only, assoc_tag=assoc_tag)
    if item is None:
        return
    product = Product(item.ASIN.pyval)
    update_product(product, item, assoc_tag)
    return product


def update_product(product, item=None, assoc_tag=None):
    product.last_refreshed_at = datetime.datetime.now()

    if item is None:
        item = find_item(product.ASIN, assoc_tag=assoc_tag)
        if item is None:
            product.visible = False
            return product

    popuplate_product_fields(product, item)

    if item.OfferSummary.TotalNew == 0:
        update_variations(product, assoc_tag)
        if product.formated_price == '$-':
            populate_product_price(product, find_item(product.ASIN, 'VariationSummary'))
    else:
        populate_product_price(product, item)

    return product


def popuplate_product_fields(product, item):
    app.logger.debug('Populating fields for %s' % product.ASIN)
    if not product.is_field_overrided('name'):
        product.name = item.ItemAttributes.Title.pyval
    if hasattr(item, 'DetailPageURL') and not product.is_field_overrided('details_url'):
        product.details_url = item.DetailPageURL.pyval
    if not product.is_field_overrided('brand'):
        if hasattr(item.ItemAttributes, 'Brand'):
            product.brand = item.ItemAttributes.Brand.pyval
        elif hasattr(item.ItemAttributes, 'Publisher'):
            product.brand = item.ItemAttributes.Publisher.pyval
        elif hasattr(item.ItemAttributes, 'Author'):
            product.brand = item.ItemAttributes.Author.pyval
    if not product.is_field_overrided('description'):
        product.description = None
        if hasattr(item, 'EditorialReviews'):
            product.description = item.EditorialReviews.EditorialReview.Content.pyval
        if hasattr(item.ItemAttributes, 'Feature'):
            if product.description is None:
                product.description = ''
            product.description += '<p><strong>Features:</strong></p><ul>'
            for f in item.ItemAttributes.Feature:
                product.description += '<li>%s</li>' % f.pyval
            product.description += '</ul>'
    if hasattr(item, 'CustomerReviews'):
        product.reviews_url = item.CustomerReviews.IFrameURL.pyval
        product.has_reviews = item.CustomerReviews.HasReviews.pyval
    if not product.is_field_overrided('image_url'):
        if hasattr(item, 'MediumImage'):
            product.image_url = item.MediumImage.URL.pyval
        else:
            product.image_url = '/static/img/unknown.png'
    if not product.is_field_overrided('thumb_url'):
        if hasattr(item, 'SmallImage'):
            product.thumb_url = item.SmallImage.URL.pyval
        else:
            product.thumb_url = '/static/img/unknown.png'
    product.slug = slugify(product.fullname)


def populate_product_price(product, item):
    app.logger.debug('Populating price for %s' % product.ASIN)
    product.price = 0
    product.currency = 'USD'
    product.availability = 'Unknown'
    product.out_of_stock = False
    if hasattr(item, 'OfferSummary') and hasattr(item, 'Offers') and int(item.OfferSummary.TotalNew.pyval) > 0:
        offer = find_best_offer(item.Offers)
        if offer is None:
            if hasattr(item.ItemAttributes, 'ListPrice'):
                product.formated_price = item.ItemAttributes.ListPrice.FormattedPrice.pyval
                product.price = item.ItemAttributes.ListPrice.Amount.pyval
                product.currency = item.ItemAttributes.ListPrice.CurrencyCode.pyval
            else:
                product.formated_price = "$-"
        else:
            product.formated_price = offer.Price.FormattedPrice.pyval
            product.price = offer.Price.Amount.pyval
            product.currency = offer.Price.CurrencyCode.pyval
            if hasattr(offer, 'Availability'):
                product.availability = offer.Availability.pyval
    elif hasattr(item, 'VariationSummary'):
        product.formated_price = "%s-%s" % (item.VariationSummary.LowestPrice.FormattedPrice.pyval, 
            item.VariationSummary.HighestPrice.FormattedPrice.pyval)
    elif hasattr(item.ItemAttributes, 'ListPrice'):
        product.formated_price = item.ItemAttributes.ListPrice.FormattedPrice.pyval
        product.price = item.ItemAttributes.ListPrice.Amount.pyval
        product.currency = item.ItemAttributes.ListPrice.CurrencyCode.pyval
    else:
        product.formated_price = 'Out of stock'
        product.out_of_stock = True


def find_best_offer(offers):
    best_price = None
    best_offer = None
    for offer in offers.Offer:
        if offer.OfferAttributes.Condition.pyval != 'New':
            continue
        if offer.OfferListing.Price.FormattedPrice.pyval == 'Too low to display':
            continue
        if best_price is None or offer.OfferListing.Price.Amount.pyval < best_price:
            best_price = offer.OfferListing.Price.Amount.pyval
            best_offer = offer.OfferListing
    return best_offer


def update_variations(product, assoc_tag=None):
    vm = find_item(product.ASIN, 'VariationMatrix', assoc_tag=assoc_tag)
    product.out_of_stock = False
    
    if not hasattr(vm, 'Variations'):
        while len(product.variations) > 0:
            product.variations.pop(0)
        product.out_of_stock = True
        product.formated_price = 'Out of stock'
        return

    product.variation_dimensions = []
    for vd in vm.Variations.VariationDimensions.VariationDimension:
        product.variation_dimensions.append(vd.pyval)
    if not product.is_field_overrided('variation_main_dimension'):
        product.variation_main_dimension = None
        if 'Size' in product.variation_dimensions:
            product.variation_main_dimension = 'Size'
        elif 'ClothingSize' in product.variation_dimensions:
            product.variation_main_dimension = 'ClothingSize'
        elif len(product.variation_dimensions) > 0:
            product.variation_main_dimension = product.variation_dimensions[0]

    asins = []
    for vi in vm.Variations.Item:
        asins.append(vi.ASIN.pyval)
        v = product.get_variation(vi.ASIN.pyval)
        if v is None:
            v = find_product(vi.ASIN.pyval, parent_only=False, assoc_tag=assoc_tag)
            product.variations.append(v)
        else:
            update_product(v, assoc_tag=assoc_tag)
        v.variation_attrs = convert_variation_attributes_to_dict(vi.VariationAttributes)

    for v in product.variations:
        if not v.ASIN in asins:
            product.variations.remove(v)

    if len(product.variations) == 0:
        product.out_of_stock = True
        product.formated_price = 'Out of stock'
        return

    if product.description is None:
        product.description = product.variations[0].description

    lowest_price = None
    lowest_price_formated_price = None
    highest_price = None
    highest_price_formated_price = None

    for v in product.variations:
        if not v.ASIN in asins:
            product.variations.remove(v)
        else:
            if v.formated_price == '$-':
                continue
            if lowest_price is None or v.price < lowest_price:
                lowest_price = v.price
                lowest_price_formated_price = v.formated_price
            if highest_price is None or v.price > highest_price:
                highest_price = v.price
                highest_price_formated_price = v.formated_price

    product.formated_price = '$-'
    if len(product.variations) == 0:
        product.formated_price = product.variations[0].formated_price
    elif lowest_price is not None and highest_price is not None:
        if lowest_price == highest_price:
            product.formated_price = lowest_price_formated_price
        else:
            product.formated_price = "%s-%s" % (lowest_price_formated_price, highest_price_formated_price)


def convert_variation_attributes_to_dict(vattrs):
    attrs = {}
    for va in vattrs.VariationAttribute:
        attrs[va.Name.pyval] = va.Value.pyval if hasattr(va, 'Value') else 'Unknown'
    return attrs


class Cart(object):
    @classmethod
    def load(cls, id, hmac, assoc_tag=None):
        cart_data = redis.get("%s:%s" % (id, hmac))
        if cart_data:
            try:
                return pickle.loads(cart_data)
            except:
                pass
        
        c = cls(id, hmac, assoc_tag)
        c.modified = True # force persist
        return c

    modified = False

    def __init__(self, id=None, hmac=None, assoc_tag=None):
        self.id = id
        self.hmac = hmac
        self.assoc_tag = assoc_tag or app.config['AMAZON_ASSOC_TAG']
        self._purchase_url = None
        self._formated_price = None
        self._items = None

    @property
    def fullid(self):
        return "%s:%s" % (self.id, self.hmac)

    @property
    def created(self):
        return not self.id is None and not self.hmac is None

    @property
    def loaded(self):
        return not (self._purchase_url is None or self._formated_price is None or self._items is None)

    def refresh(self):
        try:
            r = api.cart_get(self.id, self.hmac, AssociateTag=self.assoc_tag)
            self._update_cart_from_response(r)
        except:
            self.id = None
            self.hmac = None
            self._purchase_url = None
            self._formated_price = None
            self._items = None

    def _update_cart_from_response(self, r):
        self._purchase_url = ''
        self._formated_price = '$0'
        self._items = []
        cart = r.Cart
        if hasattr(cart, 'PurchaseURL'):
            self._purchase_url = cart.PurchaseURL.pyval
        if hasattr(cart, 'SubTotal'):
            self._formated_price = cart.SubTotal.FormattedPrice.pyval
        if hasattr(cart, 'CartItems'):
            for item in cart.CartItems.CartItem:
                self._items.append(CartItem(item))

    @property
    def purchase_url(self):
        if self._purchase_url is None and self.created:
            self.refresh()
        return self._purchase_url

    @property
    def formated_price(self):
        if self._formated_price is None and self.created:
            self.refresh()
        if self._formated_price is None:
            return '$0'
        return self._formated_price

    @property
    def items(self):
        if self._items is None and self.created:
            self.refresh()
        if self._items is None:
            return []
        return self._items

    @property
    def products(self):
        for i in self.items:
            yield i.product

    def add_product(self, product):
        self.add_item(product.ASIN)

    def add_item(self, ASIN, quantity=1):
        items = {ASIN: quantity}
        if self.created:
            item = self.get_item(ASIN)
            if item:
                return self.update_item(item.id, item.quantity + 1)
            r = api.cart_add(self.id, self.hmac, items, AssociateTag=self.assoc_tag)
        else:
            r = api.cart_create(items, AssociateTag=self.assoc_tag)
            self.id = r.Cart.CartId.pyval
            self.hmac = r.Cart.HMAC.pyval
        self._update_cart_from_response(r)
        self.modified = True

    def get_item(self, ASIN):
        for item in self.items:
            if item.ASIN == ASIN:
                return item
        return False

    def update_item(self, item_id, quantity):
        r = api.cart_modify(self.id, self.hmac, {item_id: quantity}, AssociateTag=self.assoc_tag)
        self._update_cart_from_response(r)
        self.modified = True

    def remote_item(self, item_id):
        self.update_item(item_id, 0)

    def clear_items(self):
        r = api.cart_clear(self.id, self.hmac, AssociateTag=self.assoc_tag)
        self._update_cart_from_response(r)
        self.modified = True

    def persist(self):
        redis.setex(self.fullid, app.config['CART_TTL'], pickle.dumps(self))
        self.modified = False

    def __getstate__(self):
        if not self.loaded and self.created:
            self.refresh()
        s = self.__dict__.copy()
        del(s['modified'])
        return s


class CartItem(object):
    def __init__(self, r):
        self.id = r.CartItemId.pyval
        self.ASIN = r.ASIN.pyval
        self.quantity = int(r.Quantity.pyval)
        self.unit_formated_price = r.Price.FormattedPrice.pyval
        self.total_formated_price = r.ItemTotal.FormattedPrice.pyval

    @cached_property
    def product(self):
        if self.variation.parent:
            return self.variation.parent
        return self.variation

    @cached_property
    def variation(self):
        return Product.query.filter_by(ASIN=self.ASIN).first()
