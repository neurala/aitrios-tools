import argparse
import json
import jsonschema
import time

from pathlib import Path

from console_access_api.aitrios_console import AitriosConsole

parser = argparse.ArgumentParser(
    description="Launches execution on a camera configured in AITRIOS Console",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

parser.add_argument(
    "--aitrios_secrets",
    "-s",
    type=str,
    help="The path to your AITIRIOS console configuration file",
    required=True,
)
parser.add_argument(
    "--device_name",
    "-D",
    type=str,
    help="Device Name to search for",
    required=True,
)


def load_configuration_file(configuration_path: Path, schema_path: Path) -> dict:
    """
    Parse a secrets configuration file, validate against schema
    """
    # Load configuration file
    with open(configuration_path, "r") as f:
        configuration = json.load(f)

    # Load configuration schema file
    with open(schema_path, "r") as f:
        json_schema = json.load(f)

    # Validate configuration
    jsonschema.validate(configuration, json_schema)
    return configuration


def create_client(aitrios_secrets):
    """
    Create a connection object
    """
    config = load_configuration_file(
        aitrios_secrets, "./json_schemas/console_configuration_schema.json"
    )
    return AitriosConsole(
        config["console_endpoint"],
        config["client_id"],
        config["client_secret"],
        config["portal_authorization_endpoint"],
    )


def jsonify(data):
    """
    Dump data as a JSON element, pretty formated
    """
    return json.dumps(data, indent=4)

if __name__ == "__main__":
    print("Initiating Console connection")
    args = parser.parse_args()
    client = create_client(args.aitrios_secrets)

    # 1. Get a device information
    print(f"Looking for device {args.device_name}")
    request = client.GetDevices(
        connectionState="connected",
        device_name=args.device_name
    )
    devices = request["devices"]
    if not devices:
        connected_devices = client.GetDevices(connectionState="connected")
        print("Connected Devices")
        for device in connected_devices["devices"]:
            name = device["property"]["device_name"]
            dev_id = device["device_id"]
            print(f"{name}: {dev_id}")
        exit(1)

    print(jsonify(devices[0]))
    device_id = devices[0]["device_id"]

    print("Retrieving CommandParameters")
    response = client.GetCommandParameterFile()
    for command_parameter in response["parameter_list"]:
        if device_id in command_parameter["device_ids"]:
            print(jsonify(command_parameter))


    # 2. Turn logs on
    print("Activating logs")
    response = client.Request(
        url="/devices/{device_id}/configuration/applog",
        method="PUT",
        device_id=device_id,
        payload={"enable": True},
    )
    print(jsonify(response))

    print("Setting device destination")
    response = client.Request(
        url="/devices/{device_id}/configuration/logdestination",
        method="PUT",
        device_id=device_id,
        payload={"level": "Verbose", "destination": "Cloud", "SensorRegister": True},
    )
    print(jsonify(response))

    # 3. Start processing
    print("Starting processing")
    response = client.StartUploadInferenceResult(device_id=device_id)
    print(jsonify(response))
    if not "SUCCESS" in response["result"]:
        exit(2)
    output_subdirectory = response["outputSubDirectory"]

    # Wait for processing to do something useful
    print("Waiting on camera to infer...")
    time.sleep(10)

    # 4. Downloads Results
    print("Getting results")
    result = client.GetInferenceResults(
        device_id=device_id, NumberOfInferenceresults=1, raw=1
    )
    print(jsonify(result))

    # 5. Download logs
    # sleeping to make sure all logs are loaded in the database
    print("Waiting on camera to gather logs...")
    time.sleep(10)
    topNLogs = 50
    print(f"Downloading last {topNLogs} logs")

    # Hardcoding "top" here to return the N latest logs
    response = client.Request(
        url="/devices/{device_id}/applogs?top={topNLogs}",
        method="GET",
        device_id=device_id,
        topNLogs=str(topNLogs)
    )
    print(jsonify(response))

    # Turning logs off
    response = client.Request(
        url="/devices/{device_id}/configuration/applog",
        method="PUT",
        device_id=device_id,
        payload={"enable": False},
    )
    print(jsonify(response))

    # 6. Stop processing
    print("Stopping processing")
    response = client.StopUploadInferenceResult(device_id=device_id)
    print(jsonify(response))
