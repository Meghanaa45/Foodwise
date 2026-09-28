import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


def _to_out(pref: models.UserPreference) -> schemas.UserPreferenceOut:
    return schemas.UserPreferenceOut(
        dietary_restrictions=[s for s in pref.dietary_restrictions.split(",") if s],
        disliked_ingredients=[s for s in pref.disliked_ingredients.split(",") if s],
        cuisine_weights=json.loads(pref.cuisine_weights or "{}"),
        nutrition_goal=pref.nutrition_goal,
        expiry_horizon_days=pref.expiry_horizon_days,
    )


def _get_or_create(db: Session) -> models.UserPreference:
    pref = db.query(models.UserPreference).filter_by(id=1).first()
    if pref is None:
        pref = models.UserPreference(id=1)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.get("", response_model=schemas.UserPreferenceOut)
def get_preferences(db: Session = Depends(get_db)):
    return _to_out(_get_or_create(db))


@router.put("", response_model=schemas.UserPreferenceOut)
def update_preferences(payload: schemas.UserPreferenceUpdate, db: Session = Depends(get_db)):
    pref = _get_or_create(db)
    if payload.dietary_restrictions is not None:
        pref.dietary_restrictions = ",".join(s.strip() for s in payload.dietary_restrictions if s.strip())
    if payload.disliked_ingredients is not None:
        pref.disliked_ingredients = ",".join(s.strip().lower() for s in payload.disliked_ingredients if s.strip())
    if payload.cuisine_weights is not None:
        pref.cuisine_weights = json.dumps(payload.cuisine_weights)
    if payload.nutrition_goal is not None:
        pref.nutrition_goal = payload.nutrition_goal
    if payload.expiry_horizon_days is not None:
        pref.expiry_horizon_days = payload.expiry_horizon_days
    db.commit()
    db.refresh(pref)
    return _to_out(pref)
