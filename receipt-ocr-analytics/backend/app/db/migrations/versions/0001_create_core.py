from alembic import op
import sqlalchemy as sa

revision = '0001_create_core'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'vendors',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    op.create_table(
        'receipts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('vendor_id', sa.Integer(), sa.ForeignKey('vendors.id', ondelete='SET NULL')),
        sa.Column('d', sa.Date(), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False, server_default='USD'),
        sa.Column('total', sa.Numeric(12,2), nullable=False, server_default='0'),
        sa.Column('raw_text', sa.Text()),
        sa.Column('image_path', sa.String(length=512)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )

    op.create_table(
        'receipt_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('receipt_id', sa.Integer(), sa.ForeignKey('receipts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('qty', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Numeric(12,2), nullable=False, server_default='0'),
        sa.Column('line_total', sa.Numeric(12,2), nullable=False, server_default='0'),
        sa.Column('category', sa.String(length=64), nullable=False, server_default='other'),
    )

def downgrade():
    op.drop_table('receipt_items')
    op.drop_table('receipts')
    op.drop_table('vendors')
