from flask import Flask, jsonify
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user

app = Flask(__name__)
app.secret_key = "test"
login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, id, name):
        self.id = id
        self.name = name


USERS = {"1": User("1", "ann"), "2": User("2", "bob")}


@login_manager.user_loader
def load_user(user_id):
    return USERS.get(user_id)


@app.route("/login")
def login():
    return jsonify({"page": "login"})


@app.route("/signin/<uid>", methods=["POST"])
def signin(uid):
    u = USERS.get(uid)
    if u is None:
        return jsonify({"error": "no such user"}), 404
    login_user(u)
    return jsonify({"ok": True})


@app.route("/signout", methods=["POST"])
def signout():
    logout_user()
    return jsonify({"ok": True})


@app.route("/me")
def me():
    if current_user.is_authenticated:
        return jsonify({"name": current_user.name})
    return jsonify({"name": None})


@app.route("/private")
@login_required
def private():
    return jsonify({"secret": current_user.name})
