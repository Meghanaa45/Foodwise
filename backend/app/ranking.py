"""
Recipe ranking engine.

Layer 1 (always active): a transparent, weighted heuristic over expiry
urgency, ingredient coverage, user preference match, and nutrition fit.
Every score component is returned to the caller so the UI can explain why
a recipe was recommended.

Layer 2 (activates once enough interaction data exists): a logistic
regression re-ranker trained on the same feature vector, learning which
combination of signals actually predicts "the user cooked this" versus
"the user skipped this" for this specific person. Falls back to the
Layer 1 heuristic when there isn't enough labeled data yet.
"""
import json
import os
from datetime import date
from typing import Optional

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sqlalchemy.orm import Session, joinedload

from . import models

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "reranker.joblib"
)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

with open(os.path.join(DATA_DIR, "substitutions.json")) as f:
    SUBSTITUTIONS = json.load(f)

MIN_TRAINING_SAMPLES = 12
FEATURE_NAMES = ["coverage", "expiry_urgency", "preference_score", "nutrition_fit", "missing_ratio"]

HEURISTIC_WEIGHTS = {
    "coverage": 0.35,
    "expiry_urgency": 0.30,
    "preference_score": 0.20,
    "nutrition_fit": 0.15,
}


def _days_until(d: Optional[date]) -> Optional[int]:
    if d is None:
        return None
    return (d - date.today()).days


def _expiry_urgency_score(inventory_by_ingredient: dict, ingredient_id: int, horizon_days: int) -> float:
    item = inventory_by_ingredient.get(ingredient_id)
    if item is None or item.expiry_date is None:
        return 0.0
    days_left = _days_until(item.expiry_date)
    if days_left is None:
        return 0.0
    if days_left <= 0:
        return 1.0
    return max(0.0, 1.0 - days_left / horizon_days)


def _nutrition_fit_score(recipe: models.Recipe, goal: str) -> float:
    if not recipe.calories or not recipe.protein_g:
        return 0.5
    protein_ratio = (recipe.protein_g * 4) / max(recipe.calories, 1)
    if goal == "high_protein":
        return min(1.0, protein_ratio / 0.30)
    if goal == "low_carb":
        carbs_ratio = ((recipe.carbs_g or 0) * 4) / max(recipe.calories, 1)
        return max(0.0, 1.0 - carbs_ratio / 0.55)
    if goal == "light":
        return max(0.0, 1.0 - recipe.calories / 700)
    return 0.6  # balanced: mild neutral score, doesn't dominate ranking


def _preference_score(recipe: models.Recipe, cuisine_weights: dict, disliked: set) -> Optional[float]:
    recipe_ingredient_names = {link.ingredient.name for link in recipe.ingredient_links}
    if recipe_ingredient_names & disliked:
        return None  # hard filter, not just a low score
    base = 0.5
    weight = cuisine_weights.get(recipe.cuisine)
    if weight is not None:
        base = max(0.0, min(1.0, 0.5 + weight))
    return base


def score_recipe(
    recipe: models.Recipe,
    inventory_by_ingredient: dict,
    preferences: models.UserPreference,
    cuisine_weights: dict,
    disliked: set,
):
    required_links = [l for l in recipe.ingredient_links if not l.optional]
    optional_links = [l for l in recipe.ingredient_links if l.optional]

    have_required = [l for l in required_links if l.ingredient_id in inventory_by_ingredient]
    missing_required = [l for l in required_links if l.ingredient_id not in inventory_by_ingredient]

    coverage = len(have_required) / len(required_links) if required_links else 1.0

    substitutable = {}
    for link in missing_required:
        subs = SUBSTITUTIONS.get(link.ingredient.name, [])
        for sub in subs:
            sub_ingredient = next(
                (i for i in inventory_by_ingredient.values() if i.ingredient.name == sub["substitute"]),
                None,
            )
            if sub_ingredient is not None:
                substitutable[link.ingredient.name] = sub
                break

    effective_missing = [l for l in missing_required if l.ingredient.name not in substitutable]
    effective_coverage = (
        (len(required_links) - len(effective_missing)) / len(required_links) if required_links else 1.0
    )

    urgency_scores = [
        _expiry_urgency_score(inventory_by_ingredient, l.ingredient_id, preferences.expiry_horizon_days)
        for l in required_links + optional_links
        if l.ingredient_id in inventory_by_ingredient
    ]
    expiry_urgency = max(urgency_scores) if urgency_scores else 0.0
    # a recipe using several expiring items is more valuable than one using just one
    if len(urgency_scores) > 1:
        expiry_urgency = min(1.0, expiry_urgency + 0.1 * (sum(s > 0.3 for s in urgency_scores) - 1))

    preference_score = _preference_score(recipe, cuisine_weights, disliked)
    nutrition_fit = _nutrition_fit_score(recipe, preferences.nutrition_goal)

    expiring_used = [
        l.ingredient.name
        for l in required_links + optional_links
        if l.ingredient_id in inventory_by_ingredient
        and _expiry_urgency_score(inventory_by_ingredient, l.ingredient_id, preferences.expiry_horizon_days) > 0.3
    ]
    missing_names = [l.ingredient.name for l in effective_missing]

    return {
        "coverage": effective_coverage,
        "raw_coverage": coverage,
        "expiry_urgency": expiry_urgency,
        "preference_score": preference_score,
        "nutrition_fit": nutrition_fit,
        "missing_ingredients": missing_names,
        "substitutable": substitutable,
        "expiring_ingredients_used": expiring_used,
        "missing_ratio": len(effective_missing) / len(required_links) if required_links else 0.0,
    }


