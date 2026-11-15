"""Sample Flask app used by the tests."""
from flask import Flask, Blueprint, request, jsonify, abort, redirect

app = Flask(__name__)
api = Blueprint("api", __name__, url_prefix="/api")

ITEMS = {1: "apple", 2: "banana"}


@app.route("/")
def index():
    return "hello flask"  # plain text


@app.route("/items/<int:item_id>")
def get_item(item_id):
    if item_id not in ITEMS:
        abort(404)
    return jsonify({"id": item_id, "name": ITEMS[item_id]})


@app.route("/search")
def search():
    q = request.args.get("q", "")
    limit = request.args.get("limit", 10, type=int)
    return jsonify(query=q, limit=limit)


@app.route("/echo", methods=["POST"])
def echo():
    data = request.get_json()
    return jsonify(data), 201


@app.route("/form", methods=["POST"])
def form():
    name = request.form.get("name", "anon")
    return {"hello": name}


@app.get("/hdr")
def hdr():
    return jsonify(agent=request.headers.get("X-Agent", "none"))


@app.route("/old")
def old():
    return redirect("/")


@app.route("/files/<path:p>")
def files(p):
    return jsonify(path=p)


@app.route("/both", methods=["GET", "POST"])
def both():
    if request.method == "POST":
        return jsonify(method="post")
    return jsonify(method="get")


@api.route("/ping")
def ping():
    return jsonify(pong=True)


@api.route("/sum/<int:a>/<int:b>")
def add(a, b):
    return jsonify(sum=a + b)


app.register_blueprint(api)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
