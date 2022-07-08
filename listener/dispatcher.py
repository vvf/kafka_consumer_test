import os
import uuid
from datetime import datetime

from aiokafka import ConsumerRecord
from bs4 import BeautifulSoup

from models.base import get_session
from models.order import Order
from models.sending import Sending

consumer_id = str(uuid.uuid4())


def create_sending(sending):
    return Sending(
        dest_station=sending.destination.text
    )


def create_order(db_session, order_tag, message_meta_data):
    order = Order(
        status=order_tag.status.text,
        comment=order_tag.comment.text,
        src_station=order_tag.source.text,
        dest_station=order_tag.destination.text,
        generated=datetime.fromisoformat(order_tag.generated.text) if order_tag.generated is not None else None,
        message_meta_data=message_meta_data,
        processed_by=consumer_id,
        sendings=[
            create_sending(sending)
            for sending in order_tag.sendings.find_all('sending')
        ]
    )
    db_session.add(order)
    return order


async def dispatch(message: ConsumerRecord):
    db_session = get_session()
    soup = BeautifulSoup(message.value, 'lxml')
    message_meta = {
        k: getattr(message, k)
        for k in ('timestamp', "partition", "offset")
    }
    async with db_session.begin():
        for order_tag in soup.orders.find_all('order'):
            create_order(db_session, order_tag, message_meta)
