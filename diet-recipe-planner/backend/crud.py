"""
CRUD (Create, Read, Update, Delete) operations for all database models.
Each function takes a SQLAlchemy session and returns model instances or lists.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from models import (
    Recipe, UserIngredient, MealPlan, MealPlanEntry,
    ShoppingListItem, UserPreference, DayOfWeek, MealType
)
from schemas import (
    RecipeCreate, RecipeUpdate,
    UserIngredientCreate,
    MealPlanCreate,
    ShoppingListItemCreate, ShoppingListItemUpdate,
    UserPreferenceCreate,
)


# ─── Recipe CRUD ─────────────────────────────────────────────

def get_recipe(db: Session, recipe_id: int) -> Recipe | None:
    """Fetch a single recipe by ID."""
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()


def get_recipes(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    max_calories: int | None = None,
    max_prep_time: int | None = None,
    diet_type: str | None = None,
    tags: list[str] | None = None,
    search: str | None = None,
) -> list[Recipe]:
    """
    Fetch recipes with optional filters.
    - max_calories: filter recipes <= this calorie count
    - max_prep_time: filter recipes <= this prep time in minutes
    - diet_type: filter by tag matching the diet (e.g. "keto")
    - tags: filter recipes that have ALL specified tags
    - search: search in name, description, and ingredients
    """
    query = db.query(Recipe)

    if max_calories is not None:
        query = query.filter(Recipe.calories <= max_calories)
    if max_prep_time is not None:
        query = query.filter(Recipe.prep_time <= max_prep_time)
    if diet_type:
        # Match diet type as a tag (e.g. recipes tagged "keto")
        query = query.filter(Recipe.tags.any(diet_type.lower()))
    if tags:
        # Recipe must have ALL specified tags
        for tag in tags:
            query = query.filter(Recipe.tags.any(tag.lower()))
    if search:
        # Search across name, description, and ingredients
        search_pattern = f"%{search.lower()}%"
        query = query.filter(
            or_(
                Recipe.name.ilike(search_pattern),
                Recipe.description.ilike(search_pattern),
                Recipe.cuisine.ilike(search_pattern),
            )
        )

    return query.offset(skip).limit(limit).all()


def create_recipe(db: Session, recipe: RecipeCreate) -> Recipe:
    """Create a new recipe."""
    db_recipe = Recipe(**recipe.model_dump())
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe


def update_recipe(db: Session, recipe_id: int, updates: RecipeUpdate) -> Recipe | None:
    """Update an existing recipe. Only provided fields are changed."""
    db_recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not db_recipe:
        return None
    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_recipe, key, value)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe


def delete_recipe(db: Session, recipe_id: int) -> bool:
    """Delete a recipe. Returns True if deleted, False if not found."""
    db_recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not db_recipe:
        return False
    db.delete(db_recipe)
    db.commit()
    return True


def search_recipes_by_ingredients(
    db: Session,
    available_ingredients: list[str],
    min_match: int = 2,
    limit: int = 10,
) -> list[Recipe]:
    """
    Find recipes that use at least `min_match` of the available ingredients.
    Does a case-insensitive substring match against each ingredient string.
    """
    if not available_ingredients:
        return []

    recipes = db.query(Recipe).limit(200).all()
    scored = []

    for recipe in recipes:
        match_count = 0
        for user_ing in available_ingredients:
            user_ing_lower = user_ing.lower().strip()
            for recipe_ing in recipe.ingredients:
                if user_ing_lower in recipe_ing.lower() or recipe_ing.lower() in user_ing_lower:
                    match_count += 1
                    break  # Count each user ingredient only once

        if match_count >= min_match:
            scored.append((match_count, recipe))

    # Sort by number of matching ingredients (most matches first)
    scored.sort(key=lambda x: x[0], reverse=True)
    return [recipe for _, recipe in scored[:limit]]


# ─── User Ingredient CRUD ────────────────────────────────────

def get_user_ingredients(db: Session) -> list[UserIngredient]:
    """Get all ingredients the user has on hand."""
    return db.query(UserIngredient).order_by(UserIngredient.name).all()


def add_user_ingredient(db: Session, data: UserIngredientCreate) -> UserIngredient:
    """Add an ingredient to the user's pantry. Updates quantity if already exists."""
    existing = db.query(UserIngredient).filter(
        UserIngredient.name.ilike(data.name)
    ).first()
    if existing:
        existing.quantity = data.quantity
        db.commit()
        db.refresh(existing)
        return existing
    db_ingredient = UserIngredient(name=data.name.lower(), quantity=data.quantity)
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient


