import asyncio
import logging
import os
import sys
from random import randint
from typing import Any, Callable, Coroutine

from aiokafka import AIOKafkaConsumer, ConsumerRebalanceListener, ConsumerRecord

from config import settings
from dispatcher import consumer_id, dispatch

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("listener.runner" if __name__ == '__main__' else __name__)
# logging.getLogger('listener').setLevel(logging.DEBUG)

Dispatcher = Callable[[ConsumerRecord], Coroutine[Any, Any, None]]
_consumer_lock = asyncio.Lock()


class KafkaRebalanceListener(ConsumerRebalanceListener):
    async def on_partitions_revoked(self, revoked):
        # lock revoking until current processing done and commit new position
        async with _consumer_lock:
            logger.info("Kafka rebalancing. Revoke %s", revoked)

    async def on_partitions_assigned(self, revoked):
        pass


async def process_message(message: ConsumerRecord):
    logger.info("Got message from topic %s, offset=%s, key=%s", message.topic, message.offset, message.key,
                )
    from models.base import run_with_db

    try:
        await run_with_db(dispatch(message))

    except KeyboardInterrupt as error:
        """
        Если тебе нужно пояснение к этой ошибке, то увольняйся и освободи место тому,
        кто этого действительно заслуживает.
        """
        logger.info("got KeyboardInterrupt, break the loop")
        raise error


async def consume_loop(consumer: AIOKafkaConsumer):
    logger.info("Start consumer loop")

    while True:
        try:
            result = await consumer.getmany(timeout_ms=settings.KAFKA_TIMEOUT_MS,
                                            max_records=settings.KAFKA_MAX_RECORDS)
            for tp, messages in result.items():
                if messages:
                    tasks = [asyncio.create_task(process_message(message)) for message in messages]
                    await asyncio.gather(*tasks)
                    if not consumer._enable_auto_commit:
                        await consumer.commit({tp: messages[-1].offset + 1})
                        logger.info(
                            f"Commit {len(messages)} messages: topic={tp.topic}, partition={tp.partition}. "
                            f"Last message: offset={messages[-1].offset}."
                        )
        except KeyboardInterrupt:
            break

    logger.warning("Consumer loop finished")


async def async_start():
    consumer_config = {}
    if settings.KAFKA_USERNAME and settings.KAFKA_PASSWORD:
        consumer_config.update({
            "sasl_mechanism": settings.KAFKA_SASL_MECHANISM or "PLAIN",
            "sasl_plain_username": settings.KAFKA_USERNAME or '',
            "sasl_plain_password": settings.KAFKA_PASSWORD or '',
            "security_protocol": "PLAINTEXT"
        })
        if settings.KAFKA_SECURITY_PROTOCOL:
            consumer_config["security_protocol"] = settings.KAFKA_SECURITY_PROTOCOL
    consumer = AIOKafkaConsumer(
        bootstrap_servers=settings.KAFKA_BROKERS.split(","),
        group_id=settings.KAFKA_GROUP or "0",
        client_id=f"listener-{consumer_id}",
        enable_auto_commit=False,
        **consumer_config
    )
    consumer.subscribe(
        settings.KAFKA_TOPIC.split(),
        listener=KafkaRebalanceListener()
    )
    logger.info("Connect consumer")
    await consumer.start()

    logger.info("Start consumer")

    try:
        await consume_loop(consumer)
    finally:
        await consumer.stop()


def main():
    loop = asyncio.get_event_loop()
    # if '-v' in sys.argv:
    #     print("DEBUG logging")
    #     logger.setLevel(logging.DEBUG)
    #     logging.basicConfig(level=logging.INFO)
    # else:
    logger.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)
    try:
        loop.run_until_complete(async_start())
    finally:
        loop.stop()


if __name__ == '__main__':
    main()
