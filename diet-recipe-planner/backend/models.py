"""
SQLAlchemy ORM models representing the database tables.
Each class maps to a table in PostgreSQL.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, ARRAY, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


# ─── Enum Types ───────────────────────────────────────────────

class DietType(str, enum.Enum):
    """Supported diet types for user preferences and recipe filtering."""
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    KETO = "keto"
    PALEO = "paleo"
    LOW_CARB = "low_carb"
    MEDITERRANEAN = "mediterranean"
    NONE = "none"


class MealType(str, enum.Enum):
    """Meal slot types for the weekly planner."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class DayOfWeek(str, enum.Enum):
    """Days of the week for meal planning."""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


# ─── Models ───────────────────────────────────────────────────

class Recipe(Base):
    """
    A recipe with ingredients, steps, nutritional info, and tags.
    Ingredients stored as JSONB-like text array: ["200g chicken breast", "1 cup rice"]
    """
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, default="")
    # Each ingredient as a string like "200g chicken breast"
    ingredients = Column(ARRAY(String), nullable=False)
    # Step-by-step instructions
    steps = Column(ARRAY(String), nullable=False)
    # Nutritional macros per serving
    protein = Column(Float, default=0.0)       # grams
    fat = Column(Float, default=0.0)           # grams
    carbs = Column(Float, default=0.0)         # grams
    calories = Column(Float, default=0.0)      # kcal
    prep_time = Column(Integer, default=0)     # minutes
    cook_time = Column(Integer, default=0)     # minutes
    servings = Column(Integer, default=1)
    # Tags for filtering: ["keto", "high-protein", "asian"]
    tags = Column(ARRAY(String), default=[])
    cuisine = Column(String(100), default="")  # e.g. "Italian", "Mexican"
    image_url = Column(String(500), default="")  # placeholder or real URL
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    meal_plan_entries = relationship("MealPlanEntry", back_populates="recipe")


class UserIngredient(Base):
    """
    Ingredients the user currently has on hand.
    Used by the /suggest endpoint to find matching recipes.
    """
    __tablename__ = "user_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    quantity = Column(String(50), default="")  # e.g. "500g", "1 dozen"
    added_at = Column(DateTime, default=datetime.utcnow)


class MealPlan(Base):
    """
    A named weekly meal plan (e.g. "Week of Jan 15").
    Contains multiple MealPlanEntry records.
    """
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), default="Weekly Plan")
    week_start_date = Column(String(20), default="")  # ISO date string
    created_at = Column(DateTime, default=datetime.utcnow)

    entries = relationship("MealPlanEntry", back_populates="plan", cascade="all, delete-orphan")


class MealPlanEntry(Base):
    """
    A single meal slot: e.g. Monday Breakfast = Recipe #5
    """
    __tablename__ = "meal_plan_entries"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("meal_plans.id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    day = Column(SAEnum(DayOfWeek), nullable=False)
    meal_type = Column(SAEnum(MealType), nullable=False)

    plan = relationship("MealPlan", back_populates="entries")
    recipe = relationship("Recipe", back_populates="meal_plan_entries")


class ShoppingListItem(Base):
    """
    A single item on the user's shopping list.
    Auto-generated from meal plan + missing ingredients, or added manually.
    """
    __tablename__ = "shopping_list"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    quantity = Column(String(100), default="")  # e.g. "400g", "2 cups"
    category = Column(String(100), default="")  # e.g. "Produce", "Dairy", "Meat"
    purchased = Column(Integer, default=0)      # 0 = not purchased, 1 = purchased
    created_at = Column(DateTime, default=datetime.utcnow)


class UserPreference(Base):
    """
    User's dietary preferences used by the agent and planner.
    Single-row table (id=1) for the current user.
    """
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    daily_calorie_target = Column(Integer, default=2000)
    diet_type = Column(SAEnum(DietType), default=DietType.NONE)
    allergies = Column(ARRAY(String), default=[])  # e.g. ["peanuts", "shellfish"]
    protein_target = Column(Integer, default=0)    # grams per day
    excluded_ingredients = Column(ARRAY(String), default=[])  # ingredients to avoid
