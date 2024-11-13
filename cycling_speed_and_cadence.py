import rich

class CSCSensor:
    def __init__(self) -> None:
        self.speed = 0.0

        self.wheel_revolutions = 0
        self.wheel_revolutions_event_time = 0
        self.previous_wheel_revolutions = 0
        self.previous_wheel_revolutions_event_time = 0

        self.crank_revolutions = 0
        self.crank_revolutions_event_time = 0
        self.last_crank_revolutions = 0
        self.last_crank_revolutions_event_time = 0

        self.wheel_circumference = 2.146

        self.wheel_repeat_count = 0
        self.wheel_repeat_limit = 7


    def parse(self, data: bytearray) -> None:
        flags = data[0]

        wheel_revolutions_data_present = (flags & 0x01) > 0
        crank_revolutions_data_present = (flags & 0x02) > 0

        index = 1

        if wheel_revolutions_data_present:
            self.wheel_revolutions = int.from_bytes(data[index : index + 4], byteorder="little")
            index += 4
            self.wheel_revolutions_event_time = int.from_bytes(data[index : index + 2], byteorder="little")
            index += 2
            
            # rich.print(f"Wheel Revolutions: {self.wheel_revolutions}, Wheel Revolutions Event Time: {self.wheel_revolutions_event_time}")
            self.update_speed()

        if crank_revolutions_data_present:
            crank_revolutions = int.from_bytes(data[index : index + 2], byteorder="little")
            index += 2
            crank_revolutions_event_time = int.from_bytes(data[index : index + 2], byteorder="little")
            index += 2

            rich.print(f"Crank Revolutions: {crank_revolutions}, Crank Revolutions Event Time: {crank_revolutions_event_time}")

    def update_speed(self):
        # First valid update, no previous data to compare
        if self.previous_wheel_revolutions == 0 or self.previous_wheel_revolutions_event_time == 0:
            self.previous_wheel_revolutions = self.wheel_revolutions
            self.previous_wheel_revolutions_event_time = self.wheel_revolutions_event_time
            return
        
        # Handle the case where event time resets (e.g., overflows or rollovers)
        if self.wheel_revolutions_event_time < self.previous_wheel_revolutions_event_time:
            rich.print("Event time reset detected. Skipping speed calculation.")

            self.previous_wheel_revolutions = self.wheel_revolutions
            self.previous_wheel_revolutions_event_time = self.wheel_revolutions_event_time

            return
        
        if self.wheel_revolutions == self.previous_wheel_revolutions or self.wheel_revolutions_event_time == self.previous_wheel_revolutions_event_time:
            if self.wheel_repeat_count >= self.wheel_repeat_limit:
                self.speed = 0.0
                self.on_speed_update(self.speed)
                self.wheel_repeat_count = 0
            self.wheel_repeat_count += 1
            return
        
        self.wheel_repeat_count = 0
        
        time_difference = (self.wheel_revolutions_event_time - self.previous_wheel_revolutions_event_time) / 1024.0
        wheel_revolutions_difference = self.wheel_revolutions - self.previous_wheel_revolutions
        
        speed_mps = (wheel_revolutions_difference * self.wheel_circumference) / time_difference
        speed_kmph = speed_mps * 3.6

        self.on_speed_update(speed_kmph)

        self.previous_wheel_revolutions = self.wheel_revolutions
        self.previous_wheel_revolutions_event_time = self.wheel_revolutions_event_time

    def on_speed_update(self, speed: float):
        rich.print(f"Speed: {speed} km/h")