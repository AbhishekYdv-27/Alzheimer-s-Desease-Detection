from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer

from backend.app.schemas.auth import UserCreate, UserLogin, UserUpdate, PasswordUpdate, TokenResponse, UserResponse
from backend.app.core.auth import verify_password, create_password_hash, create_access_token, get_current_user_id
from backend.app.core.database import get_user_by_email, get_user_by_id, create_user, update_user_name, update_user_password

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    password_hash = create_password_hash(user_data.password)
    user = create_user(user_data.name, user_data.email, password_hash, "patient")

    access_token = create_access_token(data={"sub": user["id"]})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            created_at=user["created_at"],
            updated_at=user["updated_at"],
            role=user["role"]
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = get_user_by_email(credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(data={"sub": user["id"]})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            created_at=user["created_at"],
            updated_at=user["updated_at"],
            role=user.get("role", "patient")
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user_id: str = Depends(get_current_user_id)):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"],
        updated_at=user["updated_at"],
        role=user.get("role", "patient")
    )


@router.patch("/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(password_data: PasswordUpdate, user_id: str = Depends(get_current_user_id)):
    if len(password_data.new_password) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters")
    user = get_user_by_id(user_id)
    if not user or not verify_password(password_data.current_password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    update_user_password(user_id, create_password_hash(password_data.new_password))


@router.patch("/me", response_model=UserResponse)
async def update_me(user_data: UserUpdate, user_id: str = Depends(get_current_user_id)):
    name = user_data.name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Name must be at least 2 characters")
    user = update_user_name(user_id, name)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(
        id=user["id"], name=user["name"], email=user["email"],
        created_at=user["created_at"], updated_at=user["updated_at"], role=user.get("role", "patient")
    )
