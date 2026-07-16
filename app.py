from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Quest, ShopItem, Inventory

from game_logic import (
    get_rank,
    xp_needed,
    coin_reward,
    check_achievements,
    seed_shop
)

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///questify.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

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

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

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

    max_xp = xp_needed(user.level)

    progress = (
        (user.xp / max_xp) * 100
        if max_xp > 0 else 0
    )

    rank = get_rank(user.level)

    quests = Quest.query.filter_by(
        user_id=user.id
    ).all()

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
        avatar=user.avatar,
        username=user.username,
        quests=quests,
        xp=user.xp,
        coins=user.coins,
        level=user.level,
        rank=rank,
        max_xp=max_xp,
        progress=progress,
        total_quests=total_quests,
        completed_quests=completed_quests,
        completion_rate=completion_rate
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

    owned = Inventory.query.filter_by(
        user_id=user.id,
        item_id=item.id
    ).first()

    if owned:
        flash("ℹ️ You already own this item.", "info")
        return redirect("/shop")

    if user.coins < item.price:
        flash(
            f"❌ You need {item.price - user.coins} more coins to buy {item.name}.",
            "danger"
        )
        return redirect("/shop")

    user.coins -= item.price

    inventory = Inventory(
        user_id=user.id,
        item_id=item.id
    )

    db.session.add(inventory)
    db.session.commit()

    flash(
        f"✅ Successfully purchased {item.name}!",
        "success"
    )

    return redirect("/shop")

@app.route("/equip/<int:item_id>", methods=["POST"])
def equip_item(item_id):

    if "user_id" not in session:
        return redirect("/login")

    user = db.session.get(User, session["user_id"])

    if user is None:
        session.clear()
        return redirect("/login")

    inventory_item = Inventory.query.filter_by(
        user_id=user.id,
        item_id=item_id
    ).first()

    if inventory_item is None:
        flash("❌ You don't own this item.", "danger")
        return redirect("/shop")

    item = db.session.get(ShopItem, item_id)

    if item.category != "Avatar":
        flash("❌ Only avatars can be equipped right now.", "warning")
        return redirect("/shop")

    # Unequip every avatar
    avatar_items = Inventory.query.join(ShopItem).filter(
        Inventory.user_id == user.id,
        ShopItem.category == "Avatar"
    ).all()

    for inv in avatar_items:
        inv.equipped = False

    # Equip selected avatar
    inventory_item.equipped = True

    # Update user's avatar
    user.avatar = item.icon

    db.session.commit()

    flash(f"✅ {item.name} equipped!", "success")

    return redirect("/shop")

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

    quest = db.session.get(Quest, quest_id)

    if quest is None:
        return redirect("/dashboard")

    if quest.user_id != session["user_id"]:
        return redirect("/dashboard")

    if not quest.completed:

        quest.completed = True

        user = db.session.get(User, session["user_id"])

        if user is None:
            session.clear()
            return redirect("/login")

        # XP
        user.xp += quest.xp

        # Coins
        user.coins += coin_reward(quest.difficulty)

        # Achievements
        check_achievements(user)

        # Level Up
        # Level Up
        needed = xp_needed(user.level)

        while user.xp >= needed:

            user.xp -= needed
            user.level += 1

            flash(
                f"⭐ Level Up! You reached Level {user.level}.",
                "success"
            )

            needed = xp_needed(user.level)

        db.session.commit()
        
        flash(
            f"🎉 Quest completed! +{quest.xp} XP, +{coin_reward(quest.difficulty)} Coins",
            "success"
        )

    return redirect("/dashboard")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)