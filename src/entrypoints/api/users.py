from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dependencies import get_db_session, get_user_repository
from src.domain.entities.user import UserProfile
from src.domain.ports.user_repository import UserRepositoryProtocol
from src.domain.value_objects import EmailAddress, Profession
from src.entrypoints.api.schemas import UserResponse

router = APIRouter(prefix="/v1/users", tags=["users"])


def _to_response(user: UserProfile) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email.value,
        is_active=user.is_active,
        created_at=user.created_at,
        full_name=user.full_name,
        profession=user.profession.title if user.profession else None,
        experience_years=user.profession.experience_years if user.profession else 0,
    )


@router.get("/")
async def list_users(
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List all users with pagination.
    """
    return {"users": [], "total": 0, "limit": limit, "offset": offset}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repository)],
) -> UserResponse:
    """
    Get a user profile by ID.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid user ID format") from e

    user = await user_repo.get_by_id(user_uuid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_response(user)


@router.get("/by-email/{email}", response_model=UserResponse)
async def get_user_by_email(
    email: str,
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repository)],
) -> UserResponse:
    """
    Get a user profile by email address.
    """
    user = await user_repo.get_by_email(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_response(user)


@router.post("/")
async def create_user(
    user_data: dict[str, Any],
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repository)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserResponse:
    """
    Create a new user profile.
    """
    required_fields = ["id", "email"]
    for field in required_fields:
        if field not in user_data:
            raise HTTPException(
                status_code=400, detail=f"Missing required field: {field}"
            )

    try:
        user_id = (
            UUID(user_data["id"])
            if isinstance(user_data["id"], str)
            else user_data["id"]
        )

        prof = None
        if user_data.get("profession"):
            prof = Profession(
                title=user_data["profession"],
                experience_years=user_data.get("experience_years", 0),
            )

        user = UserProfile(
            id=user_id,
            email=EmailAddress(value=user_data["email"]),
            full_name=user_data.get("full_name"),
            profession=prof,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid user data: {str(e)}"
        ) from e

    existing = await user_repo.get_by_id(user_id)
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    await user_repo.save(user)
    await db.commit()
    return _to_response(user)


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    user_data: dict[str, Any],
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repository)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserResponse:
    """
    Update an existing user profile.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid user ID format") from e

    existing_user = await user_repo.get_by_id(user_uuid)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    updates = {}
    updatable_fields = [
        "email",
        "full_name",
        "profession",
        "experience_years",
        "is_active",
    ]
    for field in updatable_fields:
        if field in user_data:
            updates[field] = user_data[field]

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    curr_title = existing_user.profession.title if existing_user.profession else ""
    curr_years = (
        existing_user.profession.experience_years if existing_user.profession else 0
    )

    new_title = updates.get("profession", curr_title)
    new_years = updates.get("experience_years", curr_years)

    if "profession" in updates or "experience_years" in updates:
        updated_user = existing_user.update_profession(new_title, new_years)
    else:
        updated_user = existing_user

    if "email" in updates:
        updates["email"] = EmailAddress(value=updates["email"])

    fields_to_update = {
        k: v for k, v in updates.items() if k not in ["profession", "experience_years"]
    }

    if fields_to_update:
        updated_user = updated_user.model_copy(update=fields_to_update)

    await user_repo.save(updated_user)
    await db.commit()
    return _to_response(updated_user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repository)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """
    Delete a user profile.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid user ID format") from e

    user = await user_repo.get_by_id(user_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    raise HTTPException(status_code=501, detail="User deletion not implemented")
