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
    dest="aitrios_secrets",
    help=f"The path to your AITIRIOS console configuration file",
    required=True,
)
parser.add_argument(
    "--device_name",
    "-D",
    type=str,
    dest="device_name",
    help=f"Device Name to search for",
    required=True,
)


def load_configuration_file(configuration_path: Path, schema_path: Path):
    """
    Parse a secrects configuration file, validates against schema
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
    json_load = load_configuration_file(
        aitrios_secrets, "./json_schemas/console_configuration_schema.json"
    )
    return AitriosConsole(
        json_load["console_endpoint"],
        json_load["client_id"],
        json_load["client_secret"],
        json_load["portal_authorization_endpoint"],
    )


def jsonify(data):
    """
    Dumnp data as a JSON element, pretty formated
    """
    return json.dumps(data, indent=4)

if __name__ == "__main__":
    print("Initiating Console connection")
    args = parser.parse_args()
    client_obj = create_client(args.aitrios_secrets)

    # 1. Get a device information
    print(f"Looking for device {args.device_name}")
    request = client_obj.GetDevices(
        connectionState="connected", device_name=args.device_name
    )
    devices = request["devices"]
    if not devices or len(devices) == 0:
        connected_devices = client_obj.GetDevices(connectionState="connected")
        print(f"Connected Devices")
        for device in connected_devices["devices"]:
            name = device["property"]["device_name"]
            dev_id = device["device_id"]
            print(f"{name}: {dev_id}")
        exit(1)

    print(jsonify(devices[0]))
    device_id = devices[0]["device_id"]

    print("Retrieving CommandParameters")
    response = client_obj.GetCommandParameterFile()
    for command_parameter in response["parameter_list"]:
        if device_id in command_parameter["device_ids"]:
            print(jsonify(command_parameter))


    # 2. Turn logs on
    print("Activating logs")
    response = client_obj.Request(
        url="/devices/{device_id}/configuration/applog",
        method="PUT",
        device_id=device_id,
        payload={"enable": True},
    )
    print(jsonify(response))

    print("Setting device destination")
    response = client_obj.Request(
        url="/devices/{device_id}/configuration/logdestination",
        method="PUT",
        device_id=device_id,
        payload={"level": "Verbose", "destination": "Cloud", "SensorRegister": True},
    )
    print(jsonify(response))

    # 3. Start processing
    print("Starting processing")
    response = client_obj.StartUploadInferenceResult(device_id=device_id)
    print(jsonify(response))
    if not "SUCCES" in response["result"]:
        exit(2)
    output_subdirectory = response["outputSubDirectory"]

    # Wait for processing do do something useful
    time.sleep(10)

    # 4. Downloads Results
    print("Getting results")
    # while not result:
    result = client_obj.GetInferenceResults(
        device_id=device_id, NumberOfInferenceresults=1, raw=1
    )
    print(jsonify(result))

    # 5. Download logs
    # sleeping to make sure all logs are loaded in the database
    time.sleep(10)
    print("Downloading logs")

    # Hardcoding "top" here to return the N latest logs
    response = client_obj.Request(
        url="/devices/{device_id}/applogs?top=59", method="GET", device_id=device_id
    )
    print(jsonify(response))

    # Turning logs off
    response = client_obj.Request(
        url="/devices/{device_id}/configuration/applog",
        method="PUT",
        device_id=device_id,
        payload={"enable": False},
    )
    print(jsonify(response))

    # 6. Stop processing
    print("Stopping processing")
    response = client_obj.StopUploadInferenceResult(device_id=device_id)
    print(jsonify(response))
