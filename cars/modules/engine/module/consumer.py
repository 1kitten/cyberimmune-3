import os
import json
import threading
import time
from uuid import uuid4
from confluent_kafka import Consumer, OFFSET_BEGINNING
import random
from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")


def send_to_engine_controller(id, details):
    details["deliver_to"] = "engine_controller"
    proceed_to_deliver(id, details)


def handle_event(id, details_str):
    """ Обработчик входящих в модуль задач. """
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: str = details.get("data")
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    if operation == "send_current_engine_state":
        send_to_engine_controller(id, details)


def consumer_job(args, config):
    consumer = Consumer(config)

    def reset_offset(verifier_consumer, partitions):
        if not args.reset:
            return

        for p in partitions:
            p.offset = OFFSET_BEGINNING
        verifier_consumer.assign(partitions)

    topic = MODULE_NAME
    consumer.subscribe([topic], on_assign=reset_offset)

    try:
        while True:
            time.sleep(30)

            try:
                handle_event(uuid4(), json.dumps(dict(
                    source=MODULE_NAME,
                    deliver_to="engine_controller",
                    operation="send_current_engine_state",
                    data={
                        "is_working": bool(random.randint(0,1)),
                        "exactly": bool(random.randint(0,1))
                    }
                )))
            except Exception as e:
                print(f"[error] Malformed event received from " \
                    f"topic {topic}. {e}")
    except KeyboardInterrupt:
        pass

    finally:
        consumer.close()

def start_consumer(args, config):
    print(f'{MODULE_NAME}_consumer started')
    threading.Thread(target=lambda: consumer_job(args, config)).start()