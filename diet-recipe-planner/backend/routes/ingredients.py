"""
User ingredients API routes.
These are the ingredients the user has on hand in their pantry/fridge.
GET /api/ingredients - list all
POST /api/ingredients - add one
DELETE /api/ingredients/{id} - remove one
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import UserIngredientCreate, UserIngredientResponse
import crud

router = APIRouter(prefix="/api", tags=["ingredients"])


@router.get("/ingredients", response_model=List[UserIngredientResponse])
def list_ingredients(db: Session = Depends(get_db)):
    """List all ingredients the user has on hand."""
    return crud.get_user_ingredients(db)


@router.post("/ingredients", response_model=UserIngredientResponse, status_code=201)
def add_ingredient(data: UserIngredientCreate, db: Session = Depends(get_db)):
    """
    Add an ingredient to the user's pantry.
    If the ingredient already exists, updates its quantity.
    """
    return crud.add_user_ingredient(db, data)


@router.delete("/ingredients/{ingredient_id}", status_code=204)
def remove_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    """Remove an ingredient from the user's pantry."""
    if not crud.remove_user_ingredient(db, ingredient_id):
        raise HTTPException(status_code=404, detail="Ingredient not found")
