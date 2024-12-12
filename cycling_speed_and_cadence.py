from dataclasses import dataclass
import ssl
import rich
import struct
import paho.mqtt.client as mqtt


@dataclass
class SpeedData:
    speed: float


@dataclass
class CadenceData:
    cadence: float


def serialize_speed_data(speed_data: SpeedData) -> bytes:
    data_bytes = struct.pack(">B", 4)
    data_bytes += struct.pack(">f", speed_data.speed)
    return data_bytes


def serialize_cadence_data(cadence_data: CadenceData) -> bytes:
    data_bytes = struct.pack(">B", 5)
    data_bytes += struct.pack(">f", cadence_data.cadence)
    return data_bytes


class CSCSensor:
    def __init__(self) -> None:
        self.speed = 0.0

        self.wheel_revolutions = 0
        self.wheel_revolutions_event_time = 0
        self.previous_wheel_revolutions = 0
        self.previous_wheel_revolutions_event_time = 0

        self.crank_revolutions = 0
        self.crank_revolutions_event_time = 0
        self.previous_crank_revolutions = 0
        self.previous_crank_revolutions_event_time = 0

        self.wheel_circumference = 2.146

        self.wheel_repeat_count = 0
        self.wheel_repeat_limit = 7

        self.crank_repeat_count = 0
        self.crank_repeat_limit = 3

        self.connect()

    def connect(self) -> None:
        def on_connect(client, userdata, flags, reason_code, properties):
            rich.print(
                f"[bold blue]Connected to MQTT broker with code {reason_code}[/bold blue]"
            )

        username = "084bf859-2206-4cc6-ba82-98b4a1b898c4"
        password = "$argon2id$v=19$m=65536,t=3,p=4$kuXO8SAFS6mO27ArtliYXA$yQHlGSi6zQsDKfeJUtefrNMIhPV3ge8NYuQopimNp14"

        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.username_pw_set(username, password)
        self.mqtt_client.on_connect = on_connect

        self.mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.mqtt_client.tls_insecure_set(True)

        self.mqtt_client.connect("mqtt.traek.fit", 8883, 60)
        self.mqtt_client.loop_start()

    def parse(self, data: bytearray) -> None:
        flags = data[0]

        wheel_revolutions_data_present = (flags & 0x01) > 0
        crank_revolutions_data_present = (flags & 0x02) > 0

        index = 1

        if wheel_revolutions_data_present:
            self.wheel_revolutions = int.from_bytes(
                data[index : index + 4], byteorder="little"
            )
            index += 4
            self.wheel_revolutions_event_time = int.from_bytes(
                data[index : index + 2], byteorder="little"
            )
            index += 2

            # rich.print(f"Wheel Revolutions: {self.wheel_revolutions}, Wheel Revolutions Event Time: {self.wheel_revolutions_event_time}")
            self.update_speed()

        if crank_revolutions_data_present:
            self.crank_revolutions = int.from_bytes(
                data[index : index + 2], byteorder="little"
            )
            index += 2
            self.crank_revolutions_event_time = int.from_bytes(
                data[index : index + 2], byteorder="little"
            )
            index += 2

            # rich.print(f"Crank Revolutions: {self.crank_revolutions}, Crank Revolutions Event Time: {self.crank_revolutions_event_time}")
            self.update_cadence()

    def update_speed(self):
        # First valid update, no previous data to compare
        if (
            self.previous_wheel_revolutions == 0
            or self.previous_wheel_revolutions_event_time == 0
        ):
            self.previous_wheel_revolutions = self.wheel_revolutions
            self.previous_wheel_revolutions_event_time = (
                self.wheel_revolutions_event_time
            )
            return

        # Handle the case where event time resets (e.g., overflows or rollovers)
        if (
            self.wheel_revolutions_event_time
            < self.previous_wheel_revolutions_event_time
        ):
            rich.print("Event time reset detected. Skipping speed calculation.")

            self.previous_wheel_revolutions = self.wheel_revolutions
            self.previous_wheel_revolutions_event_time = (
                self.wheel_revolutions_event_time
            )

            return

        if (
            self.wheel_revolutions == self.previous_wheel_revolutions
            or self.wheel_revolutions_event_time
            == self.previous_wheel_revolutions_event_time
        ):
            if self.wheel_repeat_count >= self.wheel_repeat_limit:
                self.speed = 0.0
                self.on_speed_update(self.speed)
                self.wheel_repeat_count = 0
            self.wheel_repeat_count += 1
            return

        self.wheel_repeat_count = 0

        time_difference = (
            self.wheel_revolutions_event_time
            - self.previous_wheel_revolutions_event_time
        ) / 1024.0
        wheel_revolutions_difference = (
            self.wheel_revolutions - self.previous_wheel_revolutions
        )

        speed_mps = (
            wheel_revolutions_difference * self.wheel_circumference
        ) / time_difference
        speed_kmph = speed_mps * 3.6

        self.on_speed_update(speed_kmph)

        self.previous_wheel_revolutions = self.wheel_revolutions
        self.previous_wheel_revolutions_event_time = self.wheel_revolutions_event_time

    def update_cadence(self):
        # First valid update, no previous data to compare
        if (
            self.previous_crank_revolutions == 0
            or self.previous_crank_revolutions_event_time == 0
        ):
            self.previous_crank_revolutions = self.crank_revolutions
            self.previous_crank_revolutions_event_time = (
                self.crank_revolutions_event_time
            )
            return

        # Handle the case where event time resets (e.g., overflows or rollovers)
        if (
            self.crank_revolutions_event_time
            < self.previous_crank_revolutions_event_time
        ):
            rich.print("Event time reset detected. Skipping cadence calculation.")

            self.previous_crank_revolutions = self.crank_revolutions
            self.previous_crank_revolutions_event_time = (
                self.crank_revolutions_event_time
            )

            return

        if (
            self.crank_revolutions == self.previous_crank_revolutions
            or self.crank_revolutions_event_time
            == self.previous_crank_revolutions_event_time
        ):
            if self.crank_repeat_count >= self.crank_repeat_limit:
                self.cadence = 0
                self.on_cadence_update(self.cadence)
                self.crank_repeat_count = 0
            self.crank_repeat_count += 1
            return

        self.crank_repeat_count = 0

        time_difference = (
            self.crank_revolutions_event_time
            - self.previous_crank_revolutions_event_time
        ) / 1024.0
        crank_revolutions_difference = (
            self.crank_revolutions - self.previous_crank_revolutions
        )

        cadence = (crank_revolutions_difference / time_difference) * 60

        self.on_cadence_update(cadence)

        self.previous_crank_revolutions = self.crank_revolutions
        self.previous_crank_revolutions_event_time = self.crank_revolutions_event_time

    def on_speed_update(self, speed: float):
        rich.print(f"Speed: {speed} km/h")
        payload = serialize_speed_data(SpeedData(speed=speed))
        self.mqtt_client.publish("rooms/26", payload, qos=2)

    def on_cadence_update(self, cadence: float):
        rich.print(f"Cadence: {cadence} rpm")
        payload = serialize_cadence_data(CadenceData(cadence=cadence))
        self.mqtt_client.publish("rooms/26", payload, qos=2)
