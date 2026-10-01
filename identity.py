from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AuditLog, User
from app.schemas import LoginRequest, SignupRequest, TokenResponse, UserRead
from app.services.security import current_user, hash_password, issue_token, verify_password

router = APIRouter(prefix="/identity", tags=["identity"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(name=payload.name, email=payload.email, password_hash=hash_password(payload.password), role="admin")
    db.add(user)
    db.flush()
    db.add(AuditLog(actor=payload.email, action="signup", entity_type="user", entity_id=user.id))
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=issue_token(user), user=user)


@router.post("/token", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=issue_token(user), user=user)


@router.get("/profile", response_model=UserRead)
def profile(user: User = Depends(current_user)):
    return user
