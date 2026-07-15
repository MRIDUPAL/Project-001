from flask import Flask, render_template, request, redirect, session
from models import db, User, Quest
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

def get_rank(level):

    if level < 5:
        return "🌱 Novice"

    elif level < 10:
        return "⚔️ Adventurer"

    elif level < 20:
        return "🛡️ Hero"

    elif level < 40:
        return "👑 Champion"

    else:
        return "🐉 Legend"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///questify.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id
            session["username"] = user.username

            return redirect("/dashboard")

        return "Invalid email or password"

    return render_template("login.html")

@app.route("/")
def home():

    if "user_id" in session:
        return redirect("/dashboard")

    return render_template("index.html")

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    max_xp = 500 + ((user.level - 1) * 250)
    progress = (user.xp / max_xp) * 100 if max_xp > 0 else 0
    rank = get_rank(user.level)

    quests = Quest.query.filter_by(
        user_id=session["user_id"]
    ).all()

    # Player Statistics
    total_quests = len(quests)

    completed_quests = sum(
        1 for quest in quests if quest.completed
    )

    completion_rate = (
        round((completed_quests / total_quests) * 100)
        if total_quests > 0 else 0
    )

    return render_template(
        "dashboard.html",
        username=user.username,
        quests=quests,
        xp=user.xp,
        level=user.level,
        rank=rank,
        max_xp=max_xp,
        progress=progress,
        total_quests=total_quests,
        completed_quests=completed_quests,
        completion_rate=completion_rate
    )

@app.route("/add_quest", methods=["POST"])
def add_quest():

    if "user_id" not in session:
        return redirect("/login")

    title = request.form["title"]
    difficulty = request.form["difficulty"]

    xp_values = {
        "Easy": 25,
        "Medium": 50,
        "Hard": 100,
        "Epic": 250
    }

    quest = Quest(
        title=title,
        difficulty=difficulty,
        xp=xp_values[difficulty],
        user_id=session["user_id"]
    )

    db.session.add(quest)
    db.session.commit()

    return redirect("/dashboard")

@app.route("/complete/<int:quest_id>", methods=["POST"])
def complete_quest(quest_id):

    if "user_id" not in session:
        return redirect("/login")

    quest = Quest.query.get_or_404(quest_id)

    if quest.user_id != session["user_id"]:
        return redirect("/dashboard")

    if not quest.completed:

        quest.completed = True

        user = User.query.get(session["user_id"])

        user.xp += quest.xp

        xp_needed = 500 + ((user.level - 1) * 250)

        while user.xp >= xp_needed:
            user.xp -= xp_needed
            user.level += 1
            xp_needed = 500 + ((user.level - 1) * 250)

        db.session.commit()

    return redirect("/dashboard")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        new_user = User(
        username=username,
        email=email,
        password=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)