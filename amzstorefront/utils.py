import re
from redis import StrictRedis
import oembed
import hashlib


redis = StrictRedis()


oembed_consumer = oembed.OEmbedConsumer()
oembed_consumer.addEndpoint(oembed.OEmbedEndpoint('http://www.youtube.com/oembed', ['http://*.youtube.com/*']))
oembed_consumer.addEndpoint(oembed.OEmbedEndpoint('http://vimeo.com/api/oembed.json', ['http://*.vimeo.com/*']))
oembed_consumer.addEndpoint(oembed.OEmbedEndpoint('http://www.flickr.com/services/oembed', ['http://*.flickr.com/*']))


def hash_with_salt(value):
    return hashlib.sha1(app.config['SALT'] + value).hexdigest()


## {{{ http://code.activestate.com/recipes/577257/ (r1)
_slugify_strip_re = re.compile(r'[^\w\s-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    
    From Django's "django/template/defaultfilters.py".
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', unicode(value)).encode('ascii', 'ignore')
    value = unicode(_slugify_strip_re.sub('', value).strip().lower())
    return _slugify_hyphenate_re.sub('-', value)
## end of http://code.activestate.com/recipes/577257/ }}}
