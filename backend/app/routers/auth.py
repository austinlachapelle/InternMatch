from fastapi import APIRouter, HTTPException, status

from ..schemas.auth import LoginRequest, RegisterRequest
from ..services.auth import authenticate_user, create_access_token, create_user


router = APIRouter(tags=["auth"])


@router.post("/auth/register")
def register(payload: RegisterRequest) -> dict[str, object]:
    try:
        user = create_user(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    token = create_access_token(user["id"])
    return {"token": token, "user": user}


@router.post("/auth/login")
def login(payload: LoginRequest) -> dict[str, object]:
    user = authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")

    token = create_access_token(user["id"])
    return {"token": token, "user": user}
