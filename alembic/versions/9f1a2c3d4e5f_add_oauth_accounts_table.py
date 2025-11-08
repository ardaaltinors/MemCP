"""Add OAuth accounts table

Revision ID: 9f1a2c3d4e5f
Revises: de7cfeb9cd83
Create Date: 2025-11-08 19:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f1a2c3d4e5f'
down_revision: Union[str, None] = 'de7cfeb9cd83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'oauth_accounts',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('access_token', sa.String(), nullable=True),
        sa.Column('refresh_token', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oauth_accounts_id'), 'oauth_accounts', ['id'], unique=False)
    op.create_index(op.f('ix_oauth_accounts_provider'), 'oauth_accounts', ['provider'], unique=False)
    op.create_index(op.f('ix_oauth_accounts_subject'), 'oauth_accounts', ['subject'], unique=False)
    op.create_index(op.f('ix_oauth_accounts_email'), 'oauth_accounts', ['email'], unique=False)
    op.create_unique_constraint('uq_oauth_provider_subject', 'oauth_accounts', ['provider', 'subject'])


def downgrade() -> None:
    op.drop_constraint('uq_oauth_provider_subject', 'oauth_accounts', type_='unique')
    op.drop_index(op.f('ix_oauth_accounts_email'), table_name='oauth_accounts')
    op.drop_index(op.f('ix_oauth_accounts_subject'), table_name='oauth_accounts')
    op.drop_index(op.f('ix_oauth_accounts_provider'), table_name='oauth_accounts')
    op.drop_index(op.f('ix_oauth_accounts_id'), table_name='oauth_accounts')
    op.drop_table('oauth_accounts')

