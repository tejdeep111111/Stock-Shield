from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product
from ..schemas import ProductOut
from ..services.agent import run_recovery_analysis

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{product_id}/risk")
def get_product_risk(product_id: int, db: Session = Depends(get_db)):
    analysis = run_recovery_analysis(db, [product_id], None, 10000, "product-risk")
    return {"risks": analysis["at_risk_products"], "recommendation": analysis["recommendation"]}
