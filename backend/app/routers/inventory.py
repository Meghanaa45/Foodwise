from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


def _to_out(item: models.InventoryItem) -> schemas.InventoryItemOut:
    out = schemas.InventoryItemOut.model_validate(item)
    if item.expiry_date:
        out.days_until_expiry = (item.expiry_date - date.today()).days
    return out


def _get_or_create_ingredient(db: Session, name: str) -> models.Ingredient:
    normalized = name.strip().lower()
    ingredient = db.query(models.Ingredient).filter_by(name=normalized).first()
    if ingredient:
        return ingredient
    ingredient = models.Ingredient(name=normalized, category="pantry", default_shelf_life_days=30)
    db.add(ingredient)
    db.flush()
    return ingredient


@router.get("", response_model=List[schemas.InventoryItemOut])
def list_inventory(db: Session = Depends(get_db)):
    items = (
        db.query(models.InventoryItem)
        .options(joinedload(models.InventoryItem.ingredient))
        .order_by(models.InventoryItem.expiry_date.is_(None), models.InventoryItem.expiry_date)
        .all()
    )
    return [_to_out(item) for item in items]


@router.post("", response_model=schemas.InventoryItemOut)
def add_inventory_item(payload: schemas.InventoryItemCreate, db: Session = Depends(get_db)):
    ingredient = _get_or_create_ingredient(db, payload.ingredient_name)
    expiry = payload.expiry_date
    purchase = payload.purchase_date or date.today()
    if expiry is None:
        expiry = date.fromordinal(purchase.toordinal() + ingredient.default_shelf_life_days)

    item = models.InventoryItem(
        ingredient_id=ingredient.id,
        quantity=payload.quantity,
        unit=payload.unit,
        storage_location=payload.storage_location,
        purchase_date=purchase,
        expiry_date=expiry,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_out(item)


@router.put("/{item_id}", response_model=schemas.InventoryItemOut)
def update_inventory_item(item_id: int, payload: schemas.InventoryItemUpdate, db: Session = Depends(get_db)):
    item = db.query(models.InventoryItem).filter_by(id=item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return _to_out(item)


@router.delete("/{item_id}")
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.InventoryItem).filter_by(id=item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    db.delete(item)
    db.commit()
    return {"deleted": item_id}
