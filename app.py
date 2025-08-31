from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.utils import secure_filename
import os, json

# basic flask setup
app = Flask(__name__)
app.secret_key = "mysecret"   # just random
load_dotenv()

# openai client init
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# upload config
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXT = {'png','jpg','jpeg','gif'}

def ok_file(name):
    return '.' in name and name.rsplit('.', 1)[1].lower() in ALLOWED_EXT

# user data stuff
USERS_FILE = "users.json"
CHAT_DIR = "chat_history"
os.makedirs(CHAT_DIR, exist_ok=True)

def read_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f: json.dump({}, f)
    return json.load(open(USERS_FILE))

def write_users(u):
    with open(USERS_FILE, "w") as f: json.dump(u, f, indent=4)

@app.route("/")
def start():
    return redirect("/chat") if "username" in session else redirect("/login")

@app.route("/login", methods=["GET","POST"])
def do_login():
    if request.method == "POST":
        uname = request.form["username"]
        pwd = request.form["password"]
        users = read_users()
        if users.get(uname) == pwd:
            session["username"] = uname
            return redirect("/chat")
        return render_template("login.html", error="wrong username or password")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def do_register():
    if request.method == "POST":
        uname = request.form["username"]
        pwd = request.form["password"]
        users = read_users()

        if uname in users:
            return render_template("register.html", error="User exists")
        if "@gmail.com" not in uname or len(uname) < 10:
            return render_template("register.html", error="use proper gmail id")
        if len(pwd) < 8:
            return render_template("register.html", error="password too short")

        users[uname] = pwd
        write_users(users)
        return redirect("/login")
    return render_template("register.html")

@app.route("/forgot-password", methods=["GET","POST"])
def forgot_pwd():
    if request.method == "POST":
        uname = request.form["username"]
        npwd = request.form["new_password"]
        users = read_users()

        if uname not in users:
            return render_template("forgot_password.html", error="user not found")
        if len(npwd) < 8:
            return render_template("forgot_password.html", error="min 8 chars")

        users[uname] = npwd
        write_users(users)
        return redirect("/login")
    return render_template("forgot_password.html")

@app.route("/chat")
def chat_pg():
    if "username" not in session:
        return redirect("/login")
    return render_template("index.html", username=session["username"])

@app.route("/get", methods=["POST"])
def get_ai_reply():
    if "username" not in session:
        return jsonify({"reply": "Unauthorized"})

    data = request.get_json()
    if not data or "messages" not in data:
        return jsonify({"reply": "bad data"})

    msgs = data["messages"]
    if not msgs or not isinstance(msgs, list):
        return jsonify({"reply": "empty msg"})

    last_msg = msgs[-1].get("content", "").strip()
    if not last_msg:
        return jsonify({"reply": "no msg"})

    if not any(m["role"] == "system" for m in msgs):
        msgs.insert(0, {
            "role": "system",
            "content": (
                "You are Quick-fix.AI, you are created by Rifai, i was created by 26th july, rifai is doing engineering importantly he is a college student"
                "rifai bio : born in kayalpattinam schooling central higher secondary school and now doing college in aalim muhammed saleghh college of engineering avadi doing 2nd year B.Tech IT ( information Technology)"
                "rifai age 19, dob 26th july 2006, if they ask in tamil you can say,  Give only they ask instagram id  @Rifffffffffai"
                "rifai best firend name is sumaiya, rifai gives cutest nickname that's called Echha sumaiya, if they ask about sumaiya tell sumaiya's native chennai she speaks urdu and tamil fluently she is multitalented person"
                "having a good heart person , she is studying in aalim muhammed salegh college of engineering avadi 2nd year information technology , she born in 19.09.2006 , because rifai forget to give dairy milk thats why sumaiya call echha rifai its so cutee,- Quick-fix.AI, a smart and friendly AI assistant."
                " respond in English  (Tamil using English letters). "
                "respond in tamil (when people ask to speak in tamil)."
                "speak many languages like tamil, english, urdu, hindi, malayalam, telugu, kannada, arabic, french, german, spanish, chinese, japanese, korean, russian, italian, portuguese."
                "Understand casual phrases like 'hw r u', 'epdi iruka', 'enna panra'. "
                "Do not say you're a bot. Speak like a human friend. Be helpful, funny if needed, and clear."
            )
        })

    try:
        res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=msgs
        )
        reply_text = res.choices[0].message.content.strip()
        return jsonify({"reply": reply_text})
    except Exception as e:
        return jsonify({"reply": f"Error: {e}"})

@app.route("/save-chat", methods=["POST"])
def save_chat():
    if "username" not in session:
        return jsonify({"status": "unauthorized"})
    chat_data = request.get_json().get("messages")
    if not chat_data:
        return jsonify({"status": "no data"})

    path = os.path.join(CHAT_DIR, f"{session['username']}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(chat_data, f, indent=4, ensure_ascii=False)
        return jsonify({"status": "saved"})
    except Exception as e:
        return jsonify({"status": f"error: {e}"})


@app.route("/profile")
def my_profile():
    if "username" not in session:
        return redirect("/login")

    uname = session["username"]
    hist_file = os.path.join(CHAT_DIR, f"{uname}.json")
    history = []
    if os.path.exists(hist_file):
        with open(hist_file, encoding="utf-8") as f:
            history = json.load(f)

    chat_count = sum(1 for m in history if m.get("role") == "user")

    profile_img = None
    for ext in ALLOWED_EXT:
        img_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{uname}.{ext}")
        if os.path.exists(img_path):
            profile_img = f"{uname}.{ext}"
            break

    return render_template("profile.html", username=uname, history=history,
                           profile_image=profile_img, chat_count=chat_count)

@app.route("/upload_profile_pic", methods=["POST"])
def upload_pic():
    if "username" not in session:
        return redirect("/login")

    file = request.files.get("profile_pic")
    if not file or file.filename == "":
        return "no file"

    if ok_file(file.filename):
        uname = session["username"]
        for ext in ALLOWED_EXT:
            old = os.path.join(app.config["UPLOAD_FOLDER"], f"{uname}.{ext}")
            if os.path.exists(old): os.remove(old)

        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uname}.{ext}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        return redirect("/profile")
    return "bad file"

@app.route("/upload-chat-image", methods=["POST"])
def upload_chat_img():
    if "username" not in session:
        return jsonify({"status": "unauthorized"})

    f = request.files.get("image")
    if not f or f.filename == "":
        return jsonify({"status": "no file"})

    if ok_file(f.filename):
        fname = secure_filename(f.filename)
        f_path = os.path.join(app.config["UPLOAD_FOLDER"], fname)
        f.save(f_path)
        return jsonify({"status": "success", "url": url_for('static', filename=f"uploads/{fname}")})
    return jsonify({"status": "invalid"})

@app.route("/logout")
def bye():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
