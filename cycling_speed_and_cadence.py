import rich

class CSCSensor:
    def parseCSCData(self, data: bytearray) -> None:
        flags = data[0]

        wheel_revolutions_data_present = (flags & 0x01) > 0
        crank_revolutions_data_present = (flags & 0x02) > 0

        index = 1

        if wheel_revolutions_data_present:
            wheel_revolutions = int.from_bytes(data[index : index + 4], byteorder="little")
            index += 4
            wheel_revolutions_event_time = int.from_bytes(data[index : index + 2], byteorder="little")
            index += 2
            
            rich.print(f"Wheel Revolutions: {wheel_revolutions}, Wheel Revolutions Event Time: {wheel_revolutions_event_time}")

        if crank_revolutions_data_present:
            crank_revolutions = int.from_bytes(data[index : index + 2], byteorder="little")
            index += 2
            crank_revolutions_event_time = int.from_bytes(data[index : index + 2], byteorder="little")
            index += 2

            rich.print(f"Crank Revolutions: {crank_revolutions}, Crank Revolutions Event Time: {crank_revolutions_event_time}")