import asyncio
import logging
import os
import random
import string
import time
from datetime import datetime
from typing import Iterable, List, Optional

from aiokafka import AIOKafkaProducer
from pydantic import BaseSettings

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("listener.producer" if __name__ == '__main__' else __name__)
logging.getLogger('listener').setLevel(logging.DEBUG)

pid = os.getpid()


class ProducerSettings(BaseSettings):
    BATCH_SIZE: Optional[int] = 50
    BATCHES_COUNT: Optional[int] = 20
    ORDERS_PER_MESSAGE: Optional[int] = 1
    SENDINGS_PER_ORDER: Optional[int] = 5


producer_settings = ProducerSettings()


def generate_random_str(l=32):
    return ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=l))


def generate_payload(batch_id, message_id):
    return ({
        "generated": datetime.now().isoformat(),
        "status": "TEST",
        "comment": f"PID: {pid}; Batch {batch_id}; Message {message_id}; order {order_id};\n\n{generate_random_str(512)}",
        "source": generate_random_str(80),
        "destination": generate_random_str(80),
        "sendings": (
            {
                "dest": f"P{pid}B{batch_id}M{message_id}O{order_id}S{send_id}-{generate_random_str(12)}"
            }
            for send_id in range(producer_settings.SENDINGS_PER_ORDER)
        )
    } for order_id in range(producer_settings.ORDERS_PER_MESSAGE))


async def async_start():
    producer_config = {}
    if settings.KAFKA_USERNAME and settings.KAFKA_PASSWORD:
        producer_config.update({
            "sasl_mechanism": settings.KAFKA_SASL_MECHANISM or "PLAIN",
            "sasl_plain_username": settings.KAFKA_USERNAME or '',
            "sasl_plain_password": settings.KAFKA_PASSWORD or '',
            "security_protocol": "PLAINTEXT",
            "bootstrap_servers": settings.KAFKA_BROKERS
        })
        if settings.KAFKA_SECURITY_PROTOCOL:
            producer_config["security_protocol"] = settings.KAFKA_SECURITY_PROTOCOL

    producer = AIOKafkaProducer(
        **producer_config
    )
    await producer.start()
    start_ts = time.monotonic()
    print("-" * 20)
    try:
        for batch_id in range(producer_settings.BATCHES_COUNT):
            logger.info(f"started batch {batch_id}")
            await asyncio.gather(*[
                send_message(producer, generate_payload(batch_id, message_id))
                for message_id in range(producer_settings.BATCH_SIZE)
            ])
    finally:
        await producer.stop()
    stop_ts = time.monotonic()
    logger.info(f"execute time - {stop_ts - start_ts}")


def build_sendings(sendings: List[dict]):
    return ''.join(f"""<SENDING><DESTINATION>{sending['dest']}</DESTINATION></SENDING>"""
                   for sending in sendings)


def build_xml_message(message: Iterable[dict]) -> bytes:
    orders_xml = ''.join(f'''
    <ORDER>
        <STATUS>{order['status']}</STATUS>
        <COMMENT>{order['comment']}</COMMENT>
        <SOURCE>{order['source']}</SOURCE>
        <DESTINATION>{order['destination']}</DESTINATION>
        <GENERATED>{order['generated']}</GENERATED>
        <SENDINGS>{build_sendings(order['sendings'])}</SENDINGS>        
    </ORDER>
''' for order in message)
    return f'<ORDERS>{orders_xml}</ORDERS>'.encode()


async def send_message(producer: AIOKafkaProducer, message: Iterable[dict]):
    try:
        topic = settings.KAFKA_TOPIC
        message = build_xml_message(message)

        # logger.info(f'Send message to scoring: topic={topic}, message_len={len(message)}')
        await producer.send(topic, message)
    except Exception:
        logger.exception('Failed send message to Kafka')


def main():
    global pid
    loop = asyncio.get_event_loop()
    pid = generate_random_str(5) + ' '

    try:
        loop.run_until_complete(async_start())
    finally:
        loop.stop()


if __name__ == '__main__':
    # logger.addHandler(logging.StreamHandler())
    logger.setLevel("DEBUG")
    n = producer_settings.ORDERS_PER_MESSAGE * producer_settings.BATCH_SIZE * producer_settings.BATCHES_COUNT
    logger.info(f"Each producer create - {n} rows")
    main()
