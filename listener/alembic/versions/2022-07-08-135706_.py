"""empty message

Revision ID: a414a9ea88a0
Revises: 649ab12c86da
Create Date: 2022-07-08 13:57:06.522074

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a414a9ea88a0'
down_revision = '649ab12c86da'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('processed_by', postgresql.UUID(), nullable=True))
    op.add_column('orders', sa.Column('message_meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('orders', 'message_meta_data')
    op.drop_column('orders', 'processed_by')
    # ### end Alembic commands ###