def remove_user_ingredient(db: Session, ingredient_id: int) -> bool:
    """Remove an ingredient from the user's pantry."""
    db_item = db.query(UserIngredient).filter(UserIngredient.id == ingredient_id).first()
    if not db_item:
        return False
    db.delete(db_item)
    db.commit()
    return True


def get_user_ingredient_names(db: Session) -> list[str]:
    """Get just the names of user ingredients (for agent context)."""
    return [ing.name for ing in get_user_ingredients(db)]


# ─── Meal Plan CRUD ──────────────────────────────────────────

def get_meal_plans(db: Session) -> list[MealPlan]:
    """Get all meal plans, most recent first."""
    return db.query(MealPlan).order_by(MealPlan.created_at.desc()).all()


def get_meal_plan(db: Session, plan_id: int) -> MealPlan | None:
    """Get a specific meal plan with its entries and recipes."""
    return (
        db.query(MealPlan)
        .filter(MealPlan.id == plan_id)
        .first()
    )


def create_meal_plan(db: Session, data: MealPlanCreate) -> MealPlan:
    """Create a new empty meal plan."""
    plan = MealPlan(name=data.name, week_start_date=data.week_start_date)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def add_meal_plan_entry(db: Session, plan_id: int, recipe_id: int, day: DayOfWeek, meal_type: MealType) -> MealPlanEntry | None:
    """
    Add a recipe to a meal plan slot.
    If the slot already exists, it replaces the recipe.
    """
    # Check if this day+meal_type slot already exists
    existing = db.query(MealPlanEntry).filter(
        MealPlanEntry.plan_id == plan_id,
        MealPlanEntry.day == day,
        MealPlanEntry.meal_type == meal_type,
    ).first()

    if existing:
        existing.recipe_id = recipe_id
        db.commit()
        db.refresh(existing)
        return existing

    entry = MealPlanEntry(plan_id=plan_id, recipe_id=recipe_id, day=day, meal_type=meal_type)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def remove_meal_plan_entry(db: Session, entry_id: int) -> bool:
    """Remove a meal plan entry."""
    entry = db.query(MealPlanEntry).filter(MealPlanEntry.id == entry_id).first()
    if not entry:
        return False
    db.delete(entry)
    db.commit()
    return True


def get_weekly_nutrition(db: Session, plan_id: int) -> dict:
    """
    Calculate total and daily nutrition for a meal plan.
    Returns {total_calories, total_protein, total_fat, total_carbs, daily_breakdown}.
    """
    entries = (
        db.query(MealPlanEntry)
        .filter(MealPlanEntry.plan_id == plan_id)
        .all()
    )

    daily = {}
    totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}

    for entry in entries:
        recipe = db.query(Recipe).filter(Recipe.id == entry.recipe_id).first()
        if not recipe:
            continue

        day_key = entry.day.value
        if day_key not in daily:
            daily[day_key] = {"day": day_key, "calories": 0, "protein": 0, "fat": 0, "carbs": 0}

        daily[day_key]["calories"] += recipe.calories
        daily[day_key]["protein"] += recipe.protein
        daily[day_key]["fat"] += recipe.fat
        daily[day_key]["carbs"] += recipe.carbs

        totals["calories"] += recipe.calories
        totals["protein"] += recipe.protein
        totals["fat"] += recipe.fat
        totals["carbs"] += recipe.carbs

    return {
        "total_calories": round(totals["calories"], 1),
        "total_protein": round(totals["protein"], 1),
        "total_fat": round(totals["fat"], 1),
        "total_carbs": round(totals["carbs"], 1),
        "daily_breakdown": list(daily.values()),
    }


# ─── Shopping List CRUD ──────────────────────────────────────

