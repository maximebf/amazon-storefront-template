from datetime import timedelta


class Config(object):
    SECRET_KEY = 'GENERATE SECRET KEY' # for the session, see flask.pocoo.org/docs/quickstart/#sessions
    PERMANENT_SESSION_LIFETIME = timedelta(days=90)
    
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin'

    AWS_KEY = 'YOUR AWS KEY' # Amazon Access Key, can be found in your AWS account under Security Credentials
    AWS_SECRET = 'YOUR AWS SECRET' # Amazon Access Secret Key
    AMAZON_ASSOC_TAG = 'YOUR ASSOC TAG' # Your associates tag, can be found on your Amazon Affiliates dashboard
    AMAZON_LOCALE = 'us'

    ALLOW_AFFILIATES = False # Built-in affiliates program, see README
    AFFILIATE_TAG_TTL = 86400 * 2
    ALLOWED_AFFILIATE_TAGS = None # None = all, list with affiliate tags = whitelist
    CART_TTL = 3600 # Duration of the cache time for the cart

    SHOW_BUY_NOW_BTN = True # Show a Buy Now button with a direct link to Amazon

    BROKER_URL = 'redis://localhost:6379/0'
    CELERY_TIMEZONE = 'UTC'
    CELERYBEAT_SCHEDULE = {
        'sync-products': {
            'task': 'amzstorefront.tasks.sync_all',
            'schedule': timedelta(hours=12)
        }
    }


class ProdConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///amzstorefront.db' # You should use a proper database in production


class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///amzstorefront.db'
    SQLALCHEMY_ECHO = True
