# 🍽️ Diet Recipe Planner

A full-stack recipe planning application with **two interfaces**: a traditional recipe browser/planner and an AI-powered chat agent. Built with FastAPI, PostgreSQL, React, and LLM function calling.

## Features

### Tab 1 — Recipe Browser & Planner

- **Ingredient pantry** — Add/remove ingredients you have on hand
- **Recipe browser** — Filter by calories, prep time, diet type, and search
- **Smart suggestions** — Get recipe recommendations based on your available ingredients
- **Weekly meal calendar** — Drag-and-click to assign recipes to day/meal slots
- **Nutrition charts** — Visualize weekly macro breakdown with bar and doughnut charts
- **Shopping list** — Auto-generated from meal plan, with quantity aggregation and categorization

### Tab 2 — AI Agent Chat

- **Natural language queries** — "What can I cook with chicken and rice?"
- **LLM function calling** — The agent uses tools (not regex) to search, plan, and manage
- **Inline recipe cards** — Structured data rendered in the chat
- **Suggested prompts** — Quick-access buttons for common queries
- **Cross-tab sync** — Actions in chat update the planner and vice versa

### Telegram Bot (Bonus)

- `/add` — Add ingredients to your pantry
- `/suggest` — Get top 3 recipe suggestions
- `/plan week` — Generate a 7-day meal plan
- `/shopping` — Get your grocery list as a formatted message

### Background Jobs (APScheduler)

- **Daily dinner reminder** (8 AM) — Telegram message with today's dinner recipe
- **Weekly shopping list** (Sunday 9 AM) — Auto-generated and sent via Telegram

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)
- OpenAI API key or Qwen API key (for AI agent)

### 1. Clone and configure

```bash
cd diet-recipe-planner
cp .env.example .env
# Edit .env and add your API keys:
#   OPENAI_API_KEY=sk-...
#   TELEGRAM_BOT_TOKEN=...
```

### 2. Start everything

```bash
docker compose up -d
```

This starts:

- **PostgreSQL** on port 5432
- **FastAPI backend** on port 8000 (with hot reload)
- **React frontend** on port 5173 (Vite dev server)

### 3. Seed the database

```bash
docker compose exec backend python seed_recipes.py
```

### 4. Open the app

Navigate to <http://localhost:5173> in your browser.

---

## Architecture

```
diet-recipe-planner/
├── docker-compose.yml          # Orchestrates all services
├── .env.example                # Environment variable template
├── TESTING.md                  # curl commands for every endpoint
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── database.py             # SQLAlchemy engine + session
│   ├── models.py               # ORM models (Recipe, MealPlan, etc.)
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── crud.py                 # Database operations
│   ├── agent.py                # LLM agent with function calling
│   ├── telegram_bot.py         # Telegram bot (python-telegram-bot v21)
│   ├── scheduler.py            # APScheduler cron jobs
│   ├── seed_recipes.py         # 30 diverse recipes
│   └── routes/
│       ├── recipes.py          # /api/recipes, /api/suggest
│       ├── ingredients.py      # /api/ingredients
│       ├── meal_plans.py       # /api/meal-plans, /api/meal-plans/generate
│       ├── shopping.py         # /api/shopping-list
│       ├── preferences.py      # /api/preferences
│       └── agent.py            # /api/agent/query
└── frontend/
    ├── src/
    │   ├── App.jsx             # Main app with tab navigation
    │   ├── api.js              # Fetch wrapper for all API calls
    │   └── components/
    │       ├── RecipeBrowser.jsx    # Tab 1: filters, cards, actions
    │       ├── WeeklyCalendar.jsx   # Weekly meal grid
    │       ├── NutritionChart.jsx   # Chart.js bar + doughnut
    │       ├── ShoppingListModal.jsx # Shopping list with CRUD
    │       └── AgentChat.jsx        # Tab 2: chat interface
    ├── package.json
    ├── vite.config.js
    └── tailwind.config.js
```

