from datetime import date, timedelta
import json
import os

from sqlalchemy.orm import Session

from . import models

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


def seed_if_empty(db: Session):
    shelf_life = _load_json("shelf_life.json")
    recipes = _load_json("recipes.json")

    ingredient_cache = {}

    def get_or_create_ingredient(name: str, category: str) -> models.Ingredient:
        if name in ingredient_cache:
            return ingredient_cache[name]
        existing = db.query(models.Ingredient).filter_by(name=name).first()
        if existing:
            ingredient_cache[name] = existing
            return existing
        ingredient = models.Ingredient(
            name=name,
            category=category,
            default_shelf_life_days=shelf_life.get(category, 30),
        )
        db.add(ingredient)
        db.flush()
        ingredient_cache[name] = ingredient
        return ingredient

    if db.query(models.Recipe).first() is None:
        for recipe_data in recipes:
            recipe = models.Recipe(
                title=recipe_data["title"],
                cuisine=recipe_data["cuisine"],
                tags=recipe_data["tags"],
                prep_time_minutes=recipe_data["prep_time_minutes"],
                steps=recipe_data["steps"],
                calories=recipe_data.get("calories"),
                protein_g=recipe_data.get("protein_g"),
                carbs_g=recipe_data.get("carbs_g"),
                fat_g=recipe_data.get("fat_g"),
            )
            db.add(recipe)
            db.flush()

            for ing in recipe_data["ingredients"]:
                ingredient = get_or_create_ingredient(ing["name"], ing["category"])
                db.add(
                    models.RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient.id,
                        quantity=ing["quantity"],
                        unit=ing["unit"],
                        optional=ing["optional"],
                    )
                )

    if db.query(models.UserPreference).filter_by(id=1).first() is None:
        db.add(models.UserPreference(id=1))

    if db.query(models.InventoryItem).first() is None:
        today = date.today()
        sample_inventory = [
            {"name": "salmon fillet", "category": "protein_fish", "qty": 2, "unit": "portions", "days": 1},
            {"name": "ground beef", "category": "protein_meat", "qty": 1, "unit": "lb", "days": 2},
            {"name": "spinach", "category": "produce_leafy", "qty": 1, "unit": "bag", "days": 2},
            {"name": "white fish fillet", "category": "protein_fish", "qty": 2, "unit": "fillets", "days": 3},
            {"name": "lettuce", "category": "produce_leafy", "qty": 1, "unit": "head", "days": 3},
            {"name": "garlic", "category": "produce_root", "qty": 1, "unit": "bulb", "days": 14},
            {"name": "soy sauce", "category": "condiment", "qty": 1, "unit": "bottle", "days": 60},
        ]
        for item_data in sample_inventory:
            ing = get_or_create_ingredient(item_data["name"], item_data["category"])
            db.add(
                models.InventoryItem(
                    ingredient_id=ing.id,
                    quantity=item_data["qty"],
                    unit=item_data["unit"],
                    storage_location="fridge" if item_data["days"] <= 7 else "pantry",
                    purchase_date=today,
                    expiry_date=today + timedelta(days=item_data["days"]),
                )
            )

    db.commit()

