"""webhook retry and dead letter fields
Revision ID: 20261020_0003
Revises: 20261020_0002
"""
from alembic import op
import sqlalchemy as sa

revision = '20261020_0003'
down_revision = '20261020_0002'
branch_labels = None
depends_on = None

TABLE = 'acculynx_webhook_events'
INDEX = 'ix_webhook_status_next_attempt'


def _column_names():
    return {c['name'] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}


def _index_names():
    return {i['name'] for i in sa.inspect(op.get_bind()).get_indexes(TABLE)}


def upgrade():
    columns = _column_names()
    additions = [
        ('attempt_count', sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0')),
        ('next_attempt_at', sa.Column('next_attempt_at', sa.DateTime(), nullable=True)),
        ('last_error', sa.Column('last_error', sa.Text(), nullable=True)),
        ('dead_lettered_at', sa.Column('dead_lettered_at', sa.DateTime(), nullable=True)),
    ]
    for name, column in additions:
        if name not in columns:
            op.add_column(TABLE, column)
            columns.add(name)
    if INDEX not in _index_names():
        op.create_index(INDEX, TABLE, ['status', 'next_attempt_at'])


def downgrade():
    if INDEX in _index_names():
        op.drop_index(INDEX, table_name=TABLE)
    columns = _column_names()
    for name in ['dead_lettered_at', 'last_error', 'next_attempt_at', 'attempt_count']:
        if name in columns:
            op.drop_column(TABLE, name)
            columns.remove(name)
