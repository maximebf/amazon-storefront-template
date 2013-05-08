# Amazon Storefront Template

An almost ready-to-use Python [Flask](http://flask.pocoo.org/) application to create your own 
online shop on top of the [Amazon Affiliates](https://affiliate-program.amazon.com/) program
using their [Product Advertising API](https://affiliate-program.amazon.com/gp/advertising/api/detail/main.html).

Features:

 - Easy to learn, easy to use
 - Easy to add products using Amazon's ASIN
 - Easy to customize and extend
 - Stays synchronized with Amazon
 - Optimized for caching engine (works great behind [Varnish](https://www.varnish-cache.org/))
 - Small web admin and commands from the terminal
 - Uses [Celery](http://www.celeryproject.org/) for background tasks

## Installation

 1. Get the source code
 2. Install dependencies using `pip install -r requirements.txt`
 3. Create the db using `./manage.py create_db`

## Getting started

 1. Signup on Amazon Affiliates.
 2. Signup on AWS
 3. Edit the *amzstorefront/settings.py* with your authentification details
 4. Add categories and products
 5. Customize the templates and CSS
 6. Run!

## Adding categories and products

To add a product you will need its ASIN which can be found
in a product's URL or on the product's page in the Details section
(it looks like: B003O6JIVE).

From the command line:

    $ ./manage.py add_category Games
    $ ./manage.py add_product B003O6JIVE Games

## Running

Running the development server is as simple as:

    $ ./manage.py runserver

In production, you can use uWSGI and Supervisor as explained
[here](http://maximebf.com/blog/2012/10/building-websites-in-python-with-flask).

## Using Varnish

This application has been optimized to run behind [Varnish](https://www.varnish-cache.org) 
so that everything can be cached. Use this simple rule to ensure the cart is not cached:

    sub vcl_fetch {
        if ( !( req.url ~ "^/cart") ) {
            unset req.http.Cookie;
        }
    }
