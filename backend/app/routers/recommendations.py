from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import ranking, schemas
from ..database import get_db
from ..routers.recipes import _to_out as recipe_to_out

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("", response_model=List[schemas.RecommendationOut])
def get_recommendations(top_n: int = 10, db: Session = Depends(get_db)):
    results = ranking.get_recommendations(db, top_n=top_n)
    return [
        schemas.RecommendationOut(
            recipe=recipe_to_out(recipe),
            score=round(score, 4),
            coverage=round(components["coverage"], 3),
            expiry_urgency=round(components["expiry_urgency"], 3),
            preference_score=round(components["preference_score"], 3),
            nutrition_fit=round(components["nutrition_fit"], 3),
            missing_ingredients=components["missing_ingredients"],
            substitutable=components["substitutable"],
            expiring_ingredients_used=components["expiring_ingredients_used"],
            model_used=model_used,
        )
        for recipe, score, components, model_used in results
    ]


@router.post("/retrain")
def retrain(db: Session = Depends(get_db)):
    model = ranking.train_reranker(db)
    if model is None:
        return {
            "trained": False,
            "reason": f"Need at least {ranking.MIN_TRAINING_SAMPLES} labeled interactions "
            "(cooked/skipped/rated) covering both positive and negative outcomes.",
        }
    return {"trained": True}
