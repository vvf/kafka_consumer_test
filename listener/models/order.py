from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from models.base import Model, SurrogatePK


def now_as_int():
    return datetime.now().timestamp()


class Order(SurrogatePK, Model):
    __tablename__ = 'orders'

    status = Column(String(20), nullable=False, default="CREATED")
    comment = Column(String(1024), nullable=True)
    src_station = Column(String(100), nullable=True)
    dest_station = Column(String(100), nullable=True)
    created_ts = Column(Integer, default=now_as_int)
    created = Column(DateTime, default=datetime.now)

    generated = Column(DateTime, nullable=True)
    processed_by = Column(UUID, nullable=True)
    message_meta_data = Column(JSONB, nullable=True)

    sendings = relationship('Sending', backref='order')
