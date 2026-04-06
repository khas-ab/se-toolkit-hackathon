"""
Pydantic schemas for API request/response validation.
These define the shape of JSON data sent to and from the frontend.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ─── Enums (mirrors models.py enums for JSON serialization) ───

class DietType(str, Enum):
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    KETO = "keto"
    PALEO = "paleo"
    LOW_CARB = "low_carb"
    MEDITERRANEAN = "mediterranean"
    NONE = "none"


class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class DayOfWeek(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


# ─── Recipe Schemas ───────────────────────────────────────────

class RecipeBase(BaseModel):
    """Fields required to create or update a recipe."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    ingredients: List[str] = Field(..., min_length=1)
    steps: List[str] = Field(..., min_length=1)
    protein: float = 0.0
    fat: float = 0.0
    carbs: float = 0.0
    calories: float = 0.0
    prep_time: int = 0
    cook_time: int = 0
    servings: int = 1
    tags: List[str] = []
    cuisine: str = ""
    image_url: str = ""


class RecipeCreate(RecipeBase):
    """Schema for creating a new recipe (same as base)."""
    pass


class RecipeUpdate(BaseModel):
    """Schema for updating an existing recipe (all fields optional)."""
    name: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[str]] = None
    steps: Optional[List[str]] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    carbs: Optional[float] = None
    calories: Optional[float] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    tags: Optional[List[str]] = None
    cuisine: Optional[str] = None
    image_url: Optional[str] = None


class RecipeResponse(RecipeBase):
    """Recipe returned from the API (includes id and timestamps)."""
    id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Ingredient Schemas ──────────────────────────────────────

class UserIngredientCreate(BaseModel):
    """Add an ingredient to the user's pantry."""
    name: str = Field(..., min_length=1, max_length=100)
    quantity: str = ""


class UserIngredientResponse(BaseModel):
    """Ingredient in the user's pantry."""
    id: int
    name: str
    quantity: str
    added_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Meal Plan Schemas ───────────────────────────────────────

class MealPlanEntryCreate(BaseModel):
    """Add a recipe to a meal plan slot."""
    plan_id: int
    recipe_id: int
    day: DayOfWeek
    meal_type: MealType


class MealPlanEntryResponse(BaseModel):
    """A single meal plan slot with recipe details."""
    id: int
    plan_id: int
    recipe_id: int
    day: DayOfWeek
    meal_type: MealType
    recipe: Optional[RecipeResponse] = None

    model_config = {"from_attributes": True}


class MealPlanCreate(BaseModel):
    """Create a new weekly meal plan."""
    name: str = "Weekly Plan"
    week_start_date: str = ""


class MealPlanResponse(BaseModel):
    """Meal plan with all its entries."""
    id: int
    name: str
    week_start_date: str
    created_at: Optional[datetime] = None
    entries: List[MealPlanEntryResponse] = []

    model_config = {"from_attributes": True}


# ─── Shopping List Schemas ───────────────────────────────────

class ShoppingListItemCreate(BaseModel):
    """Add an item to the shopping list."""
    name: str = Field(..., min_length=1, max_length=200)
    quantity: str = ""
    category: str = ""


class ShoppingListItemUpdate(BaseModel):
    """Update a shopping list item (e.g. mark as purchased)."""
    quantity: Optional[str] = None
    category: Optional[str] = None
    purchased: Optional[int] = None


class ShoppingListItemResponse(BaseModel):
    """A single shopping list item."""
    id: int
    name: str
    quantity: str
    category: str
    purchased: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── User Preference Schemas ─────────────────────────────────

class UserPreferenceCreate(BaseModel):
    """Set or update user dietary preferences."""
    daily_calorie_target: int = 2000
    diet_type: DietType = DietType.NONE
    allergies: List[str] = []
    protein_target: int = 0
    excluded_ingredients: List[str] = []


class UserPreferenceResponse(BaseModel):
    """User's current dietary preferences."""
    id: int
    daily_calorie_target: int
    diet_type: DietType
    allergies: List[str]
    protein_target: int
    excluded_ingredients: List[str]

    model_config = {"from_attributes": True}


# ─── Agent / Suggest Schemas ─────────────────────────────────

class SuggestRequest(BaseModel):
    """Request body for /suggest endpoint."""
    ingredients: List[str] = []       # ingredients user has
    max_calories: Optional[int] = None
    max_prep_time: Optional[int] = None
    diet_type: Optional[DietType] = None
    tags: List[str] = []
    limit: int = 10


class AgentQueryRequest(BaseModel):
    """Natural language query to the AI agent."""
    query: str = Field(..., min_length=1, max_length=1000)


class AgentQueryResponse(BaseModel):
    """Response from the AI agent."""
    response: str           # Natural language text
    data: Optional[dict] = None  # Structured data (recipes, plans, etc.)


# ─── Nutrition Summary ───────────────────────────────────────

class NutritionSummary(BaseModel):
    """Weekly nutrition totals for charts."""
    total_calories: float = 0
    total_protein: float = 0
    total_fat: float = 0
    total_carbs: float = 0
    daily_breakdown: List[dict] = []  # [{day, calories, protein, fat, carbs}]
