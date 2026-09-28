from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from .. import models, ocr, schemas
from ..database import get_db
from .inventory import _get_or_create_ingredient, _to_out

router = APIRouter(prefix="/api/receipts", tags=["receipts"])


@router.post("/scan", response_model=schemas.ReceiptScanResult)
def scan_receipt(file: UploadFile = File(...), db: Session = Depends(get_db)):
    image_bytes = file.file.read()
    try:
        raw_text = ocr.extract_text(image_bytes)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    lines = ocr.parse_receipt_lines(raw_text)
    known_names = [i.name for i in db.query(models.Ingredient).all()]
    matched = ocr.match_to_ingredients(lines, known_names)
    return schemas.ReceiptScanResult(items=[schemas.ReceiptParsedItem(**m) for m in matched])


@router.post("/confirm", response_model=list[schemas.InventoryItemOut])
def confirm_receipt_items(payload: schemas.ReceiptConfirmRequest, db: Session = Depends(get_db)):
    """Commit user-confirmed receipt items into inventory (never auto-commits from OCR alone)."""
    created = []
    for entry in payload.items:
        ingredient = _get_or_create_ingredient(db, entry.ingredient_name)
        expiry = date.fromordinal(date.today().toordinal() + ingredient.default_shelf_life_days)
        item = models.InventoryItem(
            ingredient_id=ingredient.id,
            quantity=entry.quantity,
            unit=entry.unit,
            storage_location=entry.storage_location,
            purchase_date=date.today(),
            expiry_date=expiry,
        )
        db.add(item)
        db.flush()
        created.append(item)
    db.commit()
    for item in created:
        db.refresh(item)
    return [_to_out(item) for item in created]
