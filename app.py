import json
import threading
import time
from typing import Callable

from cycling_speed_and_cadence import CSCSensor


class Processor:
    def __init__(self, json_file: str) -> None:
        self.json_file = json_file
        self.data = self.load_json_data()

    def load_json_data(self) -> dict:
        with open(self.json_file, "r") as f:
            return json.load(f)

    def convert_value_to_bytearray(self, value: str) -> bytearray:
        return bytearray.fromhex(value.replace("-", ""))

    def schedule_tasks(self, target_function: Callable[[bytearray], None]) -> None:
        last_timestamp = 0
        for entry in self.data:
            timestamp = entry["timestamp"]
            value = entry["value"]
            byte_data = self.convert_value_to_bytearray(value)

            wait_time = timestamp - last_timestamp
            if wait_time > 0:
                time.sleep(wait_time)

            target_function(byte_data)
            last_timestamp = timestamp


if __name__ == "__main__":
    cscSensor = CSCSensor()

    wheel_processor = Processor("data/output/wheel/1.json")
    crank_processor = Processor("data/output/crank/1.json")

    wheel_thread = threading.Thread(
        target=wheel_processor.schedule_tasks, args=(cscSensor.parse,)
    )
    crank_thread = threading.Thread(
        target=crank_processor.schedule_tasks, args=(cscSensor.parse,)
    )

    wheel_thread.start()
    crank_thread.start()

    wheel_thread.join()
    crank_thread.join()
