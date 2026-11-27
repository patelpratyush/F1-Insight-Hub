from fastapi import APIRouter, Depends
from pydantic import BaseModel

from f1_api.auth.jwt import Principal, current_principal

router = APIRouter(prefix="/v1", tags=["me"])


class MeOut(BaseModel):
    user_id: str
    email: str | None


@router.get("/me", response_model=MeOut, operation_id="getMe")
async def me(principal: Principal = Depends(current_principal)) -> MeOut:  # noqa: B008
    return MeOut(user_id=principal.user_id, email=principal.email)
