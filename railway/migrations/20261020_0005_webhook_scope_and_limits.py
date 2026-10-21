"""Scope webhook event idempotency to each AccuLynx connection.

Revision ID: 20261020_0005
Revises: 20261020_0004
"""
from alembic import op
import sqlalchemy as sa

revision = '20261020_0005'
down_revision = '20261020_0004'
branch_labels = None
depends_on = None

TABLE = 'acculynx_webhook_events'
OLD = 'uq_acculynx_webhook_event'
NEW = 'uq_acculynx_webhook_connection_event'


def _unique_names():
    return {c['name'] for c in sa.inspect(op.get_bind()).get_unique_constraints(TABLE) if c.get('name')}


def upgrade():
    names = _unique_names()
    if NEW in names:
        return
    if OLD in names:
        op.drop_constraint(OLD, TABLE, type_='unique')
    op.create_unique_constraint(NEW, TABLE, ['connection_id', 'event_id'])


def downgrade():
    names = _unique_names()
    if OLD in names:
        return
    if NEW in names:
        op.drop_constraint(NEW, TABLE, type_='unique')
    op.create_unique_constraint(OLD, TABLE, ['event_id'])
