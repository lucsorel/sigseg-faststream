from time import sleep

from faststream import FastStream, Logger

from sigseg_faststream import sigseg_broker, sigseg_exchange


produce = FastStream(sigseg_broker)

@produce.after_startup
async def publish(logger: Logger):
        messages = [
            {'id': 1, 'sigseg': False},
            {'id': 2, 'sigseg': True}, # this message will cause a segmentation fault in the consumer
            {'id': 3, 'sigseg': False},
        ]

        for message in messages:
            logger.info('Sending message %s', message)
            await sigseg_broker.publish(message, exchange=sigseg_exchange)
            sleep(0.5)
