# Diet Recipe Planner

A full-stack recipe planning application with two interfaces: a traditional recipe browser/planner and an AI-powered chat agent. Built with FastAPI, PostgreSQL, React, and LLM function calling.

## Demo

### Tab 1 — Recipe Browser & Planner

Traditional UI with ingredient filters, recipe cards, weekly calendar, and nutrition charts.

![Recipe Browser](diet-recipe-planner/docs/screenshot-recipe-browser.png)

### Tab 2 — AI Agent Chat

Natural language queries with inline recipe cards and structured data rendering.

![AI Agent Chat](diet-recipe-planner/docs/screenshot-agent-chat.png)

## Product Context

### End Users

- Home cooks who want to plan meals based on what they already have in their pantry
- People tracking their nutrition (calories, protein, macros) on a weekly basis
- Anyone who wants quick recipe ideas without scrolling through blogs

### Problem

Planning meals is tedious. You need to:
1. Check what ingredients you have at home
2. Find recipes that match those ingredients
3. Fit recipes into a weekly schedule
4. Make a shopping list for missing items
5. Keep track of your nutrition goals

Most recipe apps do one of these things. None do all of them together.

### Our Solution

A single web application with two views:

- **Recipe Browser & Planner** — Filter recipes by calories, prep time, and diet type. Add recipes to a weekly calendar. Auto-generate a shopping list from your plan.
- **AI Agent Chat** — Ask natural language questions like "What can I cook with chicken and rice?" or "Plan my week for keto." The agent uses LLM function calling to search recipes, suggest substitutions, and manage your meal plan.

Both views share the same database, so actions in one tab update the other.

## Features

### Implemented

- [x] Recipe CRUD with 32 seeded recipes (breakfast, lunch, dinner, snacks; 8 cuisines)
- [x] Ingredient pantry — add/remove ingredients you have on hand
- [x] Smart recipe suggestions based on available ingredients
- [x] Filters: max calories, max prep time, diet type (keto, vegan, vegetarian, paleo, low-carb, mediterranean), full-text search
- [x] Weekly meal calendar (Mon–Sun × breakfast/lunch/dinner) with click-to-add
- [x] Auto-generate weekly meal plans based on user preferences
- [x] Nutrition charts — bar chart (daily macros) + doughnut chart (weekly distribution) via Chart.js
- [x] Shopping list — auto-generated from meal plan with quantity aggregation and category grouping
- [x] AI Agent Chat with local intent detection (works without any LLM API key)
- [x] AI Agent with LLM function calling (OpenAI or Qwen) when API key is configured
- [x] Telegram bot: `/add`, `/suggest`, `/plan week`, `/shopping`
- [x] APScheduler cron jobs: daily dinner reminder, weekly shopping list
- [x] Docker Compose — PostgreSQL, FastAPI (hot reload), React (Vite) in one command
- [x] Responsive UI (mobile-friendly)

### Not Yet Implemented

- [ ] Drag-and-drop recipe assignment in the weekly calendar
- [ ] User authentication and multi-user support
- [ ] Recipe image uploads (currently using emoji placeholders)
- [ ] PDF export of shopping lists
- [ ] Recipe rating and favorites
- [ ] Portion scaling (adjust ingredient quantities for N servings)
- [ ] Integration with grocery delivery APIs

## Usage

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- OpenAI API key or Qwen API key (optional — the agent works without one)

### Quick Start

```bash
cd diet-recipe-planner
cp .env.example .env
# Edit .env and add your API keys if needed (optional)
docker compose up -d
docker compose exec backend python seed_recipes.py
```

Open **http://localhost:5173** in your browser.

### Telegram Bot

1. Get a bot token from **@BotFather** on Telegram
2. Get your chat ID from **@userinfobot**
3. Add both to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your-token-here
   TELEGRAM_CHAT_ID=your-chat-id-here
   ```
4. Restart the backend and start the bot:
   ```bash
   docker compose restart backend
   docker compose exec backend python telegram_bot.py
   ```
5. In Telegram, send:
   - `/start` — Welcome message
   - `/add chicken, rice, broccoli` — Add ingredients
   - `/suggest` — Get recipe suggestions
   - `/plan week` — Generate weekly plan
   - `/shopping` — Get grocery list

### API Documentation

Swagger UI: **http://localhost:8000/docs**

Full curl test commands: see [TESTING.md](diet-recipe-planner/TESTING.md)

## Deployment

### Target OS

Ubuntu 24.04 LTS (same as university VMs)

### What Should Be Installed

- **Docker** (24.0+)
- **Docker Compose** (v2, included with Docker Desktop or `docker-compose-plugin`)
- **Git**

Install on a fresh Ubuntu 24.04 VM:

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in for group change to take effect

# Verify
docker --version
docker compose version
```

### Step-by-Step Deployment

1. **Clone the repository:**

   ```bash
   git clone https://github.com/khas-ab/se-toolkit-lab-9.git
   cd se-toolkit-lab-9/diet-recipe-planner
   ```

2. **Configure environment:**

   ```bash
   cp .env.example .env
   nano .env
   ```

   Required settings:
   - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` — database credentials (defaults are fine for dev)
   - `OPENAI_API_KEY` or `QWEN_API_KEY` — for AI agent (optional, agent works without it)
   - `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` — for Telegram bot (optional)

3. **Start all services:**

   ```bash
   docker compose up -d
   ```

   This starts:
   - PostgreSQL on port 5432
   - FastAPI backend on port 8000
   - React frontend on port 5173

4. **Seed the database:**

   ```bash
   docker compose exec backend python seed_recipes.py
   ```

5. **Verify:**

   ```bash
   curl http://localhost:8000/health
   ```

   Expected: `{"status":"ok","version":"1.0.0",...}`

6. **Open the app:**

   Navigate to `http://<VM_IP>:5173` in your browser.

7. **(Optional) Start the Telegram bot:**

   ```bash
   docker compose exec backend python telegram_bot.py
   ```

### Firewall

If UFW is enabled, open the required ports:

```bash
sudo ufw allow 5173/tcp   # Frontend
sudo ufw allow 8000/tcp   # Backend API
sudo ufw allow 5432/tcp   # PostgreSQL (optional, only if external access needed)
```

### Production Notes

- Replace `allow_origins=["*"]` in `backend/main.py` with your actual frontend domain
- Set `NODE_ENV=production` and run `npm run build` for the frontend
- Use a reverse proxy (nginx/Caddy) for HTTPS
- Use named volumes for PostgreSQL data persistence (already configured)
- Rotate API keys and never commit `.env` to git
