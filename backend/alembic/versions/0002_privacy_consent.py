"""Store required registration consent timestamps."""
from alembic import op
import sqlalchemy as sa

revision = "0002_privacy_consent"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "terms_accepted_at" not in columns:
        op.add_column("users", sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True))
    if "privacy_accepted_at" not in columns:
        op.add_column("users", sa.Column("privacy_accepted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "privacy_accepted_at" in columns:
        op.drop_column("users", "privacy_accepted_at")
    if "terms_accepted_at" in columns:
        op.drop_column("users", "terms_accepted_at")