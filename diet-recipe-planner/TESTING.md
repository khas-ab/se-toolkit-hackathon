# Testing Guide — Diet Recipe Planner

This document contains `curl` commands to test every API endpoint.

## Prerequisites

```bash
# Start the backend (via docker-compose or locally)
cd diet-recipe-planner
docker compose up -d backend

# Or run locally:
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Base URL: `http://localhost:8000`

---

## 1. Health Check

```bash
curl -s http://localhost:8000/health | python -m json.tool
```

Expected: `{"status": "ok", "version": "1.0.0", ...}`

---

## 2. Recipes

### List all recipes

```bash
curl -s http://localhost:8000/api/recipes | python -m json.tool | head -30
```

### Filter by max calories

```bash
curl -s "http://localhost:8000/api/recipes?max_calories=300" | python -m json.tool
```

### Filter by diet type (keto)

```bash
curl -s "http://localhost:8000/api/recipes?diet_type=keto" | python -m json.tool
```

### Search by name

```bash
curl -s "http://localhost:8000/api/recipes?search=chicken" | python -m json.tool
```

### Get a single recipe

```bash
curl -s http://localhost:8000/api/recipes/1 | python -m json.tool
```

### Create a recipe

```bash
curl -s -X POST http://localhost:8000/api/recipes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Recipe",
    "ingredients": ["1 cup flour", "2 eggs", "1/2 cup milk"],
    "steps": ["Mix ingredients", "Cook on pan"],
    "protein": 10,
    "fat": 8,
    "carbs": 40,
    "calories": 280,
    "prep_time": 10,
    "cook_time": 15,
    "tags": ["breakfast", "vegetarian"],
    "cuisine": "Test"
  }' | python -m json.tool
```

### Update a recipe

```bash
curl -s -X PUT http://localhost:8000/api/recipes/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Recipe Name"}' | python -m json.tool
```

### Delete a recipe

```bash
curl -s -X DELETE http://localhost:8000/api/recipes/1 -w "\nHTTP Status: %{http_code}\n"
```

---

## 3. Suggest Recipes

### Suggest by ingredients

```bash
curl -s -X POST http://localhost:8000/api/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": ["chicken", "rice", "broccoli"],
    "max_calories": 500,
    "limit": 5
  }' | python -m json.tool
```

### Suggest with diet filter

```bash
curl -s -X POST http://localhost:8000/api/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": ["eggs", "avocado"],
    "diet_type": "keto",
    "limit": 3
  }' | python -m json.tool
```

---

## 4. User Ingredients

### List ingredients

```bash
curl -s http://localhost:8000/api/ingredients | python -m json.tool
```

### Add an ingredient

```bash
curl -s -X POST http://localhost:8000/api/ingredients \
  -H "Content-Type: application/json" \
  -d '{"name": "chicken breast", "quantity": "500g"}' | python -m json.tool
```

### Add multiple ingredients

```bash
curl -s -X POST http://localhost:8000/api/ingredients \
  -H "Content-Type: application/json" \
  -d '{"name": "broccoli", "quantity": "1 head"}' | python -m json.tool

curl -s -X POST http://localhost:8000/api/ingredients \
  -H "Content-Type: application/json" \
  -d '{"name": "rice", "quantity": "1 kg"}' | python -m json.tool
```

### Remove an ingredient

```bash
curl -s -X DELETE http://localhost:8000/api/ingredients/1 -w "\nHTTP Status: %{http_code}\n"
```

---

## 5. Meal Plans

### List meal plans

```bash
curl -s http://localhost:8000/api/meal-plans | python -m json.tool
```

### Create a meal plan

```bash
curl -s -X POST http://localhost:8000/api/meal-plans \
  -H "Content-Type: application/json" \
  -d '{"name": "My Weekly Plan", "week_start_date": "2025-01-20"}' | python -m json.tool
```

### Get a meal plan with entries

```bash
curl -s http://localhost:8000/api/meal-plans/1 | python -m json.tool
```

### Add a recipe to a meal plan slot

```bash
curl -s -X POST "http://localhost:8000/api/meal-plans/1/entries?recipe_id=1&day=monday&meal_type=dinner" \
  -w "\nHTTP Status: %{http_code}\n"
```

### Remove a meal plan entry

```bash
# First get the entry ID from the meal plan response, then:
curl -s -X DELETE http://localhost:8000/api/meal-plans/entries/1 -w "\nHTTP Status: %{http_code}\n"
```

### Auto-generate a weekly plan

```bash
curl -s -X POST "http://localhost:8000/api/meal-plans/generate?plan_name=Auto+Plan" \
  | python -m json.tool
```

