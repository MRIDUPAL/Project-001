from flask import flash

from models import (
    db,
    Quest,
    ShopItem,
    Inventory,
    Achievement
)

from game_logic import (
    ALL_ACHIEVEMENTS,
    get_rank,
    xp_needed,
    coin_reward,
    check_achievements
)

class GameEngine:

    @staticmethod
    def process_player(user):

        new_achievements = check_achievements(user)

        db.session.commit()

        return new_achievements

    @staticmethod
    def notify(new_achievements):

        for achievement in new_achievements:

            flash(
                f"🏆 Achievement Unlocked! "
                f"{achievement['title']} "
                f" (+{achievement['reward']} Coins)",
                "success"
            )

    @staticmethod
    def player_stats(user):

        quests = Quest.query.filter_by(
            user_id=user.id
        ).all()

        total_quests = len(quests)

        completed_quests = sum(
            1 for quest in quests
            if quest.completed
        )

        completion_rate = (
            round(
                (completed_quests / total_quests) * 100
            )
            if total_quests > 0 else 0
        )

        max_xp = xp_needed(user.level)

        progress = (
            (user.xp / max_xp) * 100
            if max_xp > 0 else 0
        )

        return {

            # Dashboard
            "quests": quests,
            "rank": get_rank(user.level),
            "max_xp": max_xp,
            "progress": progress,
            "total_quests": total_quests,
            "completed_quests": completed_quests,
            "completion_rate": completion_rate,

            # Profile
            "level": user.level,
            "xp": user.xp,
            "coins": user.coins,
            "avatar": user.avatar,
            "streak": user.streak,

            "total_xp_earned": user.total_xp_earned,
            "total_coins_earned": user.total_coins_earned,

            "equipped_title": user.equipped_title,
            "selected_theme": user.selected_theme,
            "joined_at": user.joined_at,

            "achievement_count": len(user.achievements),
            "inventory_count": len(user.inventory)

        }

    @staticmethod
    def achievement_progress(user):

        unlocked = Achievement.query.filter_by(
            user_id=user.id
        ).all()

        unlocked_titles = {
            achievement.title
            for achievement in unlocked
        }

        completed_quests = Quest.query.filter_by(
            user_id=user.id,
            completed=True
        ).count()

        purchased_items = Inventory.query.filter_by(
            user_id=user.id
        ).count()

        achievement_list = []

        for achievement in ALL_ACHIEVEMENTS:

            if achievement["type"] == "quests":
                progress = completed_quests

            elif achievement["type"] == "level":
                progress = user.level

            elif achievement["type"] == "coins":
                progress = user.coins

            elif achievement["type"] == "shop":
                progress = purchased_items

            else:
                progress = 0

            progress_percent = min(
                (progress / achievement["target"]) * 100,
                100
            )

            achievement_list.append({

                "title": achievement["title"],

                "description": achievement["description"],

                "reward": achievement["reward"],

                "target": achievement["target"],

                "progress": progress,

                "progress_percent": progress_percent,

                "unlocked": achievement["title"] in unlocked_titles

            })

        return achievement_list

    @staticmethod
    def add_quest(user, title, difficulty):

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
            user_id=user.id
        )

        db.session.add(quest)
        db.session.commit()

        flash(
            f"📜 Quest '{title}' added!",
            "success"
        )

    @staticmethod
    def complete_quest(user, quest):

        if quest.completed:
            return

        # Complete quest
        quest.completed = True

        # Calculate rewards
        earned_coins = coin_reward(quest.difficulty)

        # Give rewards
        user.xp += quest.xp
        user.coins += earned_coins

        # Lifetime statistics
        user.total_xp_earned += quest.xp
        user.total_coins_earned += earned_coins

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

        # Process achievements and other player systems
        new_achievements = GameEngine.process_player(user)

        # Show achievement notifications
        GameEngine.notify(new_achievements)

        # Quest completion message
        flash(
            f"🎉 Quest completed! "
            f"+{quest.xp} XP "
            f"and +{earned_coins} Coins.",
            "success"
        )

    @staticmethod
    def buy_item(user, item):

        owned = Inventory.query.filter_by(
            user_id=user.id,
            item_id=item.id
        ).first()

        if owned:
            return (
                False,
                "ℹ️ You already own this item."
            )

        if user.coins < item.price:
            return (
                False,
                f"❌ You need {item.price - user.coins} more coins to buy {item.name}."
            )

        user.coins -= item.price

        db.session.add(
            Inventory(
                user_id=user.id,
                item_id=item.id
            )
        )

        new_achievements = GameEngine.process_player(user)

        GameEngine.notify(new_achievements)

        flash(
            f"✅ Successfully purchased {item.name}!",
            "success"
        )

        return (
            True,
            None
        )

    @staticmethod
    def equip_item(user, item):

        owned_item = Inventory.query.filter_by(
            user_id=user.id,
            item_id=item.id
        ).first()

        if owned_item is None:
            return (
                False,
                "❌ You don't own this item."
            )

        if item.category != "Avatar":
            return (
                False,
                "❌ Only avatars can be equipped right now."
            )

        # Unequip every avatar
        avatar_items = Inventory.query.join(ShopItem).filter(
            Inventory.user_id == user.id,
            ShopItem.category == "Avatar"
        ).all()

        for avatar in avatar_items:
            avatar.equipped = False

        # Equip selected avatar
        owned_item.equipped = True

        # Update player's avatar
        user.avatar = item.icon

        db.session.commit()

        return (
            True,
            f"✅ {item.name} equipped!"
        )