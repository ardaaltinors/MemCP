from sqlalchemy import Column, String, Boolean, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.db.models.custom_base import CustomBase


class ServerProperty(CustomBase):
    __tablename__ = "server_properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    arguments: Mapped[dict] = mapped_column(JSON, nullable=True, default={})
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)