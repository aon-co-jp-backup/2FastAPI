"""Second sample: hooks, templates, uploads, Flask-RESTful resources, CORS."""
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_restful import Api, Resource, abort

app = Flask(__name__)
CORS(app)
api = Api(app)

BOOKS = {1: {"title": "Dune"}, 2: {"title": "Emma"}}


@app.before_request
def block_admin():
    if request.path == "/blocked":
        return jsonify(error="blocked"), 403


@app.errorhandler(404)
def not_found(e):
    return jsonify(error="not found"), 404


@app.route("/hello/<name>")
def hello(name):
    return render_template("hello.html", name=name, items=[1, 2, 3])


@app.route("/upload", methods=["POST"])
def upload():
    f = request.files["doc"]
    data = f.read()
    return jsonify(filename=f.filename, size=len(data))


@app.route("/blocked")
def blocked():
    return "never reached"


class Book(Resource):
    def get(self, book_id):
        if book_id not in BOOKS:
            abort(404, message="no such book")
        return BOOKS[book_id]

    def delete(self, book_id):
        return {"deleted": book_id}, 202


class BookList(Resource):
    def get(self):
        return {"books": list(BOOKS.values())}

    def post(self):
        data = request.get_json()
        return {"created": data["title"]}, 201


api.add_resource(Book, "/books/<int:book_id>")
api.add_resource(BookList, "/books")

if __name__ == "__main__":
    app.run()
