from flask import Flask, g, session

app = Flask(__name__)
app.secret_key = "test"


@app.route("/login/<name>", methods=["POST"])
def login(name):
    session["user"] = name
    return {"ok": True}


@app.route("/whoami")
def whoami():
    return {"user": session.get("user", "anonymous")}


@app.route("/count")
def count():
    session["n"] = session.get("n", 0) + 1
    g.tag = "t"
    return {"n": session["n"], "tag": g.tag}
