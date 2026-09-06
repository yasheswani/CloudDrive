from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import current_user
from app.models.models import Activity, User

router = APIRouter(prefix="/activities", tags=["activities"])

@router.get("")
def list_activities(
    limit: int = 50,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    activities = (
        db.query(Activity)
        .filter(Activity.user_id == user.id)
        .order_by(Activity.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": a.id,
            "action": a.action,
            "target_type": a.target_type,
            "target_id": a.target_id,
            "metadata_json": a.metadata_json,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in activities
    ]
