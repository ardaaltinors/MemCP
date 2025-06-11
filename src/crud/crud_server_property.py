from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.models.server_property import ServerProperty
from src.exceptions import RecordNotFoundError


async def get_server_property_by_name(db: AsyncSession, name: str) -> Optional[ServerProperty]:
    """Get a server property by name."""
    stmt = select(ServerProperty).where(ServerProperty.name == name)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_server_property_value(db: AsyncSession, name: str, default: Optional[str] = None) -> Optional[str]:
    """Get the value of a server property by name, return default if not found or not active."""
    property = await get_server_property_by_name(db, name)
    if property and property.active:
        return property.value
    return default


async def is_registration_active(db: AsyncSession) -> bool:
    """Check if user registration is active."""
    value = await get_server_property_value(db, "is_registration_active", "false")
    return value.lower() == "true"


async def update_server_property(db: AsyncSession, name: str, value: str, description: Optional[str] = None) -> ServerProperty:
    """Update a server property value."""
    property = await get_server_property_by_name(db, name)
    if not property:
        raise RecordNotFoundError(table_name="server_properties", record_id=name)
    
    property.value = value
    if description is not None:
        property.description = description
    
    await db.commit()
    await db.refresh(property)
    return property


async def create_server_property(
    db: AsyncSession,
    name: str,
    value: str,
    description: Optional[str] = None,
    active: bool = True,
    arguments: Optional[dict] = None
) -> ServerProperty:
    """Create a new server property."""
    property = ServerProperty(
        name=name,
        value=value,
        description=description,
        active=active,
        arguments=arguments or {}
    )
    db.add(property)
    await db.commit()
    await db.refresh(property)
    return property