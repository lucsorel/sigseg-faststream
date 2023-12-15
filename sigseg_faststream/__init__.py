from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue


sigseg_broker = RabbitBroker('amqp://guest:guest@localhost:5672/')
sigseg_exchange = RabbitExchange('sigseg.x', durable=True)
sigseg_queue = RabbitQueue('sigseg.q', durable=True)
