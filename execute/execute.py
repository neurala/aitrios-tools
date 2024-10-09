import argparse
import fnmatch
import json
import jsonschema
import time
from typing import List

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
parser.add_argument(
    "--stages",
    action='append',
    help="Glob patterns to select specific stages (e.g., 'stage_*', 'stage_start_*')"
)


def load_configuration_file(configuration_path: Path, schema_path: Path) -> dict:
    """
    Parse a secrets configuration file, validate against schema
    """
    # Load configuration schema file
    json_schema = json.loads(schema_path.read_text())

    # Load configuration file
    configuration = json.loads(configuration_path.read_text())

    # Validate configuration
    jsonschema.validate(configuration, json_schema)
    return configuration


def create_client(aitrios_secrets):
    """
    Create a connection object
    """
    config = load_configuration_file(
        Path(aitrios_secrets),
        Path("./json_schemas/console_configuration_schema.json")
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


class DeviceProcessor:
    """
    DeviceProcessor is a state machine containing the interaction with a console device
    Stages are defined by the prefix "stage" at the bottom, and will be executed by default
    in the oder they are provided.
    """

    def __init__(self, client, device_name):
        """
        Initialize a processor for device named device_name
        using client API.
        """
        self.client = client
        self.device_name = device_name
        self.device_id = None

    def get_device_info(self):
        """
        Retrieves the information about the device selected
        """
        print(f"Looking for device {self.device_name}")
        request = self.client.GetDevices(
            connectionState="connected",
            device_name=self.device_name
        )
        devices = request["devices"]
        if not devices:
            connected_devices = self.client.GetDevices(connectionState="connected")
            print("Connected Devices")
            for device in connected_devices["devices"]:
                name = device["property"]["device_name"]
                dev_id = device["device_id"]
                print(f"{name}: {dev_id}")
            raise Exception(f"Device {self.device_name} not found.")

        self.device_id = devices[0]["device_id"]
        print(jsonify(devices[0]))

    def retrieve_command_parameters(self):
        """
        Search for the command parameter bound the device selected
        """
        print("Retrieving CommandParameters")
        response = self.client.GetCommandParameterFile()
        for command_parameter in response["parameter_list"]:
            if self.device_id in command_parameter["device_ids"]:
                print(jsonify(command_parameter))

    def activate_logs(self):
        """
        Turns ON logging for the device
        """
        print("Activating logs")
        response = self.client.Request(
            url=f"/devices/{self.device_id}/configuration/applog",
            method="PUT",
            device_id=self.device_id,
            payload={"enable": True},
        )
        print(jsonify(response))

        print("Setting device destination")
        response = self.client.Request(
            url=f"/devices/{self.device_id}/configuration/logdestination",
            method="PUT",
            device_id=self.device_id,
            payload={
                "level": "Verbose",
                "destination": "Cloud",
                "SensorRegister": True,
            },
        )
        print(jsonify(response))

    def start_processing(self):
        """
        Tells the device to start inferences on camera feed as stipulated in the command parameter
        """
        print("Starting processing")
        response = self.client.StartUploadInferenceResult(device_id=self.device_id)
        print(jsonify(response))
        if "SUCCESS" not in response["result"]:
            raise Exception("Processing start failed.")
        self.output_subdirectory = response["outputSubDirectory"]

    def wait_for_inference(self, timeout: int = 10):
        print("Waiting on camera to infer...")
        time.sleep(timeout)

    def get_results(self):
        """
        Download one result from the camera (latest)
        """
        print("Getting results")
        result = self.client.GetInferenceResults(
            device_id=self.device_id,
            NumberOfInferenceresults=1,
            raw=1
        )
        print(jsonify(result))

    def download_logs(self, topNLogs: int = 50):
        """
        Download ANY last topNLogs from the camera, could be from an older run
        """
        print(f"Downloading last {topNLogs} logs")
        time.sleep(10)  # Wait to ensure all logs are loaded
        response = self.client.Request(
            url=f"/devices/{self.device_id}/applogs?top={topNLogs}",
            method="GET",
            device_id=self.device_id,
            topNLogs=str(topNLogs),
        )
        print(jsonify(response))

    def deactivate_logs(self):
        """
        Turn OFF camera logging, previously acquired data will remain available for 30 days
        """
        print("Turning logs off")
        response = self.client.Request(
            url=f"/devices/{self.device_id}/configuration/applog",
            method="PUT",
            device_id=self.device_id,
            payload={"enable": False},
        )
        print(jsonify(response))

    def stop_processing(self):
        """
        Stops inferencing camera stream
        """

        print("Stopping processing")
        response = self.client.StopUploadInferenceResult(device_id=self.device_id)
        print(jsonify(response))

    # Example user-defined stages
    def stage_initialize(self):
        print("Stage: Initializing device")
        self.get_device_info()

    def stage_start_logs(self):
        print("Stage: Starting logs")
        self.activate_logs()

    def stage_infer(self):
        print("Stage: Starting inference")
        self.start_processing()
        self.wait_for_inference()
        self.get_results()

    def stage_download_logs(self):
        print("Stage: Downloading logs")
        self.download_logs()

    def stage_stop_processing(self):
        print("Stage: Stopping device processing")
        self.deactivate_logs()
        self.stop_processing()

    def execute_stages(self, stage_patterns: List[str] = None):
        """
        Execute all the functions in this class prefixed by "stage", in the order they are defined
        stage_patterns may be used to filter which stages to run
        """
        # Set default pattern to run all stages if none provided
        stage_patterns = stage_patterns or ["stage_*"]

        # Find methods starting with 'stage' and filter by patterns
        all_stage_methods = [method_name for method_name in dir(self) if method_name.startswith("stage_")]
        filtered_methods = []

        # Apply glob filtering
        for pattern in stage_patterns:
            filtered_methods.extend(fnmatch.filter(all_stage_methods, pattern))

        # Remove duplicates and sort by line number (order of definition)
        filtered_methods = sorted(set(filtered_methods), key=lambda method: getattr(self, method).__code__.co_firstlineno)

        # Execute the filtered methods
        for method_name in filtered_methods:
            stage_method = getattr(self, method_name)
            print(f"Executing {stage_method.__name__}")
            stage_method()

if __name__ == "__main__":
    print("Initiating Console connection")
    args = parser.parse_args()
    client = create_client(args.aitrios_secrets)

    processor = DeviceProcessor(client, args.device_name)

    try:
        print(f"{args.stages}")
        processor.execute_stages(stage_patterns=args.stages)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
