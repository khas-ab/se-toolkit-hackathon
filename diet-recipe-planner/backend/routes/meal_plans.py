"""
Meal plan API routes.
GET /api/meal-plans - list all plans
POST /api/meal-plans - create a new plan
GET /api/meal-plans/{id} - get plan with entries
POST /api/meal-plans/{id}/entries - add a recipe to a day/meal slot
DELETE /api/meal-plans/entries/{entry_id} - remove a meal slot
GET /api/meal-plans/{id}/nutrition - get weekly nutrition summary
POST /api/meal-plans/generate - auto-generate a weekly plan based on preferences
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import (
    MealPlanCreate, MealPlanResponse, MealPlanEntryCreate,
    MealPlanEntryResponse, NutritionSummary, RecipeResponse,
    UserPreferenceCreate,
)
from models import DayOfWeek, MealType
import crud
import random

router = APIRouter(prefix="/api", tags=["meal-plans"])


@router.get("/meal-plans", response_model=List[MealPlanResponse])
def list_plans(db: Session = Depends(get_db)):
    """List all meal plans, most recent first."""
    return crud.get_meal_plans(db)


@router.post("/meal-plans", response_model=MealPlanResponse, status_code=201)
def create_plan(data: MealPlanCreate, db: Session = Depends(get_db)):
    """Create a new empty meal plan."""
    return crud.create_meal_plan(db, data)


@router.get("/meal-plans/{plan_id}", response_model=MealPlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get a meal plan with all its entries and recipe details."""
    plan = crud.get_meal_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return plan


@router.post("/meal-plans/{plan_id}/entries", response_model=MealPlanEntryResponse)
def add_entry(
    plan_id: int,
    recipe_id: int,
    day: DayOfWeek,
    meal_type: MealType,
    db: Session = Depends(get_db),
):
    """
    Add a recipe to a specific day and meal type in the plan.
    If the slot already exists, replaces the recipe.
    """
    entry = crud.add_meal_plan_entry(db, plan_id, recipe_id, day, meal_type)
    if not entry:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return entry


@router.delete("/meal-plans/entries/{entry_id}", status_code=204)
def remove_entry(entry_id: int, db: Session = Depends(get_db)):
    """Remove a meal plan entry."""
    if not crud.remove_meal_plan_entry(db, entry_id):
        raise HTTPException(status_code=404, detail="Entry not found")


@router.get("/meal-plans/{plan_id}/nutrition", response_model=NutritionSummary)
def get_nutrition(plan_id: int, db: Session = Depends(get_db)):
    """Get weekly nutrition breakdown for a meal plan."""
    plan = crud.get_meal_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return crud.get_weekly_nutrition(db, plan_id)


@router.post("/meal-plans/generate", response_model=MealPlanResponse)
def generate_plan(
    plan_name: str = "Auto-Generated Weekly Plan",
    db: Session = Depends(get_db),
):
    """
    Auto-generate a 7-day meal plan based on user preferences.
    Picks recipes that match the user's diet type and calorie targets,
    filling each day's breakfast, lunch, and dinner slots.
    """
    # Get user preferences
    prefs = crud.get_user_preference(db)
    diet_tag = prefs.diet_type.value if prefs and prefs.diet_type.value != "none" else None
    max_calories = prefs.daily_calorie_target // 3 if prefs else 700  # per meal estimate

    # Fetch matching recipes
    all_recipes = crud.get_recipes(
        db, limit=200,
        max_calories=max_calories,
        diet_type=diet_tag,
    )

    if not all_recipes:
        # Fallback: get any recipes if no filtered ones found
        all_recipes = crud.get_recipes(db, limit=200)

    if not all_recipes:
        raise HTTPException(status_code=404, detail="No recipes available to generate a plan")

    # Categorize recipes by typical meal type (using tags or name hints)
    breakfast_recipes = [r for r in all_recipes if "breakfast" in r.name.lower() or "breakfast" in [t.lower() for t in r.tags]]
    lunch_recipes = [r for r in all_recipes if "lunch" in r.name.lower() or "salad" in r.name.lower() or "soup" in r.name.lower()]
    dinner_recipes = [r for r in all_recipes if "dinner" in r.name.lower()]

    # Fallback: if categories are empty, use all recipes for each meal
    if not breakfast_recipes:
        breakfast_recipes = all_recipes
    if not lunch_recipes:
        lunch_recipes = all_recipes
    if not dinner_recipes:
        dinner_recipes = all_recipes

    # Create the plan
    plan = crud.create_meal_plan(db, MealPlanCreate(name=plan_name))

    days = list(DayOfWeek)
    used_recipes = set()  # Avoid repeating recipes too much

    for day in days:
        # Pick breakfast
        bf_candidates = [r for r in breakfast_recipes if r.id not in used_recipes] or breakfast_recipes
        bf = random.choice(bf_candidates)
        crud.add_meal_plan_entry(db, plan.id, bf.id, day, MealType.BREAKFAST)
        used_recipes.add(bf.id)

        # Pick lunch
        ln_candidates = [r for r in lunch_recipes if r.id not in used_recipes] or lunch_recipes
        ln = random.choice(ln_candidates)
        crud.add_meal_plan_entry(db, plan.id, ln.id, day, MealType.LUNCH)
        used_recipes.add(ln.id)

        # Pick dinner
        dn_candidates = [r for r in dinner_recipes if r.id not in used_recipes] or dinner_recipes
        dn = random.choice(dn_candidates)
        crud.add_meal_plan_entry(db, plan.id, dn.id, day, MealType.DINNER)
        used_recipes.add(dn.id)

    db.commit()
    return crud.get_meal_plan(db, plan.id)
