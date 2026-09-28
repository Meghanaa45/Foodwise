from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


def _to_out(recipe: models.Recipe) -> schemas.RecipeOut:
    return schemas.RecipeOut(
        id=recipe.id,
        title=recipe.title,
        cuisine=recipe.cuisine,
        tags=recipe.tags,
        prep_time_minutes=recipe.prep_time_minutes,
        steps=recipe.steps,
        calories=recipe.calories,
        protein_g=recipe.protein_g,
        carbs_g=recipe.carbs_g,
        fat_g=recipe.fat_g,
        ingredients=[
            schemas.RecipeIngredientOut(
                ingredient=schemas.IngredientOut.model_validate(link.ingredient),
                quantity=link.quantity,
                unit=link.unit,
                optional=link.optional,
            )
            for link in recipe.ingredient_links
        ],
    )


@router.get("", response_model=List[schemas.RecipeOut])
def list_recipes(cuisine: Optional[str] = None, search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Recipe).options(
        joinedload(models.Recipe.ingredient_links).joinedload(models.RecipeIngredient.ingredient)
    )
    if cuisine:
        query = query.filter(models.Recipe.cuisine == cuisine)
    if search:
        query = query.filter(models.Recipe.title.ilike(f"%{search}%"))
    return [_to_out(r) for r in query.all()]


@router.get("/{recipe_id}", response_model=schemas.RecipeOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = (
        db.query(models.Recipe)
        .options(joinedload(models.Recipe.ingredient_links).joinedload(models.RecipeIngredient.ingredient))
        .filter_by(id=recipe_id)
        .first()
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return _to_out(recipe)
