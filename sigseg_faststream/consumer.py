from faststream import FastStream, Logger

from sigseg_faststream import sigseg_broker, sigseg_queue


consume = FastStream(sigseg_broker)

@sigseg_broker.subscriber(sigseg_queue)
async def base_handler1(logger: Logger, message: dict):
    logger.info('Received message %s', message)

    if message.get('sigseg'):
        # raise ValueError('should not cause a sigseg')

        # this import causes the segmentation fault and leaves the consumer in a defunct state
        from csigseg.sigseg import DLL_TYPE
        print(DLL_TYPE)