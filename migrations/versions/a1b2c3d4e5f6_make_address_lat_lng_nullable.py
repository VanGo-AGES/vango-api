"""make_address_lat_lng_nullable

Revision ID: a1b2c3d4e5f6
Revises: 2670cdd23af9
Create Date: 2026-03-29 00:00:00.000000

Latitude e longitude tornam-se opcionais para permitir criação de endereços
sem geocoding prévio. O preenchimento via geocoding será feito em sprint futura.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "2670cdd23af9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("addresses", "latitude", existing_type=sa.Float(), nullable=True)
    op.alter_column("addresses", "longitude", existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    op.alter_column("addresses", "latitude", existing_type=sa.Float(), nullable=False)
    op.alter_column("addresses", "longitude", existing_type=sa.Float(), nullable=False)
