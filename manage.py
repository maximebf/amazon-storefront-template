#!/usr/bin/env python

from flask_script import Manager, Shell, Server
import amzstorefront
from amzstorefront import app, amazon
from amzstorefront.models import *
from amzstorefront.utils import *
import json


manager = Manager(app)
manager.add_command("runserver", Server(port=8080))
manager.add_command("shell", Shell())


@manager.shell
def make_shell_context():
    import pprint
    c = dict(app=app, amazon=amazon, models=amzstorefront.models, 
             pprint=pprint.pprint, commit=db.session.commit,
             item_lookup=item_lookup)
    c.update(amzstorefront.models.__dict__)
    c.update(amzstorefront.utils.__dict__)
    return c


@manager.command
def create_db():
    from amzstorefront.models import db
    db.create_all()


@manager.command
def add_category(name):
    c = Category(name)
    print "Adding category %s" % c.name
    db.session.add(c)
    db.session.commit()


@manager.command
def add_product(asin, category_name):
    c = Category.find_by_name(category_name)
    if c is None:
        print "ERROR: unknown category '%s'" % category_name
    p = amazon.find_product(asin)
    if p.ASIN != asin:
        print "WARNING: %s is a variation" % asin
    print "Adding product '%s' in '%s'" % (p.ASIN, category_name)
    c.products.append(p)
    db.session.commit()


@manager.command
def update_product(asin):
    p = Product.query.filter_by(ASIN=asin).one()
    amazon.populate_product(p)
    db.session.commit()


@manager.command
def update_all_products():
    for p in Product.query.filter_by(parent_id=None).all():
        amazon.populate_product(p)
    db.session.commit()


@manager.command
def item_lookup(asin, response_group):
    from lxml import etree
    r = amazon.find_item(asin, response_group)
    print etree.tostring(r, pretty_print=True)


if __name__ == "__main__":
    manager.run()
