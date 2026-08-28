from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Disruption
from ..schemas import DisruptionCreate, DisruptionOut

router = APIRouter(prefix="/api/disruptions", tags=["disruptions"])


@router.get("", response_model=list[DisruptionOut])
def list_disruptions(db: Session = Depends(get_db)):
    return db.query(Disruption).all()


@router.post("", response_model=DisruptionOut)
def create_disruption(payload: DisruptionCreate, db: Session = Depends(get_db)):
    disruption = Disruption(**payload.model_dump(), active=False)
    db.add(disruption)
    db.commit()
    db.refresh(disruption)
    return disruption


@router.post("/{disruption_id}/activate", response_model=DisruptionOut)
def activate_disruption(disruption_id: int, db: Session = Depends(get_db)):
    disruption = db.query(Disruption).filter(Disruption.id == disruption_id).first()
    if not disruption:
        raise HTTPException(status_code=404, detail="Disruption not found")
    disruption.active = True
    db.commit()
    db.refresh(disruption)
    return disruption


@router.post("/{disruption_id}/deactivate", response_model=DisruptionOut)
def deactivate_disruption(disruption_id: int, db: Session = Depends(get_db)):
    disruption = db.query(Disruption).filter(Disruption.id == disruption_id).first()
    if not disruption:
        raise HTTPException(status_code=404, detail="Disruption not found")
    disruption.active = False
    db.commit()
    db.refresh(disruption)
    return disruption