### Get weekly nutrition

```bash
curl -s http://localhost:8000/api/meal-plans/1/nutrition | python -m json.tool
```

---

## 6. Shopping List

### Get shopping list

```bash
curl -s http://localhost:8000/api/shopping-list | python -m json.tool
```

### Add an item

```bash
curl -s -X POST http://localhost:8000/api/shopping-list \
  -H "Content-Type: application/json" \
  -d '{"name": "Olive Oil", "quantity": "1 bottle", "category": "Pantry"}' | python -m json.tool
```

### Update an item (mark as purchased)

```bash
curl -s -X PUT http://localhost:8000/api/shopping-list/1 \
  -H "Content-Type: application/json" \
  -d '{"purchased": 1}' | python -m json.tool
```

### Delete an item

```bash
curl -s -X DELETE http://localhost:8000/api/shopping-list/1 -w "\nHTTP Status: %{http_code}\n"
```

### Generate from meal plan

```bash
curl -s -X POST http://localhost:8000/api/shopping-list/generate/1 | python -m json.tool
```

---

## 7. User Preferences

### Get preferences

```bash
curl -s http://localhost:8000/api/preferences | python -m json.tool
```

### Update preferences

```bash
curl -s -X PUT http://localhost:8000/api/preferences \
  -H "Content-Type: application/json" \
  -d '{
    "daily_calorie_target": 1800,
    "diet_type": "keto",
    "protein_target": 120,
    "allergies": ["peanuts"],
    "excluded_ingredients": ["coconut milk"]
  }' | python -m json.tool
```

---

## 8. AI Agent (LLM Function Calling)

> **Note:** Requires `OPENAI_API_KEY` or `QWEN_API_KEY` to be set. Without a key, the agent uses local intent detection.

### Test query: ingredient-based search

```bash
curl -s -X POST http://localhost:8000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "I have chicken, broccoli, and rice. What can I make?"}' \
  | python -m json.tool
```

### Test query: calorie-filtered search

```bash
curl -s -X POST http://localhost:8000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "High-protein dinner under 500 calories"}' \
  | python -m json.tool
```

### Test query: meal plan generation

```bash
curl -s -X POST http://localhost:8000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Plan my week for keto"}' \
  | python -m json.tool
```

### Test query: substitution

```bash
curl -s -X POST http://localhost:8000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "No coconut milk, what can I use instead?"}' \
  | python -m json.tool
```

### Test query: add to shopping list

```bash
curl -s -X POST http://localhost:8000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Add eggs and milk to my shopping list"}' \
  | python -m json.tool
```

### Test query: query meal plan

```bash
curl -s -X POST http://localhost:8000/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What did I plan for Wednesday?"}' \
  | python -m json.tool
```

---

## 9. Seed Database

```bash
cd backend
python seed_recipes.py
```

Expected: `✅ Successfully seeded 30 recipes!`

---

## 10. Telegram Bot

```bash
# Start the bot (requires TELEGRAM_BOT_TOKEN set)
cd backend
python telegram_bot.py
```

Then in Telegram, send:

- `/start` — Welcome message
- `/add chicken, rice, broccoli` — Add ingredients
- `/suggest` — Get recipe suggestions
- `/plan week` — Generate weekly plan
- `/shopping` — Get shopping list

---

## Full Integration Test Script

Run this to test the complete flow:

```bash
#!/bin/bash
API="http://localhost:8000"

echo "=== 1. Seed recipes ==="
cd backend && python seed_recipes.py && cd ..

echo "=== 2. Add ingredients ==="
curl -s -X POST $API/api/ingredients -H "Content-Type: application/json" -d '{"name":"chicken","quantity":"500g"}'
curl -s -X POST $API/api/ingredients -H "Content-Type: application/json" -d '{"name":"rice","quantity":"1kg"}'
curl -s -X POST $API/api/ingredients -H "Content-Type: application/json" -d '{"name":"broccoli","quantity":"1 head"}'

echo -e "\n=== 3. Suggest recipes ==="
curl -s -X POST $API/api/suggest -H "Content-Type: application/json" \
  -d '{"ingredients":["chicken","rice","broccoli"],"limit":3}' | python -m json.tool

echo "=== 4. Generate meal plan ==="
curl -s -X POST "$API/api/meal-plans/generate?plan_name=Test+Week" | python -m json.tool

echo "=== 5. Generate shopping list ==="
curl -s -X POST $API/api/shopping-list/generate/1 | python -m json.tool

echo "=== 6. Get nutrition ==="
curl -s $API/api/meal-plans/1/nutrition | python -m json.tool

echo "=== Done ==="
```
