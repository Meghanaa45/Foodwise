import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import models, ranking, schemas
from ..database import get_db

router = APIRouter(prefix="/api/interactions", tags=["interactions"])

VALID_ACTIONS = {"viewed", "cooked", "skipped", "rated"}


@router.post("", response_model=schemas.InteractionOut)
def log_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    if payload.action not in VALID_ACTIONS:
        raise HTTPException(status_code=400, detail=f"action must be one of {sorted(VALID_ACTIONS)}")
    if payload.action == "rated" and payload.rating is None:
        raise HTTPException(status_code=400, detail="rating is required when action is 'rated'")

    recipe = (
        db.query(models.Recipe)
        .options(joinedload(models.Recipe.ingredient_links).joinedload(models.RecipeIngredient.ingredient))
        .filter_by(id=payload.recipe_id)
        .first()
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    preferences = db.query(models.UserPreference).filter_by(id=1).first()
    if preferences is None:
        preferences = models.UserPreference(id=1)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)

    cuisine_weights = json.loads(preferences.cuisine_weights or "{}")
    disliked = {n.strip() for n in preferences.disliked_ingredients.split(",") if n.strip()}
    inventory = db.query(models.InventoryItem).options(joinedload(models.InventoryItem.ingredient)).all()
    inventory_by_ingredient = {item.ingredient_id: item for item in inventory}

    components = ranking.score_recipe(recipe, inventory_by_ingredient, preferences, cuisine_weights, disliked)

    interaction = models.Interaction(
        recipe_id=payload.recipe_id,
        action=payload.action,
        rating=payload.rating,
        coverage=components["coverage"],
        expiry_urgency=components["expiry_urgency"],
        preference_score=components["preference_score"] if components["preference_score"] is not None else 0.5,
        nutrition_fit=components["nutrition_fit"],
        missing_count=len(components["missing_ingredients"]),
    )
    db.add(interaction)

    if payload.action == "cooked":
        _decrement_inventory(db, recipe, inventory_by_ingredient)

    db.commit()
    db.refresh(interaction)
    return interaction


@router.get("", response_model=List[schemas.InteractionOut])
def list_interactions(db: Session = Depends(get_db)):
    return db.query(models.Interaction).order_by(models.Interaction.created_at.desc()).limit(200).all()


def _decrement_inventory(db: Session, recipe: models.Recipe, inventory_by_ingredient: dict):
    """Best-effort inventory decrement when a recipe is marked as cooked."""
    for link in recipe.ingredient_links:
        item = inventory_by_ingredient.get(link.ingredient_id)
        if item is None:
            continue
        item.quantity = max(0.0, item.quantity - link.quantity)
        if item.quantity == 0:
            db.delete(item)
