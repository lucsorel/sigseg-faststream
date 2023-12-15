# Provoke a segmentation fault in a FastStream consumer

## Create a segmentation fault by importing a library
The C code in [csigseg/sigseg.c](csigseg/sigseg.c):

```c
#include <iostream>
#include <stdio.h>

int *a;
// this causes the segmentation fault
int b = *a;

int main() {}
```

Compile the library:

```sh
cd csigseg
g++ -fPIC -shared -o libsigseg.so sigseg.c
```

The [csigseg/sigseg.py](csigseg/sigseg.py) module imports the C library, which causes a segmentation fault.

```python
from ctypes import cdll

DLL_TYPE = cdll.LoadLibrary('csigseg/libsigseg.so')

print('a segmentation fault should have occurred when importing libsigseg.so')
```

Test the segmentation fault principle:

```sh
# by executing script
python csigseg/sigseg.py
[1]    49168 segmentation fault (core dumped)  python csigseg/sigseg.py

# by importing the module
python
Python 3.11.3 (main, Oct 20 2023, 14:30:20) [GCC 11.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from csigseg import sigseg
[1]    50487 segmentation fault (core dumped)  python
```

## Start and configure a rabbitmq instance

```sh
# starts the cluster in one terminal
docker run --rm -p 5672:5672 -p 15672:15672 --name sigseg-mq rabbitmq:3.12-management

# configures the cluster (exchange, queue, binding) in another terminal
docker exec sigseg-mq rabbitmqadmin declare exchange name=sigseg.x type=direct
docker exec sigseg-mq rabbitmqadmin declare queue name=sigseg.q durable=true
docker exec sigseg-mq rabbitmqadmin declare binding source=sigseg.x destination=sigseg.q destination_type=queue
```

The broker, exchange and queue Python objects are defined in [sigseg_faststream/__init__.py](sigseg_faststream/__init__.py), ready to be imported and used in the producer and consumer applications:

```python
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue

sigseg_broker = RabbitBroker('amqp://guest:guest@localhost:5672/')
sigseg_exchange = RabbitExchange('sigseg.x', durable=True)
sigseg_queue = RabbitQueue('sigseg.q', durable=True)
```

## Start the producer

The code of the producer application:

```python
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
```

The command to start the producer:

```sh
# with poetry
poetry run faststream run sigseg_faststream.producer:produce

# in an activated virtual environment
faststream run sigseg_faststream.producer:produce

# 2023-12-15 16:27:05,371 INFO     - FastStream app starting...
# 2023-12-15 16:27:05,383 INFO     -      |      |            - Sending message {'id': 1, 'sigseg': False}
# 2023-12-15 16:27:05,886 INFO     -      |      |            - Sending message {'id': 2, 'sigseg': True}
# 2023-12-15 16:27:06,387 INFO     -      |      |            - Sending message {'id': 3, 'sigseg': False}
# 2023-12-15 16:27:06,889 INFO     - FastStream app started successfully! To exit, press CTRL+C
```

## Dynamically import the sigseg library in a FastStream consumer

## Start the consumer

The code of the consumer application:

```python
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
```

The command to start the consumer:

```sh
# with poetry
poetry run faststream run sigseg_faststream.consumer:consume

# in an activated virtual environment
faststream run sigseg_faststream.consumer:consume

# 2023-12-15 16:29:32,158 INFO     - FastStream app starting...
# 2023-12-15 16:29:32,171 INFO     - default | sigseg.q |            - `BaseHandler1` waiting for messages
# 2023-12-15 16:29:32,175 INFO     - FastStream app started successfully! To exit, press CTRL+C
# 2023-12-15 16:29:32,176 INFO     - default | sigseg.q | 4892031fd8 - Received
# 2023-12-15 16:29:32,177 INFO     - default | sigseg.q | eb4ef4e3b4 - Received
# 2023-12-15 16:29:32,178 INFO     - default | sigseg.q | c1f73a13b7 - Received
# 2023-12-15 16:29:32,181 INFO     - default | sigseg.q | 4892031fd8 - Received message {'id': 1, 'sigseg': False}
# 2023-12-15 16:29:32,183 INFO     - default | sigseg.q | eb4ef4e3b4 - Received message {'id': 2, 'sigseg': True}
# [1]    71371 segmentation fault (core dumped)  poetry run faststream run sigseg_faststream.consumer:consume
```

The consumer is stopped and the next message is not handled.