def heuristic_total(components: dict) -> float:
    return (
        HEURISTIC_WEIGHTS["coverage"] * components["coverage"]
        + HEURISTIC_WEIGHTS["expiry_urgency"] * components["expiry_urgency"]
        + HEURISTIC_WEIGHTS["preference_score"] * components["preference_score"]
        + HEURISTIC_WEIGHTS["nutrition_fit"] * components["nutrition_fit"]
    )


def _load_reranker():
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            return None
    return None


def train_reranker(db: Session) -> Optional[LogisticRegression]:
    """
    Trains a pointwise logistic regression re-ranker from logged interactions.
    Label: 1 if the recipe was cooked or rated >= 4, 0 if skipped or rated <= 2.
    Neutral interactions (plain "viewed", or rating == 3) are not used as labels.
    """
    rows = (
        db.query(models.Interaction)
        .filter(models.Interaction.coverage.isnot(None))
        .all()
    )
    X, y = [], []
    for row in rows:
        label = None
        if row.action == "cooked":
            label = 1
        elif row.action == "skipped":
            label = 0
        elif row.action == "rated" and row.rating is not None:
            if row.rating >= 4:
                label = 1
            elif row.rating <= 2:
                label = 0
        if label is None:
            continue
        X.append(
            [
                row.coverage or 0.0,
                row.expiry_urgency or 0.0,
                row.preference_score or 0.0,
                row.nutrition_fit or 0.0,
                (row.missing_count or 0) / 10.0,
            ]
        )
        y.append(label)

    if len(X) < MIN_TRAINING_SAMPLES or len(set(y)) < 2:
        return None

    model = LogisticRegression(max_iter=1000)
    model.fit(np.array(X), np.array(y))
    joblib.dump(model, MODEL_PATH)
    return model


def get_recommendations(db: Session, top_n: int = 10):
    preferences = db.query(models.UserPreference).filter_by(id=1).first()
    if preferences is None:
        preferences = models.UserPreference(id=1)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)

    cuisine_weights = json.loads(preferences.cuisine_weights or "{}")
    disliked = {n.strip() for n in preferences.disliked_ingredients.split(",") if n.strip()}
    restrictions = {n.strip() for n in preferences.dietary_restrictions.split(",") if n.strip()}

    inventory = db.query(models.InventoryItem).options(joinedload(models.InventoryItem.ingredient)).all()
    inventory_by_ingredient = {item.ingredient_id: item for item in inventory}

    recipes = (
        db.query(models.Recipe)
        .options(joinedload(models.Recipe.ingredient_links).joinedload(models.RecipeIngredient.ingredient))
        .all()
    )

    reranker = _load_reranker()
    results = []
    for recipe in recipes:
        recipe_tags = {t.strip() for t in recipe.tags.split(",") if t.strip()}
        if restrictions and not restrictions.issubset(recipe_tags):
            continue

        components = score_recipe(recipe, inventory_by_ingredient, preferences, cuisine_weights, disliked)
        if components["preference_score"] is None:
            continue  # hard filtered: recipe uses a disliked ingredient

        if reranker is not None:
            feature_vec = np.array(
                [[
                    components["coverage"],
                    components["expiry_urgency"],
                    components["preference_score"],
                    components["nutrition_fit"],
                    components["missing_ratio"],
                ]]
            )
            score = float(reranker.predict_proba(feature_vec)[0][1])
            model_used = "learned_reranker"
        else:
            score = heuristic_total(components)
            model_used = "heuristic"

        results.append((recipe, score, components, model_used))

    results.sort(key=lambda r: r[1], reverse=True)
    return results[:top_n]
