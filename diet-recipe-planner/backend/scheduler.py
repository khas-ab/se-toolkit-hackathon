"""
APScheduler background jobs for the Diet Recipe Planner.

Jobs:
  - Daily reminder (8 AM): Send Telegram message with today's dinner recipe
  - Weekly shopping list (Sunday 9 AM): Auto-generate and send shopping list

Uses AsyncIOScheduler which integrates with the asyncio event loop.
"""
import os
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Recipe, MealPlan, MealPlanEntry, DayOfWeek
from crud import (
    get_meal_plans, generate_shopping_list_from_plan, get_shopping_list,
)

logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://recipeuser:recipepass@db:5432/recipe_db"
)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
DAILY_REMINDER_HOUR = int(os.getenv("CRON_DAILY_REMINDER_HOUR", "8"))
WEEKLY_SHOPPING_HOUR = int(os.getenv("CRON_WEEKLY_SHOPPING_HOUR", "9"))

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def send_telegram_message(text: str):
    """Send a message to the configured Telegram chat."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not set. Skipping notification.")
        return

    import httpx
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Telegram message sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")


async def daily_dinner_reminder():
    """
    Daily job: Send today's dinner recipe to the user.
    Runs at CRON_DAILY_REMINDER_HOUR (default 8 AM).
    """
    logger.info("Running daily dinner reminder job...")

    # Get today's day name
    today = datetime.now().strftime("%A").lower()
    # Map to DayOfWeek enum
    day_map = {
        "monday": DayOfWeek.MONDAY,
        "tuesday": DayOfWeek.TUESDAY,
        "wednesday": DayOfWeek.WEDNESDAY,
        "thursday": DayOfWeek.THURSDAY,
        "friday": DayOfWeek.FRIDAY,
        "saturday": DayOfWeek.SATURDAY,
        "sunday": DayOfWeek.SUNDAY,
    }
    day_enum = day_map.get(today)
    if not day_enum:
        return

    db = SessionLocal()
    try:
        plans = get_meal_plans(db)
        if not plans:
            await send_telegram_message(
                "🍽️ *Dinner Reminder*\n\n"
                "You don't have a meal plan yet. Generate one from the app or use `/plan week`!"
            )
            return

        plan = plans[0]  # Most recent plan
        # Find dinner entry for today
        dinner_entry = None
        for entry in plan.entries:
            if entry.day == day_enum and entry.meal_type.value == "dinner":
                dinner_entry = entry
                break

        if dinner_entry:
            recipe = db.query(Recipe).filter(Recipe.id == dinner_entry.recipe_id).first()
            if recipe:
                message = (
                    f"🍽️ *Dinner Reminder for Today*\n\n"
                    f"*{recipe.name}*\n\n"
                    f"🔥 {recipe.calories} cal | 🥩 {recipe.protein}g protein\n"
                    f"⏱️ Prep: {recipe.prep_time}min | Cook: {recipe.cook_time}min\n\n"
                    f"_{recipe.description[:200]}{'...' if len(recipe.description) > 200 else ''}_"
                )
                await send_telegram_message(message)
                return

        await send_telegram_message(
            f"🍽️ *Dinner Reminder*\n\n"
            f"No dinner planned for {today.capitalize()}. "
            f"Update your meal plan in the app!"
        )
    except Exception as e:
        logger.error(f"Error in daily reminder job: {e}")
    finally:
        db.close()


async def weekly_shopping_list():
    """
    Weekly job: Generate shopping list from meal plan and send to user.
    Runs on Sunday at CRON_WEEKLY_SHOPPING_HOUR (default 9 AM).
    """
    logger.info("Running weekly shopping list job...")

    db = SessionLocal()
    try:
        plans = get_meal_plans(db)
        if not plans:
            await send_telegram_message(
                "🛒 *Weekly Shopping List*\n\n"
                "No meal plan found. Generate one first!"
            )
            return

        plan = plans[0]
        generate_shopping_list_from_plan(db, plan.id)
        items = get_shopping_list(db)

        if not items:
            await send_telegram_message(
                "🛒 *Weekly Shopping List*\n\n"
                "Your shopping list is empty. You have all the ingredients for your meal plan!"
            )
            return

        # Group by category
        by_category = {}
        for item in items:
            cat = item.category or "Other"
            if cat not in by_category:
                by_category[cat] = []
            qty_str = f" ({item.quantity})" if item.quantity else ""
            by_category[cat].append(f"• {item.name}{qty_str}")

        message = "🛒 *Weekly Shopping List*\n\n"
        for category, items_list in by_category.items():
            message += f"*{category}:*\n" + "\n".join(items_list) + "\n\n"

        await send_telegram_message(message)
    except Exception as e:
        logger.error(f"Error in weekly shopping list job: {e}")
    finally:
        db.close()


def start_scheduler():
    """
    Start the APScheduler with all jobs.
    Returns the scheduler instance (caller must ensure the event loop keeps running).
    """
    scheduler = AsyncIOScheduler()

    # Daily dinner reminder at configured hour
    scheduler.add_job(
        daily_dinner_reminder,
        "cron",
        hour=DAILY_REMINDER_HOUR,
        minute=0,
        id="daily_dinner_reminder",
        replace_existing=True,
    )

    # Weekly shopping list on Sunday at configured hour
    scheduler.add_job(
        weekly_shopping_list,
        "cron",
        day_of_week="sun",
        hour=WEEKLY_SHOPPING_HOUR,
        minute=0,
        id="weekly_shopping_list",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started. Jobs: daily reminder at {DAILY_REMINDER_HOUR}:00, "
        f"weekly shopping on Sunday at {WEEKLY_SHOPPING_HOUR}:00"
    )
    return scheduler
