from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AuditLog
from app.schemas import AuditLogRead

router = APIRouter(tags=["operations"])


@router.get("/audit-trail", response_model=list[AuditLogRead])
def audit_trail(db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(500).all()


@router.get("/health/database")
def database_health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}
