"""
FastAPI application entry point.
Mounts all route routers and provides the /docs Swagger UI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all route modules
from routes.recipes import router as recipes_router
from routes.ingredients import router as ingredients_router
from routes.meal_plans import router as meal_plans_router
from routes.shopping import router as shopping_router
from routes.preferences import router as preferences_router
from routes.agent import router as agent_router

# Create the FastAPI app
app = FastAPI(
    title="Diet Recipe Planner API",
    description="API for recipe management, meal planning, shopping lists, and AI-powered agent.",
    version="1.0.0",
)

# CORS: Allow frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers
app.include_router(recipes_router)
app.include_router(ingredients_router)
app.include_router(meal_plans_router)
app.include_router(shopping_router)
app.include_router(preferences_router)
app.include_router(agent_router)


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Diet Recipe Planner API"}


@app.get("/health")
def health():
    """Detailed health check."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "endpoints": [
            "/api/recipes",
            "/api/ingredients",
            "/api/meal-plans",
            "/api/shopping-list",
            "/api/preferences",
            "/api/agent/query",
            "/api/suggest",
        ],
    }
