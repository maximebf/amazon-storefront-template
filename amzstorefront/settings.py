import os
from datetime import timedelta


class Config(object):
    SECRET_KEY = 'GENERATE SECRET KEY'
    PERMANENT_SESSION_LIFETIME = timedelta(days=90)
    
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin'

    AWS_KEY = 'YOUR AWS KEY'
    AWS_SECRET = 'YOUR AWS SECRET'
    AMAZON_ASSOC_TAG = 'YOUR ASSOC TAG'
    AMAZON_LOCALE = 'us'

    ALLOW_AFFILIATES = False
    AFFILIATE_TAG_TTL = 86400 * 2
    ALLOWED_AFFILIATE_TAGS = None # None = all, list with affiliate tags = whitelist
    CART_TTL = 3600

    BROKER_URL = 'redis://localhost:6379/0'
    CELERY_TIMEZONE = 'UTC'
    CELERYBEAT_SCHEDULE = {
        'sync-products': {
            'task': 'amzstorefront.tasks.sync_all',
            'schedule': timedelta(hours=12)
        }
    }


class ProdConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///amzstorefront.db'


class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///amzstorefront.db'
    SQLALCHEMY_ECHO = True
