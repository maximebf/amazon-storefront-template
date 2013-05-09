from amzstorefront import app
from flask_sqlalchemy import SQLAlchemy
from flask.ext.login import UserMixin
from sqlalchemy import func
from werkzeug import cached_property
from utils import *
import datetime


__all__ = ('db', 'User', 'Category', 'Product')


db = SQLAlchemy(app)


class User(UserMixin):
    def __init__(self):
        self.id = 'admin'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=func.now())
    name = db.Column(db.String)
    slug = db.Column(db.String)
    description = db.Column(db.String)
    position = db.Column(db.Integer, default=0, nullable=False)
    thumb_size = db.Column(db.Enum('small', 'medium', 'large', name='thumb_sizes'), default='medium')

    products = db.relationship('Product', backref='category')

    @classmethod
    def find(cls, id):
        return Category.query.filter_by(id=id).first()

    @classmethod
    def find_by_slug(cls, slug):
        return Category.query.filter_by(slug=slug).first()

    @classmethod
    def find_by_name(cls, name):
        return Category.query.filter_by(name=name).first()

    def __init__(self, name=None):
        if not name is None:
            self.name = name
            self.slug = name.lower()

    def __repr__(self):
        return self.name


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=func.now())
    last_refreshed_at = db.Column(db.DateTime)
    ASIN = db.Column(db.String)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    name = db.Column(db.String)
    slug = db.Column(db.String)
    brand = db.Column(db.String)
    description = db.Column(db.String)
    price = db.Column(db.Float)
    currency = db.Column(db.String)
    availability = db.Column(db.String)
    details_url = db.Column(db.String)
    reviews_url = db.Column(db.String)
    image_url = db.Column(db.String)
    thumb_url = db.Column(db.String)
    has_reviews = db.Column(db.Boolean, default=False, nullable=False)
    formated_price = db.Column(db.String)
    out_of_stock = db.Column(db.Boolean, default=False, nullable=False)
    visible = db.Column(db.Boolean, default=False, nullable=False)
    overrided_fields = db.Column(db.PickleType)
    variation_attrs = db.Column(db.PickleType)
    variation_dimensions = db.Column(db.PickleType)
    variation_main_dimension = db.Column(db.String)
    editor_comment = db.Column(db.String)
    video_review_url = db.Column(db.String)
    video_review_html = db.Column(db.String)
    video_review_author = db.Column(db.String)
    video_review_author_url = db.Column(db.String)

    parent = db.relationship('Product', backref='variations', remote_side=[id], cascade='all')

    @classmethod
    def find(cls, id):
        return Product.query.filter_by(id=id).first()

    @classmethod
    def find_by_asin(cls, ASIN):
        return Product.query.filter_by(ASIN=ASIN).first()

    def __init__(self, ASIN=None):
        self.ASIN = ASIN
        self.overrided_fields = set()

    def __repr__(self):
        return "#%s %s" % (self.ASIN, self.fullname)

    @property
    def fullname(self):
        if self.brand:
            return self.brand + ' ' + self.name
        return self.name

    @property
    def parent_or_self(self):
        if self.parent:
            return self.parent
        return self

    @cached_property
    def formated_last_refreshed_at(self):
        if not self.last_refreshed_at:
            return 'a long time ago'
        delta = datetime.datetime.now() - self.last_refreshed_at
        if delta.seconds < 300:
            return 'less than 5 minutes ago'
        if delta.seconds < 3600:
            return 'less than an hour ago'
        return '%d hours ago' % (delta.seconds / 60 / 60)

    def get_variation(self, ASIN):
        for v in self.variations:
            if v.ASIN == ASIN:
                return v
        return None

    @cached_property
    def variation_matrix(self):
        if not self.variation_main_dimension or not self.variation_dimensions or len(self.variation_dimensions) <= 1:
            return self.variations

        matrix = {}
        one_per_dimension = True
        for v in self.variations:
            dim_name = v.variation_attrs[self.variation_main_dimension]
            if not dim_name in matrix:
                matrix[dim_name] = []
            else:
                one_per_dimension = False
            matrix[dim_name].append(v)

        if one_per_dimension:
            return self.variations
        if len(matrix) == 1:
            return matrix.values()[0]
        return matrix

    @cached_property
    def variation_name(self):
        return ", ".join(map(str, self.variation_attrs.values()))

    @cached_property
    def formated_variation_dimensions(self):
        if not self.variation_dimensions:
            return None
        names = {"Size": "sizes", "ClothingSize": "sizes", "Color": "colors", "MaterialType": "types of material",
                 "MetalType": "types of metal", "OperatingSystem": "operating systems", "Model": "models"}
        dim_names = [names[d] for d in self.variation_dimensions if d in names]
        if len(dim_names) == 0:
            return None
        if len(dim_names) > 1:
            last = dim_names.pop(-1)
            formated_dim_names = "%s and %s" % (", ".join(dim_names), last)
        else:
            formated_dim_names = dim_names[0]
        return "Available in multiple %s" % formated_dim_names

    def build_variation_name(self, exclude_dimension=None):
        values = [str(v) for k, v in self.variation_attrs.items() if k != exclude_dimension]
        return ", ".join(values)

    def is_field_overrided(self, field):
        if self.overrided_fields is None:
            return False
        return field in self.overrided_fields

    def fetch_video_review_from_url(self, url):
        r = oembed_consumer.embed(url, maxwidth=610)
        self.video_review_url = url
        self.video_review_html = r['html']
        self.video_review_author = r['author_name']
        self.video_review_author_url = r['author_url']
