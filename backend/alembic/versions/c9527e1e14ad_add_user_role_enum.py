"""add user role enum

Revision ID: c9527e1e14ad
Revises: 7bdc19842c86
Create Date: 2026-08-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9527e1e14ad"
down_revision: Union[str, Sequence[str], None] = "7bdc19842c86"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role_enum = sa.Enum(
    "ADMIN",
    "ATTENDANT",
    "DISPATCHER",
    "RIDER",
    name="userrole",
)


def upgrade() -> None:
    # Create the PostgreSQL enum type first.
    user_role_enum.create(op.get_bind(), checkfirst=True)

    # Change the users.role column from VARCHAR to the enum.
    op.alter_column(
        "users",
        "role",
        existing_type=sa.VARCHAR(length=20),
        type_=user_role_enum,
        existing_nullable=False,
        postgresql_using="role::userrole",
    )


def downgrade() -> None:
    # Change the enum column back to VARCHAR.
    op.alter_column(
        "users",
        "role",
        existing_type=user_role_enum,
        type_=sa.VARCHAR(length=20),
        existing_nullable=False,
    )

    # Remove the PostgreSQL enum type.
    user_role_enum.drop(op.get_bind(), checkfirst=True)