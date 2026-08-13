"""
Users Router
============
REST API endpoints for the Users table.
Supports GET (list/detail), POST, PUT, DELETE with pagination.
Passwords are hashed before storage; PasswordHash is never exposed in responses.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "User not found"}},
)


# ---------------------------------------------------------------------------
# GET /users — List all users
# ---------------------------------------------------------------------------
@router.get("/", response_model=schemas.PaginatedResponse)
def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    db: Session = Depends(get_db),
):
    """Retrieve a paginated list of users (passwords are never returned)."""
    total, items = crud.get_users(db, skip=skip, limit=limit)
    return schemas.PaginatedResponse(
        total=total,
        page=(skip // limit) + 1,
        per_page=limit,
        items=[schemas.UserResponse.model_validate(item) for item in items],
    )


# ---------------------------------------------------------------------------
# GET /users/{user_id} — Get user details
# ---------------------------------------------------------------------------
@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Retrieve a single user by UserID (password is never returned)."""
    db_user = crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    return db_user


# ---------------------------------------------------------------------------
# POST /users/login — Verify credentials and return access token
# ---------------------------------------------------------------------------
@router.post("/login", response_model=schemas.TokenResponse)
def login_user(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """Log in a user and return a JWT access token."""
    from ..auth import verify_password
    db_user = crud.get_user_by_username(db, login_data.Username)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    # Check password
    if not verify_password(login_data.Password, db_user.Password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Return a simulated JWT token (base64 encoded string representing user)
    import base64
    token_str = f"{db_user.Username}:{db_user.Role}:{db_user.UserID}"
    encoded_token = base64.b64encode(token_str.encode()).decode()

    return schemas.TokenResponse(
        access_token=f"mock-jwt-{encoded_token}",
        user=schemas.UserResponse.model_validate(db_user)
    )


# ---------------------------------------------------------------------------
# POST /users — Create a new user
# ---------------------------------------------------------------------------
@router.post(
    "/",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    """Create a new user. Password is hashed before storage."""
    # Check for duplicate UserID
    existing = crud.get_user(db, user.UserID)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with ID '{user.UserID}' already exists",
        )

    # Check for duplicate username
    existing_username = crud.get_user_by_username(db, user.Username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user.Username}' is already taken",
        )

    # Check for duplicate email
    existing_email = crud.get_user_by_email(db, user.Email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{user.Email}' is already registered",
        )

    return crud.create_user(db, user)


# ---------------------------------------------------------------------------
# PUT /users/{user_id} — Update a user
# ---------------------------------------------------------------------------
@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: str,
    user: schemas.UserUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing user. Password is re-hashed if provided."""
    updated = crud.update_user(db, user_id, user)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    return updated


# ---------------------------------------------------------------------------
# DELETE /users/{user_id} — Delete a user
# ---------------------------------------------------------------------------
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    """Delete a user by UserID."""
    deleted = crud.delete_user(db, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    return None
