"""
Telegram bot for the Diet Recipe Planner.
Uses python-telegram-bot v20+ with polling mode.

Commands:
  /add <ingredients>  — Add ingredients to your pantry
  /suggest            — Get top 3 recipe suggestions
  /plan week          — Generate a 7-day meal plan
  /shopping           — Get your grocery list
"""
import os
import logging
from typing import Optional
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Recipe, UserIngredient, MealPlan, MealPlanEntry, ShoppingListItem
from crud import (
    get_user_ingredients, add_user_ingredient, get_user_ingredient_names,
    search_recipes_by_ingredients, get_recipes, get_meal_plans,
    generate_shopping_list_from_plan, get_shopping_list,
    generate_plan_from_preferences,
)

# ─── Configuration ───────────────────────────────────────────

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://recipeuser:recipepass@db:5432/recipe_db"
)

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Database setup for bot (separate from FastAPI's dependency injection)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Get a database session for the bot."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def format_recipe_card(recipe: Recipe) -> str:
    """Format a recipe as a readable Telegram message."""
    macros = (
        f"🔥 {recipe.calories} cal | "
        f"🥩 {recipe.protein}g protein | "
        f"🧈 {recipe.fat}g fat | "
        f"🌾 {recipe.carbs}g carbs"
    )
    tags = f"🏷️ {', '.join(recipe.tags)}" if recipe.tags else ""
    time_info = f"⏱️ Prep: {recipe.prep_time}min | Cook: {recipe.cook_time}min"

    return (
        f"🍽️ *{recipe.name}*\n"
        f"{macros}\n"
        f"{time_info}\n"
        f"{tags}\n"
        f"_{recipe.description[:150]}{'...' if len(recipe.description) > 150 else ''}_"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(
        "🍽️ *Welcome to Diet Recipe Planner!*\n\n"
        "I can help you with:\n"
        "• `/add chicken, rice, broccoli` — Add ingredients to your pantry\n"
        "• `/suggest` — Get recipe suggestions based on what you have\n"
        "• `/plan week` — Generate a 7-day meal plan\n"
        "• `/shopping` — Get your grocery list\n\n"
        "Just type a command to get started!",
        parse_mode="Markdown",
    )


async def add_ingredients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /add command.
    Parses comma-separated ingredients and adds them to the user's pantry.
    Example: /add chicken, rice, broccoli
    """
    if not context.args:
        await update.message.reply_text(
            "Please provide ingredients to add.\n"
            "Example: `/add chicken, rice, broccoli`",
            parse_mode="Markdown",
        )
        return

    # Parse comma-separated list
    ingredient_names = [name.strip() for name in " ".join(context.args).split(",")]

    db = SessionLocal()
    try:
        added = []
        for name in ingredient_names:
            if name:
                from schemas import UserIngredientCreate
                add_user_ingredient(db, UserIngredientCreate(name=name))
                added.append(name)

        if added:
            await update.message.reply_text(
                f"✅ Added to your pantry:\n" + "\n".join(f"• {name}" for name in added)
            )
        else:
            await update.message.reply_text("No valid ingredients provided.")
    finally:
        db.close()


async def suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /suggest command.
    Returns top 3 recipes based on user's available ingredients.
    """
    db = SessionLocal()
    try:
        user_ing = get_user_ingredient_names(db)

        if user_ing:
            recipes = search_recipes_by_ingredients(db, user_ing, min_match=1, limit=3)
        else:
            # No ingredients, show random popular recipes
            recipes = get_recipes(db, limit=3)

        if not recipes:
            await update.message.reply_text(
                "No recipes found yet. Add some ingredients first with `/add`!",
                parse_mode="Markdown",
            )
            return

        for recipe in recipes:
            await update.message.reply_text(
                format_recipe_card(recipe),
                parse_mode="Markdown",
            )
    finally:
        db.close()


async def plan_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /plan week command.
    Generates a 7-day meal plan and returns a summary.
    """
    db = SessionLocal()
    try:
        plan = generate_plan_from_preferences(db, plan_name="Telegram Weekly Plan")

        # Build summary
        summary = f"📅 *{plan.name}*\n\n"
        entries_by_day = {}
        for entry in plan.entries:
            day = entry.day.value.capitalize()
            if day not in entries_by_day:
                entries_by_day[day] = {}
            recipe = db.query(Recipe).filter(Recipe.id == entry.recipe_id).first()
            if recipe:
                entries_by_day[day][entry.meal_type.value] = recipe.name

        for day, meals in entries_by_day.items():
            summary += f"*{day}:*\n"
            for meal_type, recipe_name in meals.items():
                emoji = {"breakfast": "🌅", "lunch": "☀️", "dinner": "🌙", "snack": "🍪"}
                summary += f"  {emoji.get(meal_type, '•')} {meal_type.capitalize()}: {recipe_name}\n"
            summary += "\n"

        # Telegram has message length limits, so send in chunks if needed
        if len(summary) > 4000:
            for i in range(0, len(summary), 4000):
                await update.message.reply_text(
                    summary[i:i+4000],
                    parse_mode="Markdown",
                )
        else:
            await update.message.reply_text(summary, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error generating meal plan: {e}")
        await update.message.reply_text(f"❌ Error generating meal plan: {str(e)}")
    finally:
        db.close()


async def shopping_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /shopping command.
    Sends the grocery list as a formatted message.
    """
    db = SessionLocal()
    try:
        # First try to generate from the latest meal plan
        plans = get_meal_plans(db)
        if plans:
            generate_shopping_list_from_plan(db, plans[0].id)

        items = get_shopping_list(db)
        if not items:
            await update.message.reply_text(
                "🛒 Your shopping list is empty!\n"
                "Generate a meal plan first with `/plan week`.",
                parse_mode="Markdown",
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

        message = "🛒 *Shopping List*\n\n"
        for category, items_list in by_category.items():
            message += f"*{category}:*\n" + "\n".join(items_list) + "\n\n"

        if len(message) > 4000:
            for i in range(0, len(message), 4000):
                await update.message.reply_text(
                    message[i:i+4000],
                    parse_mode="Markdown",
                )
        else:
            await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error getting shopping list: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        db.close()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command messages (echo help)."""
    await update.message.reply_text(
        "I understand commands only. Use /start to see available commands."
    )


def run_bot():
    """
    Start the Telegram bot with polling.
    This function blocks and runs the bot indefinitely.
    """
    if not BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set. Telegram bot will not start.")
        return

    logger.info("Starting Telegram bot...")

    # Build the application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_ingredients))
    app.add_handler(CommandHandler("suggest", suggest))
    app.add_handler(CommandHandler("plan", plan_week))
    app.add_handler(CommandHandler("shopping", shopping_list))

    # Handle non-command messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    run_bot()
