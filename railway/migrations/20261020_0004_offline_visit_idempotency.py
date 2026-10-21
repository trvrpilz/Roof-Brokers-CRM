"""offline canvass visit idempotency
Revision ID: 20261020_0004
Revises: 20261020_0003
"""
from alembic import op
import sqlalchemy as sa

revision = '20261020_0004'
down_revision = '20261020_0003'
branch_labels = None
depends_on = None

TABLE = 'canvass_visits'
COLUMN = 'client_action_id'
INDEX = 'ix_canvass_visits_client_action_id'


def _column_names():
    return {c['name'] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}


def _index_names():
    return {i['name'] for i in sa.inspect(op.get_bind()).get_indexes(TABLE)}


def upgrade():
    if COLUMN not in _column_names():
        op.add_column(TABLE, sa.Column(COLUMN, sa.String(), nullable=True))
    if INDEX not in _index_names():
        op.create_index(INDEX, TABLE, [COLUMN], unique=True)


def downgrade():
    if INDEX in _index_names():
        op.drop_index(INDEX, table_name=TABLE)
    if COLUMN in _column_names():
        op.drop_column(TABLE, COLUMN)
