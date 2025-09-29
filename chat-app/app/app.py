from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ---------------------------
# Helpers
# ---------------------------
def init_db():
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, message TEXT)"
    )
    conn.commit()
    conn.close()

def load_messages():
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("SELECT user, message FROM messages")
    msgs = [{"user": row[0], "message": row[1]} for row in c.fetchall()]
    conn.close()
    return msgs

def save_message(user, message):
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("INSERT INTO messages (user, message) VALUES (?, ?)", (user, message))
    conn.commit()
    conn.close()

# Initialize database
init_db()

# ---------------------------
# Routes
# ---------------------------
@app.route("/change_name", methods=["POST"])
def change_name():
    data = request.get_json()
    session["username"] = data["username"]
    return "OK"

@app.route("/", methods=["GET", "POST"])
def index():
    # If user has not set a name yet
    if "username" not in session:
        if request.method == "POST" and request.form.get("username"):
            session["username"] = request.form["username"]
            return redirect("/")
        return render_template("set_name.html")
    return render_template("chat.html", current_user=session["username"])

@app.route("/send", methods=["POST"])
def send():
    data = request.get_json()
    user = session.get("username", "Anonymous")
    message = data["message"]
    save_message(user, message)  # Save to SQLite
    return jsonify({"user": user, "message": message})

@app.route("/messages")
def get_messages():
    messages = load_messages()
    return jsonify(messages)
@app.route("/ping")
def ping():
    return "OK"


# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
