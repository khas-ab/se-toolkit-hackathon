"""
LLM-powered agent with function calling.
Supports OpenAI, Qwen (via OpenAI-compatible API), and a local fallback.

The agent receives a natural language query, decides which tool to call,
executes the tool, and returns a natural language response with structured data.

Available tools:
  - search_recipes: Find recipes by ingredients, calories, tags
  - get_recipe_details: Get full details of a specific recipe
  - suggest_substitutions: Suggest ingredient substitutions
  - generate_meal_plan: Auto-generate a weekly meal plan
  - add_to_shopping_list: Add items to the shopping list
  - get_meal_plan: Query what's planned for a specific day
  - add_ingredient: Add an ingredient to user's pantry

When no LLM API key is available (or the API is unreachable), the agent falls
back to local intent detection + tool execution — the same function-calling
pattern, just with rule-based routing instead of an LLM.
"""
import os
import json
import re
from typing import Optional
from sqlalchemy.orm import Session
from openai import OpenAI

import crud
from schemas import (
    RecipeResponse, ShoppingListItemCreate, UserIngredientCreate,
    MealPlanResponse,
)
from models import DayOfWeek, MealType


# ─── LLM Client Setup ────────────────────────────────────────

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")

client = None
MODEL_NAME = "none"

if LLM_PROVIDER == "qwen" and QWEN_API_KEY and not QWEN_API_KEY.startswith("secret-"):
    client = OpenAI(
        api_key=QWEN_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    MODEL_NAME = "qwen-plus"
elif OPENAI_API_KEY and not OPENAI_API_KEY.startswith("sk-your"):
    client = OpenAI(api_key=OPENAI_API_KEY)
    MODEL_NAME = "gpt-4o-mini"


# ─── Tool Definitions (for documentation + LLM function calling) ──

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_recipes",
            "description": "Search for recipes based on ingredients the user has, calorie limits, prep time, diet type, or tags.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ingredients": {"type": "array", "items": {"type": "string"}, "description": "List of ingredients the user has"},
                    "max_calories": {"type": "integer", "description": "Maximum calories per recipe"},
                    "max_prep_time": {"type": "integer", "description": "Maximum prep time in minutes"},
                    "diet_type": {"type": "string", "enum": ["vegan", "vegetarian", "keto", "paleo", "low_carb", "mediterranean"], "description": "Filter by diet type"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Additional tags to filter by"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recipe_details",
            "description": "Get full details of a specific recipe including ingredients, steps, and macros.",
            "parameters": {
                "type": "object",
                "properties": {"recipe_id": {"type": "integer", "description": "The ID of the recipe"}},
                "required": ["recipe_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_substitutions",
            "description": "Suggest ingredient substitutions when the user doesn't have a required ingredient.",
            "parameters": {
                "type": "object",
                "properties": {"missing_ingredient": {"type": "string", "description": "The ingredient to substitute"}},
                "required": ["missing_ingredient"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_meal_plan",
            "description": "Generate a complete 7-day meal plan based on user preferences.",
            "parameters": {
                "type": "object",
                "properties": {"plan_name": {"type": "string", "description": "Name for the meal plan"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_shopping_list",
            "description": "Add items to the user's shopping list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "quantity": {"type": "string"},
                                "category": {"type": "string"},
                            },
                            "required": ["name"],
                        },
                    },
                },
                "required": ["items"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_meal_plan",
            "description": "Query what the user has planned for a specific day or the current meal plan.",
            "parameters": {
                "type": "object",
                "properties": {"day": {"type": "string", "enum": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_ingredient",
            "description": "Add an ingredient to the user's pantry/available ingredients.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Ingredient name"},
                    "quantity": {"type": "string", "description": "Quantity"},
                },
                "required": ["name"],
            },
        },
    },
]

SYSTEM_PROMPT = """\
You are a helpful diet and recipe planning assistant. You help users find recipes, \
plan their meals, manage their shopping list, and suggest ingredient substitutions. \
Be friendly, concise, and informative. When showing recipes, mention calories and protein.\
"""

SUBSTITUTIONS = {
    "coconut milk": ["heavy cream", "oat milk", "almond milk", "cashew cream", "whole milk"],
    "almond milk": ["oat milk", "coconut milk", "soy milk", "whole milk", "cashew milk"],
    "butter": ["coconut oil", "olive oil", "ghee", "applesauce (for baking)", "avocado"],
    "egg": ["flax egg (1 tbsp ground flax + 3 tbsp water)", "chia egg", "applesauce", "mashed banana"],
    "wheat flour": ["almond flour", "oat flour", "coconut flour", "rice flour", "all-purpose gluten-free flour"],
    "soy sauce": ["coconut aminos", "tamari", "liquid aminos", "worcestershire sauce"],
    "heavy cream": ["coconut cream", "cashew cream", "silken tofu blended", "whole milk + butter"],
    "chicken breast": ["chicken thigh", "turkey breast", "tofu", "tempeh"],
    "ground beef": ["ground turkey", "ground chicken", "lentils", "mushrooms", "plant-based ground meat"],
    "rice": ["quinoa", "cauliflower rice", "couscous", "bulgur wheat"],
    "pasta": ["zucchini noodles", "spaghetti squash", "shirataki noodles", "lentil pasta"],
    "sugar": ["honey", "maple syrup", "stevia", "monk fruit sweetener", "coconut sugar"],
    "milk": ["oat milk", "almond milk", "soy milk", "coconut milk"],
    "parmesan": ["nutritional yeast", "pecorino romano", "asiago", "vegan parmesan"],
    "bread": ["lettuce wraps", "rice cakes", "cloud bread", "gluten-free bread"],
    "cheese": ["nutritional yeast", "vegan cheese", "cashew cheese", "tofu ricotta"],
}


# ─── Tool Execution Functions ────────────────────────────────

def _execute_search_recipes(db: Session, args: dict) -> list[dict]:
    """Execute the search_recipes tool."""
    if args.get("ingredients"):
        recipes = crud.search_recipes_by_ingredients(
            db, available_ingredients=args.get("ingredients", []),
            min_match=1, limit=args.get("limit", 10),
        )
    else:
        # No ingredients — just use filters
        recipes = crud.get_recipes(db, limit=args.get("limit", 50))

    if args.get("max_calories"):
        recipes = [r for r in recipes if r.calories <= args["max_calories"]]
    if args.get("max_prep_time"):
        recipes = [r for r in recipes if r.prep_time <= args["max_prep_time"]]
    if args.get("diet_type"):
        diet_tag = args["diet_type"].lower()
        recipes = [r for r in recipes if diet_tag in [t.lower() for t in r.tags]]
    if args.get("tags"):
        for tag in args["tags"]:
            recipes = [r for r in recipes if tag.lower() in [t.lower() for t in r.tags]]
    return [_recipe_to_dict(r) for r in recipes[:10]]


def _execute_get_recipe_details(db: Session, args: dict) -> dict | None:
    recipe = crud.get_recipe(db, args["recipe_id"])
    return _recipe_to_dict(recipe) if recipe else None


def _execute_suggest_substitutions(db: Session, args: dict) -> dict:
    ingredient = args["missing_ingredient"].lower().strip()
    substitutions = SUBSTITUTIONS.get(ingredient, [])
    all_recipes = crud.get_recipes(db, limit=100)
    related = set()
    for recipe in all_recipes:
        for ing in recipe.ingredients:
            if ingredient in ing.lower():
                for other_ing in recipe.ingredients:
                    if ingredient not in other_ing.lower():
                        related.add(other_ing)
    return {
        "missing_ingredient": ingredient,
        "substitutions": substitutions if substitutions else list(related)[:5],
        "message": (
            f"If you don't have {ingredient}, you can try these alternatives."
            if substitutions
            else f"I couldn't find direct substitutions for {ingredient}, but these ingredients often appear in similar recipes."
        ),
    }


def _execute_generate_meal_plan(db: Session, args: dict) -> dict:
    plan_name = args.get("plan_name", "AI-Generated Weekly Plan")
    plan = crud.generate_plan_from_preferences(db, plan_name=plan_name)
    return _meal_plan_to_dict(plan)


def _execute_add_to_shopping_list(db: Session, args: dict) -> list[dict]:
    items = []
    for item_data in args.get("items", []):
        item = crud.add_shopping_item(
            db, ShoppingListItemCreate(
                name=item_data["name"],
                quantity=item_data.get("quantity", ""),
                category=item_data.get("category", ""),
            ),
        )
        items.append({"id": item.id, "name": item.name, "quantity": item.quantity, "category": item.category})
    return items


def _execute_get_meal_plan(db: Session, args: dict) -> dict:
    plans = crud.get_meal_plans(db)
    if not plans:
        return {"message": "You don't have any meal plans yet. Would you like me to generate one?"}
    plan = plans[0]
    result = {"plan_name": plan.name, "entries": {}}
    day_filter = args.get("day")
    if day_filter:
        day_entries = [e for e in plan.entries if e.day.value == day_filter.lower()]
        for entry in day_entries:
            recipe = crud.get_recipe(db, entry.recipe_id)
            if recipe:
                result["entries"][entry.meal_type.value] = _recipe_to_dict(recipe)
        if not result["entries"]:
            result["message"] = f"No meals planned for {day_filter.capitalize()} yet."
    else:
        for entry in plan.entries:
            day = entry.day.value
            if day not in result["entries"]:
                result["entries"][day] = {}
            recipe = crud.get_recipe(db, entry.recipe_id)
            if recipe:
                result["entries"][day][entry.meal_type.value] = _recipe_to_dict(recipe)
    return result


def _execute_add_ingredient(db: Session, args: dict) -> dict:
    ingredient = crud.add_user_ingredient(
        db, UserIngredientCreate(name=args["name"], quantity=args.get("quantity", "")),
    )
    return {"id": ingredient.id, "name": ingredient.name, "quantity": ingredient.quantity, "message": f"Added '{ingredient.name}' to your pantry."}


TOOL_EXECUTORS = {
    "search_recipes": _execute_search_recipes,
    "get_recipe_details": _execute_get_recipe_details,
    "suggest_substitutions": _execute_suggest_substitutions,
    "generate_meal_plan": _execute_generate_meal_plan,
    "add_to_shopping_list": _execute_add_to_shopping_list,
    "get_meal_plan": _execute_get_meal_plan,
    "add_ingredient": _execute_add_ingredient,
}


# ─── Local Intent Detection (fallback when no LLM API is available) ──

def _detect_intent(query: str) -> tuple[str, dict]:
    """
    Detect which tool to call based on the user's query.
    Returns (tool_name, tool_args).

    This is the local fallback when no LLM API key is configured.
    It uses keyword and pattern matching to route to the right tool.
    """
    q = query.lower().strip()

    # 1. Add ingredient: "add X to my pantry/ingredients", "add X to my shopping list"
    # Note: "I have X" is NOT used here — it's too ambiguous and conflicts with recipe queries
    add_ing_patterns = [
        r"add\s+(.+?)\s+(to\s+(my\s+)?(pantry|ingredients?))",
    ]
    for pattern in add_ing_patterns:
        m = re.search(pattern, q)
        if m:
            text = m.group(1)
            text = re.sub(r"\s+to\s+(my\s+)?(pantry|ingredients?)\s*$", "", text)
            items = re.split(r",\s*|\s+and\s+", text)
            items = [i.strip() for i in items if i.strip()]
            if items:
                return "add_ingredient", {"name": items[0], "quantity": ""}

    # 2. Substitution: "no X", "what can I use instead of X", "substitute X"
    sub_patterns = [
        r"no\s+(\w[\w\s]*?)(\?|$|,|\s+what|\s+can|\s+use|\s+instead)",
        r"(instead\s+of|substitute|substitution|alternative\s+(to|for)|use\s+(instead|in\s+place))\s+(\w[\w\s]*?)(\?|$)",
        r"what\s+can\s+i\s+use\s+(instead|in\s+place|for)\s+(\w[\w\s]*?)(\?|$)",
    ]
    for pattern in sub_patterns:
        m = re.search(pattern, q)
        if m:
            # Find the ingredient name from whichever group matched
            for g in m.groups():
                if g and isinstance(g, str) and len(g) > 1:
                    return "suggest_substitutions", {"missing_ingredient": g.strip().rstrip("?")}

    # 3. Shopping list: "add X to shopping list"
    shop_m = re.search(r"add\s+(.+?)\s+to\s+(my\s+)?shopping\s+list", q)
    if shop_m:
        items_text = shop_m.group(1)
        items = [i.strip() for i in re.split(r",\s*|\s+and\s+", items_text) if i.strip()]
        return "add_to_shopping_list", {"items": [{"name": i.title()} for i in items]}

    # 4. Meal plan query: "what did I plan for X", "what's for X", "show my meal plan"
    day_map = {
        "monday": "monday", "mon": "monday",
        "tuesday": "tuesday", "tue": "tuesday", "tues": "tuesday",
        "wednesday": "wednesday", "wed": "wednesday",
        "thursday": "thursday", "thu": "thursday", "thur": "thursday",
        "friday": "friday", "fri": "friday",
        "saturday": "saturday", "sat": "saturday",
        "sunday": "sunday", "sun": "sunday",
    }

    # Check for day-specific query: "for wednesday", "for monday"
    day_in_query = None
    for day_name in day_map:
        if f"for {day_name}" in q or f"on {day_name}" in q:
            day_in_query = day_map[day_name]
            break

    plan_query_patterns = [
        r"what\s+(did\s+i\s+plan|do\s+i\s+have|is\s+planned)",
        r"show\s+(my|the)\s+meal\s+plan",
        r"what'?s\s+(my|the)\s+plan",
        r"what'?s\s+for\s+\w+",
    ]
    for pattern in plan_query_patterns:
        if re.search(pattern, q):
            return "get_meal_plan", {"day": day_in_query} if day_in_query else {}

    # 5. Generate meal plan: "plan my week", "generate a meal plan", "plan my meals"
    gen_plan_patterns = [
        r"plan\s+(my\s+)?(week|weekly)",
        r"generate\s+(a\s+)?(meal\s+plan|weekly\s+plan)",
        r"plan\s+(my\s+)?meals?\s+(for\s+the\s+)?(week)?",
    ]
    for pattern in gen_plan_patterns:
        if re.search(pattern, q):
            plan_name = "AI-Generated Weekly Plan"
            # Try to extract a custom name
            name_m = re.search(r"(?:plan|generate)\s+(?:my\s+)?(?:week|meals?)\s+(?:for\s+)?(\w[\w\s]*?)(?:\s*$)", q)
            if name_m:
                plan_name = name_m.group(1).strip().title() + " Plan"
            return "generate_meal_plan", {"plan_name": plan_name}

    # 6. Search recipes (default for ingredient mentions or "what can I cook/make/eat")
    # Look for "what can I cook/make/eat with X" or just a list of ingredients
    cook_patterns = [
        r"(?:what\s+can\s+i\s+(?:cook|make|prepare|eat|have)|recipe|ideas?|suggestions?)(?:\s+(?:with|using|from|for))?\s*(.+)?",
        r"(?:cook|make|prepare|eat)\s+(?:with|using|for)\s+(.+)",
    ]
    # Words that should NOT be treated as ingredients
    stop_words = {"i", "me", "my", "the", "a", "an", "is", "are", "was", "were",
                  "can", "could", "would", "should", "will", "do", "does", "did",
                  "have", "has", "had", "want", "need", "like", "please", "help",
                  "to", "for", "with", "from", "in", "on", "at", "by", "of", "and",
                  "or", "but", "not", "no", "what", "which", "who", "how", "when",
                  "where", "why", "this", "that", "these", "those", "it", "its",
                  "eat", "eating", "eaten", "food", "something", "anything"}
    non_ingredient_words = {
        # Meal types
        "breakfast", "lunch", "dinner", "snack", "snacks", "meal", "meals",
        # Diet types
        "keto", "vegan", "vegetarian", "paleo", "mediterranean",
        # Nutrition terms
        "high", "protein", "low", "carb", "carbs", "fat", "calorie", "calories", "cal",
        # Cooking styles
        "quick", "easy", "simple", "healthy", "weight", "loss",
        # Numbers
        "500", "400", "300", "200", "100", "600", "700", "800", "900",
        # Other
        "under", "over", "less", "than", "more",
    }

    ingredients = []
    for pattern in cook_patterns:
        m = re.search(pattern, q)
        if m and m.group(1):
            text = m.group(1).strip().rstrip("?")
            # Strip meal type references: "lunch", "for lunch", "dinner", etc.
            text = re.sub(r"\b(for\s+)?(lunch|dinner|breakfast|snack)\b\s*", " ", text).strip()
            # Strip calorie references: "under 500 cal", "under 500 calories"
            text = re.sub(r"\bunder\s+\d+\s*(?:cal|calories|kcal)\b\s*", " ", text).strip()
            # Strip other non-ingredient phrases
            text = re.sub(r"\b(high[\s-]?protein|low[\s-]?carb|low[\s-]?fat)\b\s*", " ", text).strip()
            ingredients = [i.strip() for i in re.split(r",\s*|\s+and\s+", text) if i.strip()]
            # Remove empty or stop-word-only entries
            ingredients = [i for i in ingredients if i and i not in stop_words and i not in non_ingredient_words]
            break

    if ingredients:
        args: dict = {"ingredients": ingredients}
        # Check for calorie constraint
        cal_m = re.search(r"under\s+(\d+)\s*(?:cal|calories|kcal)", q)
        if cal_m:
            args["max_calories"] = int(cal_m.group(1))
        # Check for diet type
        for diet in ["keto", "vegan", "vegetarian", "paleo", "low_carb", "mediterranean"]:
            if diet.replace("_", " ") in q or diet.replace("_", "-") in q:
                args["diet_type"] = diet
                break
        # Check for protein tag
        if "high-protein" in q or "high protein" in q:
            args["tags"] = ["high-protein"]
        # Check for prep time
        time_m = re.search(r"(?:under|less\s+than|in)\s+(\d+)\s*(?:min|minutes?)", q)
        if time_m:
            args["max_prep_time"] = int(time_m.group(1))
        # Detect meal type as a tag: "for lunch", "for dinner"
        for meal_tag in ["lunch", "dinner", "breakfast", "snack"]:
            if f"for {meal_tag}" in q:
                args.setdefault("tags", []).append(meal_tag)
                break
        return "search_recipes", args

    # No specific ingredients, but check for filter-only queries like "high-protein dinner under 500 cal"
    filter_args: dict = {}
    cal_m = re.search(r"under\s+(\d+)\s*(?:cal|calories|kcal)", q)
    if cal_m:
        filter_args["max_calories"] = int(cal_m.group(1))
    for diet in ["keto", "vegan", "vegetarian", "paleo", "low_carb", "mediterranean"]:
        if diet.replace("_", " ") in q or diet.replace("_", "-") in q:
            filter_args["diet_type"] = diet
            break
    if "high-protein" in q or "high protein" in q:
        filter_args["tags"] = ["high-protein"]
    time_m = re.search(r"(?:under|less\s+than|in)\s+(\d+)\s*(?:min|minutes?)", q)
    if time_m:
        filter_args["max_prep_time"] = int(time_m.group(1))
    # Detect meal type as a tag: "for lunch", "for dinner", "for breakfast"
    for meal_tag in ["lunch", "dinner", "breakfast", "snack"]:
        if f"for {meal_tag}" in q or f"as {meal_tag}" in q:
            filter_args.setdefault("tags", []).append(meal_tag)
            break

    if filter_args:
        return "search_recipes", filter_args

    # Fallback: general search with whatever words we have
    words = re.findall(r"[a-z]{3,}", q)
    words = [w for w in words if w not in stop_words and w not in non_ingredient_words]
    if words:
        return "search_recipes", {"ingredients": words[:5]}

    return "search_recipes", {"ingredients": []}


def _generate_response(tool_name: str, tool_result, query: str) -> str:
    """Generate a natural language response for the tool result (local fallback)."""
    if tool_name == "search_recipes":
        recipes = tool_result if isinstance(tool_result, list) else []
        if not recipes:
            return "I couldn't find any recipes matching those ingredients. Try adding more ingredients to your pantry, or adjust your filters!"
        lines = [f"I found {len(recipes)} recipe(s) you might like:"]
        for r in recipes[:5]:
            lines.append(f"\n🍽️ **{r['name']}** ({r.get('cuisine', '')})")
            lines.append(f"   🔥 {r['calories']} cal · 🥩 {r['protein']}g protein · ⏱️ {r['prep_time']}min prep")
            if r.get("tags"):
                lines.append(f"   🏷️ {', '.join(r['tags'][:3])}")
        return "\n".join(lines)

    elif tool_name == "get_recipe_details":
        r = tool_result
        if not r:
            return "I couldn't find that recipe. Try a different one!"
        lines = [f"🍽️ **{r['name']}** ({r.get('cuisine', '')})"]
        lines.append(f"\n📝 {r.get('description', '')}")
        lines.append(f"\n🔥 {r['calories']} cal · 🥩 {r['protein']}g protein · 🧈 {r['fat']}g fat · 🌾 {r['carbs']}g carbs")
        lines.append(f"\n⏱️ Prep: {r['prep_time']}min · Cook: {r['cook_time']}min · Servings: {r.get('servings', 1)}")
        lines.append(f"\n📦 Ingredients:")
        for ing in r.get("ingredients", []):
            lines.append(f"  • {ing}")
        return "\n".join(lines)

    elif tool_name == "suggest_substitutions":
        result = tool_result
        lines = [result.get("message", "")]
        if result.get("substitutions"):
            lines.append("\nTry these alternatives:")
            for sub in result["substitutions"]:
                lines.append(f"  • {sub}")
        return "\n".join(lines)

    elif tool_name == "generate_meal_plan":
        result = tool_result
        return f"✅ I've generated a new meal plan: **{result.get('name', 'Weekly Plan')}** with {result.get('entry_count', 0)} meal slots (7 days × breakfast, lunch, dinner). Check the Recipe Browser tab to see the full calendar!"

    elif tool_name == "add_to_shopping_list":
        items = tool_result if isinstance(tool_result, list) else []
        names = [i["name"] for i in items]
        return f"✅ Added {len(items)} item(s) to your shopping list: {', '.join(names)}"

    elif tool_name == "get_meal_plan":
        result = tool_result
        if result.get("message"):
            return result["message"]
        entries = result.get("entries", {})
        if not entries:
            return "Your meal plan is empty. Would you like me to generate one?"
        emoji = {"breakfast": "🌅", "lunch": "☀️", "dinner": "🌙", "snack": "🍪"}
        lines = [f"📅 **{result.get('plan_name', 'Your Meal Plan')}**"]

        # Detect structure: day-filtered = {meal_type: recipe}, full = {day: {meal_type: recipe}}
        first_val = next(iter(entries.values()), None)
        if first_val and isinstance(first_val, dict) and "name" in first_val:
            # Day-filtered: {meal_type: recipe_dict}
            for meal_type, recipe in entries.items():
                lines.append(f"  {emoji.get(meal_type, '•')} {meal_type.capitalize()}: {recipe['name']} ({recipe['calories']} cal)")
        else:
            # Full plan: {day: {meal_type: recipe_dict}}
            for day, meals in entries.items():
                lines.append(f"\n**{day.capitalize()}:**")
                for meal_type, recipe in meals.items():
                    lines.append(f"  {emoji.get(meal_type, '•')} {meal_type.capitalize()}: {recipe['name']} ({recipe['calories']} cal)")
        return "\n".join(lines)

    elif tool_name == "add_ingredient":
        result = tool_result
        return f"✅ Added '{result.get('name', '')}' to your pantry!"

    return "I processed your request. Check the results above!"


# ─── Main Agent Function ─────────────────────────────────────

def process_query(db: Session, user_query: str) -> dict:
    """
    Process a natural language query through the agent.

    Flow:
    1. If LLM client is available, use function calling
    2. Otherwise, fall back to local intent detection + tool execution
    3. Return natural language response + structured data
    """
    if client is not None:
        return _process_with_llm(db, user_query)
    else:
        return _process_locally(db, user_query)


def _process_with_llm(db: Session, user_query: str) -> dict:
    """Process query using LLM function calling."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME, messages=messages,
            tools=TOOLS, tool_choice="auto", temperature=0.3,
        )
        choice = response.choices[0]
        message = choice.message

        if message.tool_calls:
            tool_call = message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            executor = TOOL_EXECUTORS.get(tool_name)
            tool_result = executor(db, tool_args) if executor else {"error": f"Unknown tool: {tool_name}"}

            messages.append(message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result, default=str),
            })
            final_response = client.chat.completions.create(
                model=MODEL_NAME, messages=messages, temperature=0.3,
            )
            response_text = final_response.choices[0].message.content or ""
            return {"response": response_text, "data": _extract_structured_data(tool_name, tool_result)}
        else:
            return {"response": message.content or "I'm not sure how to help with that.", "data": None}
    except Exception as e:
        # If LLM call fails, fall back to local processing
        return _process_locally(db, user_query)


def _process_locally(db: Session, user_query: str) -> dict:
    """Process query using local intent detection (no LLM API needed)."""
    tool_name, tool_args = _detect_intent(user_query)
    executor = TOOL_EXECUTORS.get(tool_name)
    if executor:
        tool_result = executor(db, tool_args)
    else:
        tool_result = {"error": f"Unknown tool: {tool_name}"}

    response_text = _generate_response(tool_name, tool_result, user_query)
    structured_data = _extract_structured_data(tool_name, tool_result)

    return {"response": response_text, "data": structured_data}


# ─── Helper Functions ────────────────────────────────────────

def _recipe_to_dict(recipe) -> dict:
    return {
        "id": recipe.id, "name": recipe.name, "description": recipe.description,
        "ingredients": recipe.ingredients, "steps": recipe.steps,
        "protein": recipe.protein, "fat": recipe.fat, "carbs": recipe.carbs,
        "calories": recipe.calories, "prep_time": recipe.prep_time,
        "cook_time": recipe.cook_time, "servings": recipe.servings,
        "tags": recipe.tags, "cuisine": recipe.cuisine, "image_url": recipe.image_url,
    }


def _meal_plan_to_dict(plan) -> dict:
    return {"id": plan.id, "name": plan.name, "week_start_date": plan.week_start_date, "entry_count": len(plan.entries)}


def _extract_structured_data(tool_name: str, tool_result) -> dict | None:
    if tool_name == "search_recipes" and isinstance(tool_result, list):
        return {"type": "recipes", "recipes": tool_result}
    elif tool_name == "get_recipe_details" and isinstance(tool_result, dict):
        return {"type": "recipe", "recipe": tool_result}
    elif tool_name == "suggest_substitutions" and isinstance(tool_result, dict):
        return {"type": "substitutions", **tool_result}
    elif tool_name == "generate_meal_plan" and isinstance(tool_result, dict):
        return {"type": "meal_plan", "meal_plan": tool_result}
    elif tool_name == "add_to_shopping_list" and isinstance(tool_result, list):
        return {"type": "shopping_list", "items": tool_result}
    elif tool_name == "get_meal_plan" and isinstance(tool_result, dict):
        return {"type": "meal_plan_info", **tool_result}
    elif tool_name == "add_ingredient" and isinstance(tool_result, dict):
        return {"type": "ingredient_added", **tool_result}
    return None
