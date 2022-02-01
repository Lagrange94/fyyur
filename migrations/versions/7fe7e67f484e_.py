"""empty message

Revision ID: 7fe7e67f484e
Revises: 69edd26c9be3
Create Date: 2022-01-30 19:16:25.767430

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7fe7e67f484e'
down_revision = '69edd26c9be3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Venue', sa.Column('genres', sa.String(length=120), nullable=True))
    op.add_column('Venue', sa.Column('website_link', sa.String(length=500), nullable=True))
    op.add_column('Venue', sa.Column('seeking_description', sa.String(length=1000), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Venue', 'seeking_description')
    op.drop_column('Venue', 'website_link')
    op.drop_column('Venue', 'genres')
    # ### end Alembic commands ###
