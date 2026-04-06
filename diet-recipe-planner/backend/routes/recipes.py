"""
Recipe CRUD API routes.
GET /api/recipes - list with filters
POST /api/recipes - create
GET /api/recipes/{id} - get one
PUT /api/recipes/{id} - update
DELETE /api/recipes/{id} - delete
POST /api/suggest - find recipes by available ingredients
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from schemas import (
    RecipeCreate, RecipeUpdate, RecipeResponse,
    SuggestRequest,
)
import crud

router = APIRouter(prefix="/api", tags=["recipes"])


@router.get("/recipes", response_model=List[RecipeResponse])
def list_recipes(
    skip: int = 0,
    limit: int = 50,
    max_calories: Optional[int] = Query(None, description="Maximum calories per recipe"),
    max_prep_time: Optional[int] = Query(None, description="Maximum prep time in minutes"),
    diet_type: Optional[str] = Query(None, description="Filter by diet type tag"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter"),
    search: Optional[str] = Query(None, description="Search in name, description, cuisine"),
    db: Session = Depends(get_db),
):
    """List recipes with optional filtering."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    return crud.get_recipes(
        db, skip=skip, limit=limit,
        max_calories=max_calories,
        max_prep_time=max_prep_time,
        diet_type=diet_type,
        tags=tag_list,
        search=search,
    )


@router.post("/recipes", response_model=RecipeResponse, status_code=201)
def create_recipe(recipe: RecipeCreate, db: Session = Depends(get_db)):
    """Create a new recipe."""
    return crud.create_recipe(db, recipe)


@router.get("/recipes/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Get a single recipe by ID."""
    recipe = crud.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.put("/recipes/{recipe_id}", response_model=RecipeResponse)
def update_recipe(recipe_id: int, updates: RecipeUpdate, db: Session = Depends(get_db)):
    """Update an existing recipe."""
    recipe = crud.update_recipe(db, recipe_id, updates)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.delete("/recipes/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Delete a recipe."""
    if not crud.delete_recipe(db, recipe_id):
        raise HTTPException(status_code=404, detail="Recipe not found")


@router.post("/suggest", response_model=List[RecipeResponse])
def suggest_recipes(request: SuggestRequest, db: Session = Depends(get_db)):
    """
    Suggest recipes based on available ingredients and optional filters.
    Returns recipes that match at least 2 of the user's ingredients,
    sorted by number of matching ingredients.
    """
    if request.ingredients:
        # Search by ingredient matching
        recipes = crud.search_recipes_by_ingredients(
            db, request.ingredients, min_match=1, limit=request.limit
        )
    else:
        # No ingredients provided, fall back to filtered search
        tag_list = request.tags if request.tags else None
        recipes = crud.get_recipes(
            db, limit=request.limit,
            max_calories=request.max_calories,
            max_prep_time=request.max_prep_time,
            diet_type=request.diet_type.value if request.diet_type else None,
            tags=tag_list,
        )

    # Apply additional filters on the result
    if request.max_calories:
        recipes = [r for r in recipes if r.calories <= request.max_calories]
    if request.max_prep_time:
        recipes = [r for r in recipes if r.prep_time <= request.max_prep_time]
    if request.diet_type:
        diet_tag = request.diet_type.value
        recipes = [r for r in recipes if diet_tag in [t.lower() for t in r.tags]]

    return recipes[:request.limit]
