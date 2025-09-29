from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_key")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")  # force gevent

DB_FILE = "chat1.db"

# ---------------------------
# Database helpers
# ---------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            message TEXT
        )
    """)
    conn.commit()
    conn.close()

def load_messages():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user, message FROM messages ORDER BY id ASC")
    msgs = [{"user": row[0], "message": row[1]} for row in c.fetchall()]
    conn.close()
    return msgs

def save_message(user, message):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO messages (user, message) VALUES (?, ?)", (user, message))
    conn.commit()
    conn.close()

init_db()

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def index():
    if "username" not in session:
        session["username"] = f"User{os.urandom(2).hex()}"  # temporary random username
    return render_template("chat.html", current_user=session["username"], messages=load_messages())

@app.route("/change_name", methods=["POST"])
def change_name():
    data = request.get_json()
    session["username"] = data.get("username", session.get("username"))
    return "OK"

# ---------------------------
# Socket.IO events
# ---------------------------
@socketio.on("send_message")
def handle_message(data):
    user = data.get("user")
    message = data.get("message")
    save_message(user, message)
    emit("receive_message", {"user": user, "message": message}, broadcast=True, include_self=False)

# ---------------------------
if __name__ == "__main__":
    # Run with gevent to avoid eventlet issues on Windows
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(("0.0.0.0", 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
