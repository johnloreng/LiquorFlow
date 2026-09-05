from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserResponse


router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.get(
    "/riders",
    response_model=list[UserResponse],
)
def list_riders(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.DISPATCHER,
        )
    ),
):
    return (
        db.query(User)
        .filter(
            User.role == UserRole.RIDER,
            User.is_active.is_(True),
        )
        .order_by(User.name.asc())
        .all()
    )
