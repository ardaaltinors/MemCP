"""Merge heads: server_properties + oauth_accounts

Revision ID: aa0b5a1bb1f1
Revises: 7863b196ef92, 9f1a2c3d4e5f
Create Date: 2025-11-08 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa0b5a1bb1f1'
down_revision: Union[str, None] = ('7863b196ef92', '9f1a2c3d4e5f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge point; no schema changes."""
    pass


def downgrade() -> None:
    """Unmerge not supported; no-op."""
    pass

