from sqlalchemy import Column, ForeignKey, String

from models.base import Model, SurrogatePK
from models.order import Order


class Sending(SurrogatePK, Model):
    __tablename__ = 'sendings'

    order_id = Column(
        ForeignKey(f"orders.id"),
        nullable=False
    )
    dest_station = Column(String(100), nullable=False)
