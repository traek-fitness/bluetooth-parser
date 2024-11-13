import rich

class CSCSensor:
    def parseCSCData(self, data: bytearray) -> None:
        rich.print("CSC Data: ", data)