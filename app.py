import os
from flask import Flask, render_template, request

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-in-render")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name", "").strip()
    message = request.form.get("message", "").strip()

    if not name:
        return render_template(
            "index.html",
            error="Please enter your name to continue.",
            name=name,
            message=message,
        )

    result = f"Hello {name}, your message was received successfully."
    return render_template(
        "index.html",
        result=result,
        name=name,
        message=message,
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
