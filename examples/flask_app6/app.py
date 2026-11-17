from flask import Flask, jsonify, request
from flask_login import LoginManager, UserMixin, current_user, fresh_login_required, login_user
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "test"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
db = SQLAlchemy(app)
login_manager = LoginManager(app)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))


class User(UserMixin):
    def __init__(self, id, name):
        self.id = id
        self.name = name


USERS = {"1": User("1", "ann")}


@login_manager.user_loader
def load_user(uid):
    return USERS.get(uid)


@login_manager.request_loader
def load_from_request(req):
    if req.headers.get("X-Token") == "tok":
        return USERS["1"]
    return None


@login_manager.unauthorized_handler
def unauth():
    return jsonify({"error": "login first"}), 401


with app.app_context():
    db.create_all()
    for i in range(7):
        db.session.add(Item(name="n%d" % i))
    db.session.commit()


@app.route("/items")
def items():
    p = Item.query.order_by(Item.id).paginate(page=int(request.args.get("page", 1)), per_page=3)
    return jsonify({"names": [i.name for i in p.items], "pages": p.pages, "total": p.total, "next": p.has_next, "prev": p.has_prev})


@app.route("/signin", methods=["POST"])
def signin():
    login_user(USERS["1"])
    return jsonify({"ok": True})


@app.route("/fresh")
@fresh_login_required
def fresh():
    return jsonify({"who": current_user.name})