---

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/api/recipes` | List recipes with filters |
| POST | `/api/recipes` | Create a recipe |
| GET | `/api/recipes/{id}` | Get a single recipe |
| PUT | `/api/recipes/{id}` | Update a recipe |
| DELETE | `/api/recipes/{id}` | Delete a recipe |
| POST | `/api/suggest` | Suggest recipes by ingredients |
| GET | `/api/ingredients` | List user's ingredients |
| POST | `/api/ingredients` | Add an ingredient |
| DELETE | `/api/ingredients/{id}` | Remove an ingredient |
| GET | `/api/meal-plans` | List all meal plans |
| POST | `/api/meal-plans` | Create a meal plan |
| GET | `/api/meal-plans/{id}` | Get plan with entries |
| POST | `/api/meal-plans/{id}/entries` | Add recipe to a slot |
| DELETE | `/api/meal-plans/entries/{id}` | Remove an entry |
| POST | `/api/meal-plans/generate` | Auto-generate weekly plan |
| GET | `/api/meal-plans/{id}/nutrition` | Weekly nutrition summary |
| GET | `/api/shopping-list` | Get shopping list |
| POST | `/api/shopping-list` | Add an item |
| PUT | `/api/shopping-list/{id}` | Update an item |
| DELETE | `/api/shopping-list/{id}` | Delete an item |
| POST | `/api/shopping-list/generate/{plan_id}` | Generate from plan |
| GET | `/api/preferences` | Get user preferences |
| PUT | `/api/preferences` | Update preferences |
| POST | `/api/agent/query` | AI agent natural language query |

Full Swagger docs available at <http://localhost:8000/docs>

---

## AI Agent — Supported Queries

The agent uses **LLM function calling** (not regex or keyword matching) to interpret queries. Here are tested examples:

| User Query | Tool Called | Action |
| ---------- | ----------- | ------ |
| "I have chicken, broccoli, rice" | `search_recipes` | Finds recipes matching ≥2 ingredients |
| "High-protein dinner under 500 cal" | `search_recipes` | Filters by calories + tags |
| "Plan my week for keto" | `generate_meal_plan` | Creates 7-day plan with keto filter |
| "No coconut milk, what can I use?" | `suggest_substitutions` | Returns alternatives |
| "Add eggs to my shopping list" | `add_to_shopping_list` | Inserts into shopping_list table |
| "What did I plan for Wednesday?" | `get_meal_plan` | Queries meal plan by day |
| "Add chicken to my pantry" | `add_ingredient` | Adds to user_ingredients |

---

## Environment Variables

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `DATABASE_URL` | `postgresql://recipeuser:recipepass@db:5432/recipe_db` | PostgreSQL connection |
| `OPENAI_API_KEY` | — | OpenAI API key (for GPT) |
| `QWEN_API_KEY` | — | Qwen/DashScope API key |
| `LLM_PROVIDER` | `openai` | `openai` or `qwen` |
| `TELEGRAM_BOT_TOKEN` | — | Telegram bot token |
| `TELEGRAM_CHAT_ID` | — | Target chat ID for notifications |
| `CRON_DAILY_REMINDER_HOUR` | `8` | Hour for daily dinner reminder |
| `CRON_WEEKLY_SHOPPING_DAY` | `sun` | Day for weekly shopping list |
| `CRON_WEEKLY_SHOPPING_HOUR` | `9` | Hour for weekly shopping list |

---

## Development

### Run backend locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Run frontend locally

```bash
cd frontend
npm install
npm run dev
```

### Run Telegram bot

```bash
cd backend
python telegram_bot.py
```

### Run seed script

```bash
cd backend
python seed_recipes.py
```

---

## Screenshots

### Tab 1: Recipe Browser & Planner

- Ingredient panel with add/remove
- Filter controls (calories, prep time, diet type)
- Recipe cards with macros and tags
- Weekly calendar grid (Mon–Sun × breakfast/lunch/dinner)
- Nutrition charts (bar + doughnut)
- Shopping list modal with categories

### Tab 2: AI Agent Chat

- ChatGPT-like message bubbles
- Suggested prompt buttons
- Inline recipe cards in responses
- Structured data rendering (substitutions, shopping items, meal plans)

---

## Testing

See [TESTING.md](./TESTING.md) for `curl` commands for every API endpoint.

---

## License

MIT
