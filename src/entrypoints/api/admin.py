from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.app.dependencies import get_cost_tracker, get_user_repository
from src.domain.entities.user import UserProfile
from src.domain.ports.user_repository import UserRepositoryProtocol
from src.services.cost_tracker import CostTrackerService

router = APIRouter(prefix="/v1/admin", tags=["admin"])


class UsageStats(BaseModel):
    input_tokens: int
    output_tokens: int


class UserUsage(BaseModel):
    user: UserProfile
    usage: UsageStats


class AdminUsageResponse(BaseModel):
    users: list[UserUsage]
    total_users: int
    total_usage: UsageStats


@router.get("/dashboard", response_class=FileResponse)
async def admin_dashboard() -> FileResponse:
    """
    Render the admin dashboard UI.
    """
    template_path = Path(__file__).parent / "templates" / "admin_dashboard.html"
    return FileResponse(template_path)


@router.get("/usage", response_model=AdminUsageResponse)
async def get_usage_stats(
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repository)],
    cost_tracker: Annotated[CostTrackerService, Depends(get_cost_tracker)],
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> AdminUsageResponse:
    """
    Get usage statistics for all users.
    """
    # 1. Fetch users from DB
    users = await user_repo.list_all(limit=limit, offset=offset)

    # 2. Fetch usage from Redis
    user_ids = [str(u.id) for u in users]
    usage_map = await cost_tracker.get_bulk_usage(user_ids)

    # 3. Construct response
    items = []
    total_input = 0
    total_output = 0

    for user in users:
        stats = usage_map.get(str(user.id), {"input_tokens": 0, "output_tokens": 0})
        total_input += stats["input_tokens"]
        total_output += stats["output_tokens"]
        items.append(UserUsage(user=user, usage=UsageStats(**stats)))

    return AdminUsageResponse(
        users=items,
        total_users=len(items),
        total_usage=UsageStats(input_tokens=total_input, output_tokens=total_output),
    )
