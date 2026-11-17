from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
db = SQLAlchemy(app)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name}


with app.app_context():
    db.create_all()


@app.route("/items", methods=["POST"])
def add_item():
    data = request.get_json()
    it = Item(name=data["name"])
    db.session.add(it)
    db.session.commit()
    return jsonify(it.to_dict()), 201


@app.route("/items")
def list_items():
    return jsonify([i.to_dict() for i in Item.query.order_by(Item.id).all()])


@app.route("/items/<int:item_id>")
def get_item(item_id):
    return jsonify(Item.query.get_or_404(item_id).to_dict())
