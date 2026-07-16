from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import PlannerItem, TourContent
from ..schemas import PlannerItemCreate, PlannerItemOut, PlannerItemUpdate

router = APIRouter(prefix="/api/planner", tags=["planner"])


def client_id(x_planner_id: str = Header(min_length=8, max_length=64)) -> str:
    return x_planner_id


@router.get("", response_model=list[PlannerItemOut])
def list_items(cid: str = Depends(client_id), db: Session = Depends(get_db)):
    return db.execute(
        select(PlannerItem)
        .options(joinedload(PlannerItem.content))
        .where(PlannerItem.client_id == cid)
        .order_by(PlannerItem.plan_date, PlannerItem.sort_order, PlannerItem.id)
    ).scalars().all()


@router.post("", response_model=PlannerItemOut, status_code=201)
def create_item(payload: PlannerItemCreate, cid: str = Depends(client_id), db: Session = Depends(get_db)):
    if not db.scalar(select(TourContent).where(TourContent.contentid == payload.content_id)):
        raise HTTPException(status_code=404, detail="관광 콘텐츠를 찾을 수 없습니다.")
    order = db.scalar(select(func.count()).select_from(PlannerItem).where(
        PlannerItem.client_id == cid, PlannerItem.plan_date == payload.plan_date
    )) or 0
    item = PlannerItem(client_id=cid, sort_order=order, **payload.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return db.execute(select(PlannerItem).options(joinedload(PlannerItem.content)).where(PlannerItem.id == item.id)).scalar_one()


@router.patch("/{item_id}", response_model=PlannerItemOut)
def update_item(item_id: int, payload: PlannerItemUpdate, cid: str = Depends(client_id), db: Session = Depends(get_db)):
    item = db.scalar(select(PlannerItem).where(PlannerItem.id == item_id, PlannerItem.client_id == cid))
    if not item:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    return db.execute(select(PlannerItem).options(joinedload(PlannerItem.content)).where(PlannerItem.id == item.id)).scalar_one()


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, cid: str = Depends(client_id), db: Session = Depends(get_db)):
    item = db.scalar(select(PlannerItem).where(PlannerItem.id == item_id, PlannerItem.client_id == cid))
    if not item:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
    db.delete(item); db.commit()
