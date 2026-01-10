from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dependencies import (
    get_db_session,
    get_sphere_repository,
)
from src.domain.entities.sphere import Sphere
from src.domain.ports.sphere_repository import SphereRepositoryProtocol

router = APIRouter(prefix="/v1/spheres", tags=["spheres"])


@router.get("/")
async def list_spheres(
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    List all spheres with pagination.
    """
    # TODO: Implement proper listing
    return {"spheres": [], "total": 0, "limit": limit, "offset": offset}


@router.get("/{sphere_id}", response_model=Sphere)
async def get_sphere(
    sphere_id: str,
    sphere_repo: Annotated[SphereRepositoryProtocol, Depends(get_sphere_repository)],
) -> Sphere:
    """
    Get a sphere by ID.
    """
    try:
        sphere_uuid = UUID(sphere_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid sphere ID format") from e

    sphere = await sphere_repo.get_by_id(sphere_uuid)
    if sphere is None:
        raise HTTPException(status_code=404, detail="Sphere not found")
    return sphere


@router.get("/user/{user_id}")
async def list_spheres_for_user(
    user_id: str,
    sphere_repo: Annotated[SphereRepositoryProtocol, Depends(get_sphere_repository)],
) -> dict[str, Any]:
    """
    List all spheres for a specific user.
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid user ID format") from e

    spheres = await sphere_repo.get_by_user_id(user_uuid)
    return {
        "spheres": [sphere.model_dump() for sphere in spheres],
        "total": len(spheres),
    }


@router.post("/", response_model=Sphere)
async def create_sphere(
    sphere_data: dict[str, Any],
    sphere_repo: Annotated[SphereRepositoryProtocol, Depends(get_sphere_repository)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Sphere:
    """
    Create a new sphere.
    """
    required_fields = ["user_id", "name"]
    for field in required_fields:
        if field not in sphere_data:
            raise HTTPException(
                status_code=400, detail=f"Missing required field: {field}"
            )

    try:
        user_id = (
            UUID(sphere_data["user_id"])
            if isinstance(sphere_data["user_id"], str)
            else sphere_data["user_id"]
        )
        sphere = Sphere(
            user_id=user_id,
            name=sphere_data["name"],
            description=sphere_data.get("description"),
            status=sphere_data.get("status", "Not Started"),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid sphere data: {str(e)}"
        ) from e

    await sphere_repo.save(sphere)
    await db.commit()
    return sphere


@router.put("/{sphere_id}", response_model=Sphere)
async def update_sphere(
    sphere_id: str,
    sphere_data: dict[str, Any],
    sphere_repo: Annotated[SphereRepositoryProtocol, Depends(get_sphere_repository)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Sphere:
    """
    Update an existing sphere.
    """
    try:
        sphere_uuid = UUID(sphere_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid sphere ID format") from e

    # Check if sphere exists
    existing_sphere = await sphere_repo.get_by_id(sphere_uuid)
    if not existing_sphere:
        raise HTTPException(status_code=404, detail="Sphere not found")

    # Update fields
    updates = {}
    updatable_fields = ["name", "description", "status"]
    for field in updatable_fields:
        if field in sphere_data:
            updates[field] = sphere_data[field]

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    # Create updated sphere object - use immutable pattern
    updated_sphere = existing_sphere.model_copy(update=updates)

    await sphere_repo.save(updated_sphere)
    await db.commit()
    return updated_sphere


@router.delete("/{sphere_id}")
async def delete_sphere(
    sphere_id: str,
    sphere_repo: Annotated[SphereRepositoryProtocol, Depends(get_sphere_repository)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """
    Delete a sphere.
    """
    try:
        sphere_uuid = UUID(sphere_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid sphere ID format") from e

    await sphere_repo.delete(sphere_uuid)
    await db.commit()