def get_shopping_list(db: Session, purchased_only: bool = False) -> list[ShoppingListItem]:
    """Get the shopping list, optionally filtered to purchased items."""
    query = db.query(ShoppingListItem).order_by(ShoppingListItem.category, ShoppingListItem.name)
    if purchased_only:
        query = query.filter(ShoppingListItem.purchased == 1)
    return query.all()


def add_shopping_item(db: Session, data: ShoppingListItemCreate) -> ShoppingListItem:
    """
    Add an item to the shopping list.
    If an item with the same name exists, quantities are aggregated.
    """
    existing = db.query(ShoppingListItem).filter(
        ShoppingListItem.name.ilike(data.name)
    ).first()

    if existing:
        # Simple aggregation: append quantities (e.g. "200g" + "200g" → "400g")
        existing.quantity = _combine_quantities(existing.quantity, data.quantity)
        db.commit()
        db.refresh(existing)
        return existing

    item = ShoppingListItem(name=data.name, quantity=data.quantity, category=data.category)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_shopping_item(db: Session, item_id: int, data: ShoppingListItemUpdate) -> ShoppingListItem | None:
    """Update a shopping list item."""
    item = db.query(ShoppingListItem).filter(ShoppingListItem.id == item_id).first()
    if not item:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_shopping_item(db: Session, item_id: int) -> bool:
    """Remove an item from the shopping list."""
    item = db.query(ShoppingListItem).filter(ShoppingListItem.id == item_id).first()
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


def generate_shopping_list_from_plan(db: Session, plan_id: int) -> list[ShoppingListItem]:
    """
    Generate a shopping list from a meal plan.
    Compares recipe ingredients against user's available ingredients
    and adds only missing items.
    """
    user_ing_names = set(ing.name.lower() for ing in get_user_ingredients(db))

    entries = (
        db.query(MealPlanEntry)
        .filter(MealPlanEntry.plan_id == plan_id)
        .all()
    )

    # Collect all needed ingredients with quantities
    needed = {}  # {ingredient_name: [quantities]}
    for entry in entries:
        recipe = db.query(Recipe).filter(Recipe.id == entry.recipe_id).first()
        if not recipe:
            continue
        for ing_str in recipe.ingredients:
            # Parse quantity + name from "200g chicken breast"
            parts = ing_str.strip().split(None, 1)
            if len(parts) == 2:
                qty, name = parts
            else:
                qty, name = "", parts[0]

            name_lower = name.lower()
            # Skip if user already has this ingredient
            if name_lower in user_ing_names:
                continue

            if name_lower not in needed:
                needed[name_lower] = []
            needed[name_lower].append(qty)

    # Clear existing shopping list and add new items
    db.query(ShoppingListItem).delete()
    db.commit()

    items = []
    for name, quantities in needed.items():
        combined_qty = _combine_quantities_list(quantities)
        # Try to categorize based on common patterns
        category = _categorize_ingredient(name)
        item = add_shopping_item(db, ShoppingListItemCreate(
            name=name.title(),
            quantity=combined_qty,
            category=category,
        ))
        items.append(item)

    return items


def _combine_quantities(qty1: str, qty2: str) -> str:
    """
    Combine two quantity strings.
    If both are numeric with the same unit, adds them.
    Otherwise concatenates.
    """
    if not qty1:
        return qty2
    if not qty2:
        return qty1

    # Try to extract numbers and units
    import re
    match1 = re.match(r"([\d.]+)\s*(.*)", qty1)
    match2 = re.match(r"([\d.]+)\s*(.*)", qty2)

    if match1 and match2:
        num1, unit1 = float(match1.group(1)), match1.group(2).strip()
        num2, unit2 = float(match2.group(1)), match2.group(2).strip()
        if unit1.lower() == unit2.lower():
            total = num1 + num2
            # Show as int if whole number
            if total == int(total):
                return f"{int(total)}{unit1}"
            return f"{total}{unit1}"

    return f"{qty1} + {qty2}"


def _combine_quantities_list(quantities: list[str]) -> str:
    """Combine a list of quantity strings."""
    if not quantities:
        return ""
    result = quantities[0]
    for q in quantities[1:]:
        result = _combine_quantities(result, q)
    return result


