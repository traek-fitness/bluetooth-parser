import re
import json
from datetime import datetime

def parse_log(file_path):
    log_pattern = r'I\s+([\d:]+\.\d+)\s+Notification received from [\w-]+, value: \((0x)\)\s+([A-F0-9\-]+)'
    
    results = []
    first_timestamp = None

    with open(file_path, 'r') as file:
        for line in file:
            match = re.search(log_pattern, line)
            if match:
                timestamp_str = match.group(1)
                value = match.group(3)
                
                timestamp = datetime.strptime(timestamp_str, "%H:%M:%S.%f")
                
                if first_timestamp is None:
                    first_timestamp = timestamp
                    relative_timestamp = 0
                else:
                    relative_timestamp = (timestamp - first_timestamp).total_seconds()

                results.append({
                    'timestamp': round(relative_timestamp, 3),
                    'value': value
                })

    return results

def save_to_json(data, output_file):
    with open(output_file, 'w') as json_file:
        json.dump(data, json_file, indent=4)

if __name__ == "__main__":
    input_file = 'source/crank/1.txt'
    output_file = 'output/crank/1.json'

    parsed_data = parse_log(input_file)

    save_to_json(parsed_data, output_file)

    print(f"Parsed data saved to {output_file}")
