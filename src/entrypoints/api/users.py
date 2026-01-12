from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dependencies import get_db_session, get_user_repository
from src.domain.entities.user import UserProfile, CareerInfo
from src.domain.ports.user_repository import UserRepositoryProtocol

router = APIRouter(prefix="/v1/users", tags=["users"])


@router.get("/")
async def list_users(
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List all users with pagination.
    """
    # TODO: Implement proper listing in the domain layer
    # For now, return empty list to avoid implementing unsupported methods
    return {"users": [], "total": 0, "limit": limit, "offset": offset}


@router.get("/{user_id}", response_model=UserProfile)
async def get_user(
    user_id: str,
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repository)],
) -> UserProfile:
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
    return user


@router.get("/by-email/{email}", response_model=UserProfile)
async def get_user_by_email(
    email: str,
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repository)],
) -> UserProfile:
    """
    Get a user profile by email address.
    """
    user = await user_repo.get_by_email(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/")
async def create_user(
    user_data: dict[str, Any],  # Pydantic model could be added later
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repository)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """
    Create a new user profile.
    """
    # Validate required fields
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
        user = UserProfile(
            id=user_id,
            email=user_data["email"],
            full_name=user_data.get("full_name"),
            career=CareerInfo(
                profession=user_data.get("profession"),
                experience_years=user_data.get("experience_years", 0),
            ),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid user data: {str(e)}"
        ) from e

    # Check if user already exists
    existing = await user_repo.get_by_id(user_id)
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    await user_repo.save(user)
    await db.commit()
    return user.model_dump()


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    user_data: dict[str, Any],
    user_repo: Annotated[UserRepositoryProtocol, Depends(get_user_repository)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """
    Update an existing user profile.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid user ID format") from e

    # Check if user exists
    existing_user = await user_repo.get_by_id(user_uuid)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields
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

    # Create updated user object - use immutable pattern
    updated_user = existing_user.update_profession(
        updates.get("profession", existing_user.career.profession or ""),
        updates.get("experience_years", existing_user.career.experience_years),
    )
    updated_user = updated_user.model_copy(
        update={
            k: v
            for k, v in updates.items()
            if k not in ["profession", "experience_years"]
        }
    )

    await user_repo.save(updated_user)
    await db.commit()
    return updated_user.model_dump()


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

    # In a real implementation, you'd need a delete method in the repository
    # For now, this is a placeholder since the domain doesn't specify user deletion
    raise HTTPException(status_code=501, detail="User deletion not implemented")