def _categorize_ingredient(name: str) -> str:
    """Heuristic categorization of ingredients for shopping list organization."""
    name_lower = name.lower()
    categories = {
        "Produce": ["tomato", "onion", "garlic", "pepper", "lettuce", "spinach", "broccoli",
                     "carrot", "celery", "mushroom", "avocado", "lemon", "lime", "ginger",
                     "basil", "cilantro", "parsley", "cabbage", "zucchini", "cucumber"],
        "Meat": ["chicken", "beef", "pork", "turkey", "bacon", "sausage", "lamb", "steak",
                  "breast", "thigh", "ground"],
        "Seafood": ["salmon", "shrimp", "tuna", "cod", "tilapia", "fish", "crab", "lobster"],
        "Dairy": ["milk", "cheese", "butter", "cream", "yogurt", "egg", "parmesan", "mozzarella"],
        "Grains": ["rice", "pasta", "bread", "oat", "quinoa", "noodle", "tortilla", "flour",
                    "couscous"],
        "Pantry": ["oil", "salt", "pepper", "sugar", "vinegar", "soy sauce", "honey",
                    "spice", "sauce", "broth", "stock"],
    }
    for category, keywords in categories.items():
        if any(kw in name_lower for kw in keywords):
            return category
    return "Other"


# ─── User Preference CRUD ────────────────────────────────────

def get_user_preference(db: Session) -> UserPreference | None:
    """Get the user's preferences (single row, id=1)."""
    return db.query(UserPreference).filter(UserPreference.id == 1).first()


def create_or_update_preference(db: Session, data: UserPreferenceCreate) -> UserPreference:
    """Create or update the user's preferences."""
    pref = get_user_preference(db)
    if pref:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(pref, key, value)
        db.commit()
        db.refresh(pref)
        return pref
    pref = UserPreference(id=1, **data.model_dump())
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref


def generate_plan_from_preferences(db: Session, plan_name: str = "Auto-Generated Weekly Plan") -> MealPlan:
    """
    Generate a weekly meal plan using user preferences.
    Reused by both the meal_plans route and the agent.
    """
    import random

    prefs = get_user_preference(db)
    diet_tag = prefs.diet_type.value if prefs and prefs.diet_type.value != "none" else None
    max_calories = prefs.daily_calorie_target // 3 if prefs else 700

    all_recipes = get_recipes(db, limit=200, max_calories=max_calories, diet_type=diet_tag)
    if not all_recipes:
        all_recipes = get_recipes(db, limit=200)
    if not all_recipes:
        raise ValueError("No recipes available to generate a plan")

    breakfast_recipes = [r for r in all_recipes if "breakfast" in r.name.lower() or "breakfast" in [t.lower() for t in r.tags]]
    lunch_recipes = [r for r in all_recipes if "lunch" in r.name.lower() or "salad" in r.name.lower() or "soup" in r.name.lower()]
    dinner_recipes = [r for r in all_recipes if "dinner" in r.name.lower()]

    if not breakfast_recipes:
        breakfast_recipes = all_recipes
    if not lunch_recipes:
        lunch_recipes = all_recipes
    if not dinner_recipes:
        dinner_recipes = all_recipes

    plan = create_meal_plan(db, MealPlanCreate(name=plan_name))
    days = list(DayOfWeek)
    used_recipes: set[int] = set()

    for day in days:
        bf_candidates = [r for r in breakfast_recipes if r.id not in used_recipes] or breakfast_recipes
        bf = random.choice(bf_candidates)
        add_meal_plan_entry(db, plan.id, bf.id, day, MealType.BREAKFAST)
        used_recipes.add(bf.id)

        ln_candidates = [r for r in lunch_recipes if r.id not in used_recipes] or lunch_recipes
        ln = random.choice(ln_candidates)
        add_meal_plan_entry(db, plan.id, ln.id, day, MealType.LUNCH)
        used_recipes.add(ln.id)

        dn_candidates = [r for r in dinner_recipes if r.id not in used_recipes] or dinner_recipes
        dn = random.choice(dn_candidates)
        add_meal_plan_entry(db, plan.id, dn.id, day, MealType.DINNER)
        used_recipes.add(dn.id)

    db.commit()
    return plan
