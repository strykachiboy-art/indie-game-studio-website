"""add profile fields (bio, avatar) to users

Revision ID: 3f2c9a7d1b44
Revises: 57bded946b70
"""
from alembic import op
import sqlalchemy as sa

revision = "3f2c9a7d1b44"
down_revision = "57bded946b70"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("bio", sa.String(length=280), nullable=True))
        batch_op.add_column(sa.Column("avatar_data", sa.LargeBinary(), nullable=True))
        batch_op.add_column(
            sa.Column("avatar_version", sa.Integer(), nullable=False, server_default="0")
        )


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("avatar_version")
        batch_op.drop_column("avatar_data")
        batch_op.drop_column("bio")
