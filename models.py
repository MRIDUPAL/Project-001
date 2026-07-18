from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    # ------------------------
    # Player Progress
    # ------------------------

    level = db.Column(db.Integer, default=1)

    xp = db.Column(db.Integer, default=0)

    coins = db.Column(db.Integer, default=0)

    avatar = db.Column(
        db.String(20),
        default="🎮"
    )

    streak = db.Column(
        db.Integer,
        default=0
    )

    # ------------------------
    # Profile Statistics
    # ------------------------

    total_xp_earned = db.Column(
        db.Integer,
        default=0
    )

    total_coins_earned = db.Column(
        db.Integer,
        default=0
    )

    equipped_title = db.Column(
        db.String(100),
        default="Adventurer"
    )

    selected_theme = db.Column(
        db.String(100),
        default="Default"
    )

    joined_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # ------------------------
    # Relationships
    # ------------------------

    quests = db.relationship(
        "Quest",
        backref="user",
        lazy=True
    )

    achievements = db.relationship(
        "Achievement",
        backref="user",
        lazy=True
    )

    def __repr__(self):
        return f"<User {self.username}>"


class Quest(db.Model):
    __tablename__ = "quests"

    id = db.Column(db.Integer, primary_key=True)

    # ------------------------
    # Quest Information
    # ------------------------

    title = db.Column(
        db.String(100),
        nullable=False
    )

    description = db.Column(
        db.Text,
        default=""
    )

    category = db.Column(
        db.String(30),
        default="Personal"
    )

    difficulty = db.Column(
        db.String(20),
        nullable=False
    )

    quest_type = db.Column(
        db.String(20),
        default="One-Time"
    )

    # ------------------------
    # Rewards
    # ------------------------

    xp = db.Column(
        db.Integer,
        nullable=False
    )

    # ------------------------
    # Progress
    # ------------------------

    completed = db.Column(
        db.Boolean,
        default=False
    )

    due_date = db.Column(
        db.Date,
        nullable=True
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    expired = db.Column(
    db.Boolean,
    default=False
    )

    # ------------------------
    # Ownership
    # ------------------------

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )


class Achievement(db.Model):
    __tablename__ = "achievements"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100), nullable=False)

    description = db.Column(db.String(200), nullable=False)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    def __repr__(self):
        return f"<Achievement {self.title}>"

class ShopItem(db.Model):
    __tablename__ = "shop_items"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    description = db.Column(db.String(200))

    icon = db.Column(db.String(20), nullable=False)

    category = db.Column(db.String(30), nullable=False)

    rarity = db.Column(
    db.String(20),
    default="Common"
    )

    price = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<ShopItem {self.name}>"


class Inventory(db.Model):
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    item_id = db.Column(
        db.Integer,
        db.ForeignKey("shop_items.id"),
        nullable=False
    )

    equipped = db.Column(
    db.Boolean,
    default=False
    )

    user = db.relationship("User", backref="inventory")

    item = db.relationship("ShopItem")