from flask import render_template, request, flash, redirect, url_for
from flask.ext import wtf
from flask.ext import login
from amzstorefront import app
from amzstorefront.models import *
import admin
import store


app.register_blueprint(store.blueprint)
admin.create_admin(app)


def register_page(endpoint, template_filename):
    def render_page():
        return render_template(template_filename)
    app.add_url_rule(endpoint, endpoint.strip('/').replace('/', '_'), render_page)

register_page('/about', 'pages/about.html')
register_page('/contact', 'pages/contact.html')
register_page('/affiliates', 'pages/affiliates.html')


login_manager = login.LoginManager()
login_manager.login_view = "login"
login_manager.setup_app(app)


@login_manager.user_loader
def load_user(id):
    return User()


class LoginForm(wtf.Form):
    username = wtf.TextField(validators=[wtf.required()])
    password = wtf.PasswordField(validators=[wtf.required()])


@app.route('/login', methods=('GET', 'POST'))
def user_login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        if form.username.data == app.config['ADMIN_USERNAME'] and form.password.data == app.config['ADMIN_PASSWORD']:
            login.login_user(User())
            return redirect(url_for('admin.index'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    login.logout_user()
    return redirect(url_for('store.home'))
