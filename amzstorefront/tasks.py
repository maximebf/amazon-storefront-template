import amazon
from amzstorefront import app
from models import *
from celery import Celery

celery = Celery('amzstorefront.tasks')
celery.conf.update(app.config)


@celery.task(ignore_result=True)
def sync_all():
    for p in Product.query.filter_by(parent_id=None).all():
        sync_product.delay(p.id)


@celery.task(ignore_result=True)
def sync_product(id):
    product = Product.query.filter_by(id=id).one()
    amazon.update_product(product)
    db.session.commit()


@celery.task(ignore_result=True)
def add_product(ASIN):
    product = amazon.find_product(ASIN)
    db.session.add(product)
    db.session.commit()
