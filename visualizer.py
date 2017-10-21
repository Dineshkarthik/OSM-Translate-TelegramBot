"""Flask web app for visualizing OSM-Translation stats."""
import os
import hashlib
from optparse import OptionParser
from flask import Flask, Response, redirect, url_for, request, session, abort
from flask.ext.login import LoginManager, UserMixin, \
                                login_required, login_user, logout_user

app = Flask(__name__)
app.secret_key = hashlib.sha1(os.urandom(128)).hexdigest()

# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# silly user model
class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.name = "user" + str(id)
        self.password = self.name + "_secret"

    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.password)


# create some users with ids 1 to 20
users = [User(id) for id in range(1, 21)]


# some protected url
@app.route('/')
@login_required
def home():
    return Response("Hello World!")


# somewhere to login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if password == username + "_secret":
            id = username.split('user')[1]
            user = User(id)
            login_user(user)
            return redirect(request.args.get("next"))
        else:
            return abort(401)
    else:
        return Response('''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=password name=password>
            <p><input type=submit value=Login>
        </form>
        ''')


# somewhere to logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return Response('<p>Logged out</p>')


# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return Response('<p>Login failed</p>')


# callback to reload the user object
@login_manager.user_loader
def load_user(userid):
    return User(userid)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option(
        "-p",
        "--port",
        dest="port",
        help="Port on which the app will run",
        default=5000)
    (options, args) = parser.parse_args()
    app.run(host='0.0.0.0', debug=True, port=int(options.port))
