from models import (
    db,
    User,
    Quest,
    ShopItem,
    Inventory,
    Achievement
)
from datetime import datetime

ALL_ACHIEVEMENTS = [

    {
        "title": "🩸 First Blood",
        "description": "Complete your first quest.",
        "type": "quests",
        "target": 1,
        "reward": 50
    },

    {
        "title": "⚔️ Adventurer",
        "description": "Complete 10 quests.",
        "type": "quests",
        "target": 10,
        "reward": 100
    },

    {
        "title": "📜 Quest Master",
        "description": "Complete 50 quests.",
        "type": "quests",
        "target": 50,
        "reward": 300
    },

    {
        "title": "⭐ Rising Star",
        "description": "Reach Level 5.",
        "type": "level",
        "target": 5,
        "reward": 150
    },

    {
        "title": "🛡️ Hero",
        "description": "Reach Level 10.",
        "type": "level",
        "target": 10,
        "reward": 300
    },

    {
        "title": "💰 Rich",
        "description": "Collect 1000 Coins.",
        "type": "coins",
        "target": 1000,
        "reward": 200
    },

    {
        "title": "🛒 Shopper",
        "description": "Buy your first shop item.",
        "type": "shop",
        "target": 1,
        "reward": 100
    },

    {
        "title": "🐉 Legend",
        "description": "Reach Level 40.",
        "type": "level",
        "target": 40,
        "reward": 500
    }

]

def get_rank(level):
    if level < 5:
        return "🌱 Novice"
    elif level < 10:
        return "⚔️ Adventurer"
    elif level < 20:
        return "🛡️ Hero"
    elif level < 40:
        return "👑 Champion"
    return "🐉 Legend"


def xp_needed(level):
    return 500 + ((level - 1) * 250)


def coin_reward(difficulty):
    rewards = {
        "Easy": 10,
        "Medium": 20,
        "Hard": 40,
        "Epic": 100
    }
    return rewards.get(difficulty, 0)


def unlock_achievement(user_id, title, description):

    achievement = Achievement.query.filter_by(
        user_id=user_id,
        title=title
    ).first()

    if achievement is not None:
        return False

    db.session.add(
        Achievement(
            title=title,
            description=description,
            user_id=user_id
        )
    )

    return True

def check_achievements(user):

    completed_quests = Quest.query.filter_by(
        user_id=user.id,
        completed=True
    ).count()

    purchased_items = Inventory.query.filter_by(
        user_id=user.id
    ).count()

    unlocked_now = []

    for achievement in ALL_ACHIEVEMENTS:

        title = achievement["title"]

        already_unlocked = Achievement.query.filter_by(
            user_id=user.id,
            title=title
        ).first()

        if already_unlocked:
            continue

        progress = 0

        if achievement["type"] == "quests":
            progress = completed_quests

        elif achievement["type"] == "level":
            progress = user.level

        elif achievement["type"] == "coins":
            # Use lifetime coins earned instead of current balance
            progress = user.total_coins_earned

        elif achievement["type"] == "shop":
            progress = purchased_items

        if progress >= achievement["target"]:

            if unlock_achievement(
                user.id,
                achievement["title"],
                achievement["description"]
            ):

                print("========== ACHIEVEMENT ==========")
                print("Before:")
                print("Coins:", user.coins)
                print("Lifetime:", user.total_coins_earned)

                user.coins += achievement["reward"]
                user.total_coins_earned += achievement["reward"]

                print("Reward:", achievement["reward"])

                print("After:")
                print("Coins:", user.coins)
                print("Lifetime:", user.total_coins_earned)
                print("=================================")
                
                unlocked_now.append({
                    "title": achievement["title"],
                    "reward": achievement["reward"]
                })

    return unlocked_now

def seed_shop():

    items = [

        ShopItem(
            name="Robot Avatar",
            description="Become a futuristic robot.",
            icon="🤖",
            category="Avatar",
            rarity="Common",
            price=250
        ),

        ShopItem(
            name="Ninja Avatar",
            description="Move in the shadows.",
            icon="🥷",
            category="Avatar",
            rarity="Rare",
            price=400
        ),

        ShopItem(
            name="Wizard Avatar",
            description="Master of magic.",
            icon="🧙",
            category="Avatar",
            rarity="Epic",
            price=600
        ),

        ShopItem(
            name="Champion Title",
            description="Show everyone your rank.",
            icon="👑",
            category="Title",
            rarity="Legendary",
            price=1000
        ),

        ShopItem(
            name="neon Theme",
            description="Unlock a glowing interface.",
            icon="🌌",
            category="Theme",
            rarity="Epic",
            price=4
        ),

        ShopItem(
            name="gold Theme",
            description="A luxurious golden theme.",
            icon="👑",
            category="Theme",
            rarity="Epic",
            price=4
        ),

        ShopItem(
            name="crimson Theme",
            description="A stunning crimson theme.",
            icon="👑",
            category="Theme",
            rarity="Epic",
            price=4
        ),

        ShopItem(
            name="night Theme",
            description="A mysterious night theme.",
            icon="👑",
            category="Theme",
            rarity="Epic",
            price=4
        ),

        ShopItem(
            name="emerald Theme",
            description="An elegant emerald theme.",
            icon="👑",
            category="Theme",
            rarity="Epic",
            price=4
        ),

    ]

    for item in items:
        exists = ShopItem.query.filter_by(name=item.name).first()

        if not exists:
            db.session.add(item)

    db.session.commit()