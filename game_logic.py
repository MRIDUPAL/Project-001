from models import Achievement, Quest, db
from models import ShopItem

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

    if achievement is None:

        db.session.add(
            Achievement(
                title=title,
                description=description,
                user_id=user_id
            )
        )


def check_achievements(user):

    completed = Quest.query.filter_by(
        user_id=user.id,
        completed=True
    ).count()

    if completed == 1:

        unlock_achievement(
            user.id,
            "🏆 First Blood",
            "Completed your first quest."
        )

    if user.level >= 5:

        unlock_achievement(
            user.id,
            "⭐ Adventurer",
            "Reached Level 5."
        )

def seed_shop():

    if ShopItem.query.first():
        return

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
            name="Neon Theme",
            description="Unlock a glowing interface.",
            icon="🌌",
            category="Theme",
            rarity="Epic",
            price=500
        ),

    ]

    db.session.add_all(items)
    db.session.commit()