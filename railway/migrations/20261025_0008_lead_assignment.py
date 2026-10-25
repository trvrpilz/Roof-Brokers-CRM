from alembic import op
import sqlalchemy as sa

revision = '20261025_0008'
down_revision = '20261025_0007'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('leads', sa.Column('assigned_user_id', sa.String(), nullable=True))
    op.create_index('ix_leads_assigned_user_id', 'leads', ['assigned_user_id'])
    op.create_foreign_key('fk_leads_assigned_user_id_users', 'leads', 'users', ['assigned_user_id'], ['id'], ondelete='SET NULL')
    op.execute("""
        UPDATE leads l
        SET assigned_user_id = (
            SELECT u.id
            FROM users u
            WHERE u.company_id = l.company_id
              AND upper(u.role) = 'OWNER'
              AND u.active = true
            ORDER BY u.id
            LIMIT 1
        )
        WHERE l.assigned_user_id IS NULL
    """)


def downgrade():
    op.drop_constraint('fk_leads_assigned_user_id_users', 'leads', type_='foreignkey')
    op.drop_index('ix_leads_assigned_user_id', table_name='leads')
    op.drop_column('leads', 'assigned_user_id')
