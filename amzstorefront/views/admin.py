from flask.ext.admin import Admin, AdminIndexView, BaseView, expose
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext import wtf
from flask.ext.login import current_user
from amzstorefront.models import *
import os


class AuthenticatedView(object):
    def is_accessible(self):
        return current_user.is_authenticated()


class IndexView(AuthenticatedView, AdminIndexView):
    pass


class ProductsView(AuthenticatedView, ModelView):

    column_list = ('ASIN', 'brand', 'name', 'formated_price', 'visible')
    column_sortable_list = ('id', 'brand', 'name')
    column_searchable_list = ('ASIN', 'brand', 'name')

    form_columns = ('ASIN', 'visible', 'category', 'parent', 'name', 'slug', 'brand', 'name', 'description', 'image_url', 'thumb_url', 'editor_comment', 'video_review_url', 'video_review_html', 'video_review_author', 'video_review_author_url')
    form_overrides = dict(description=wtf.TextAreaField, editor_comment=wtf.TextAreaField, video_review_html=wtf.TextAreaField)
    form_args = dict(ASIN=dict(validators=[wtf.required()]))

    def __init__(self, session, **kwargs):
        super(ProductsView, self).__init__(Product, session, **kwargs)

    def get_query(self):
        return self.session.query(self.model).filter(Product.parent_id==None)


class CategoriesView(AuthenticatedView, ModelView):

    column_list = ('name', 'slug')
    form_columns = ('name', 'slug', 'description', 'position', 'thumb_size')
    form_overrides = dict(description=wtf.TextAreaField)
    form_args = dict(name=dict(validators=[wtf.required()]), slug=dict(validators=[wtf.required()]))

    def __init__(self, session, **kwargs):
        super(CategoriesView, self).__init__(Category, session, **kwargs)


def create_admin(app):
    admin = Admin(app, name='Admin', index_view=IndexView())
    admin.add_view(CategoriesView(db.session))
    admin.add_view(ProductsView(db.session))
