from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Quest, ShopItem, Inventory, Achievement
from game_logic import (
    get_rank,
    xp_needed,
    seed_shop,
)
from game_engine import GameEngine
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///questify.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.context_processor
def inject_current_user():

    if "user_id" in session:

        user = db.session.get(User, session["user_id"])

    else:

        user = None

    return dict(current_user=user)

with app.app_context():
    db.create_all()
    seed_shop()

@app.route("/")
def home():

    if "user_id" in session:
        return redirect("/dashboard")

    return render_template("index.html")


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


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return redirect("/register")

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "warning")
            return redirect("/register")

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        GameEngine.create_default_quests(new_user)

        return redirect("/login")

    return render_template("register.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    user = db.session.get(User, session["user_id"])

    if user is None:
        session.clear()
        return redirect("/login")

    GameEngine.reset_recurring_quests(user)
    GameEngine.expire_limited_time_quests(user)

    filter_type = request.args.get(
        "filter",
        "All"
    )

    stats = GameEngine.player_stats(user)

    quests = stats["quests"]

    if filter_type != "All":
        quests = [
            quest
            for quest in quests
            if quest.quest_type == filter_type
        ]

    stats["quests"] = quests

    return render_template(
        "dashboard.html",

        avatar=user.avatar,
        username=user.username,

        quests=stats["quests"],

        xp=user.xp,
        coins=user.coins,
        level=user.level,

        rank=stats["rank"],

        max_xp=stats["max_xp"],

        progress=stats["progress"],

        total_quests=stats["total_quests"],

        completed_quests=stats["completed_quests"],

        completion_rate=stats["completion_rate"],

        current_filter=filter_type
    )

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    if user is None:
        flash("Please login first.", "warning")
        return redirect("/login")

    stats = GameEngine.player_stats(user)

    return render_template(
        "profile.html",
        user=user,
        stats=stats
    )

@app.route("/shop")
def shop():

    if "user_id" not in session:
        return redirect("/login")

    user = db.session.get(User, session["user_id"])

    if user is None:
        session.clear()
        return redirect("/login")

    items = ShopItem.query.order_by(
        ShopItem.price
    ).all()

    owned_items = Inventory.query.filter_by(
        user_id=user.id
    ).all()

    owned_ids = [item.item_id for item in owned_items]

    equipped_ids = [
        item.item_id
        for item in owned_items
        if item.equipped
    ]

    return render_template(
        "shop.html",
        username=user.username,
        avatar=user.avatar,
        coins=user.coins,
        items=items,
        owned_ids=owned_ids,
        equipped_ids=equipped_ids
    )

@app.route("/achievements")
def achievements():

    if "user_id" not in session:
        return redirect("/login")

    user = db.session.get(User, session["user_id"])

    if user is None:
        session.clear()
        return redirect("/login")

    achievement_list = GameEngine.achievement_progress(user)

    return render_template(
        "achievements.html",
        achievements=achievement_list
    )

@app.route("/buy/<int:item_id>", methods=["POST"])
def buy_item(item_id):

    if "user_id" not in session:
        return redirect("/login")

    user = db.session.get(User, session["user_id"])

    if user is None:
        session.clear()
        return redirect("/login")

    item = db.session.get(ShopItem, item_id)

    if item is None:
        return redirect("/shop")

    success, message = GameEngine.buy_item(
        user,
        item
    )

    if not success:
        flash(message, "warning")

    return redirect("/shop")

@app.route("/inventory")
def inventory():

    if "user_id" not in session:
        return redirect("/login")

    user = db.session.get(User, session["user_id"])

    inventory = (
        Inventory.query
        .filter_by(user_id=user.id)
        .join(ShopItem)
        .all()
    )

    avatars = []
    titles = []
    themes = []

    for inv in inventory:

        if inv.item.category == "Avatar":
            avatars.append(inv)

        elif inv.item.category == "Title":
            titles.append(inv)

        elif inv.item.category == "Theme":
            themes.append(inv)

    return render_template(
        "inventory.html",
        avatars=avatars,
        titles=titles,
        themes=themes
    )

@app.route("/equip/<int:item_id>", methods=["POST"])
def equip_item(item_id):

    if "user_id" not in session:
        return redirect("/login")

    user = db.session.get(User, session["user_id"])

    if user is None:
        session.clear()
        return redirect("/login")

    item = db.session.get(ShopItem, item_id)

    if item is None:
        flash("❌ Item not found.", "danger")
        return redirect("/inventory")

    success, message = GameEngine.equip_item(user, item)

    flash(
        message,
        "success" if success else "warning"
    )

    return redirect("/inventory")

@app.route("/add_quest", methods=["POST"])
def add_quest():

    if "user_id" not in session:
        return redirect("/login")

    title = request.form["title"].strip()
    description = request.form.get("description", "").strip()
    difficulty = request.form["difficulty"]
    category = request.form["category"]
    quest_type = request.form["quest_type"]

    due_date = request.form.get("due_date")

    if due_date == "":
        due_date = None

    # -------------------------
    # Validation
    # -------------------------

    if quest_type == "Limited-Time" and due_date is None:
        flash(
            "⏳ Limited-Time quests require a due date.",
            "warning"
        )
        return redirect("/dashboard")

    if due_date:

        parsed_due_date = datetime.strptime(
            due_date,
            "%Y-%m-%d"
        ).date()

        if parsed_due_date < date.today():

            flash(
                "⏳ Due date cannot be in the past.",
                "warning"
            )

            return redirect("/dashboard")

    # -------------------------

    user = db.session.get(User, session["user_id"])

    if user is None:
        session.clear()
        return redirect("/login")

    GameEngine.add_quest(
        user=user,
        title=title,
        description=description,
        difficulty=difficulty,
        category=category,
        quest_type=quest_type,
        due_date=due_date
    )

    return redirect("/dashboard")

@app.route("/complete/<int:quest_id>", methods=["POST"])
def complete_quest(quest_id):

    if "user_id" not in session:
        return redirect("/login")

    quest = db.session.get(Quest, quest_id)

    if quest is None:
        return redirect("/dashboard")

    if quest.user_id != session["user_id"]:
        return redirect("/dashboard")

    user = db.session.get(User, session["user_id"])

    if user is None:
        session.clear()
        return redirect("/login")

    if not quest.completed:
        GameEngine.complete_quest(user, quest)

    return redirect("/dashboard")

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)