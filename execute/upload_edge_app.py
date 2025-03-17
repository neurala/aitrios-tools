import argparse
import fnmatch
import json
import jsonschema
import time
from typing import List

from pathlib import Path

from console_access_api.aitrios_console import AitriosConsole

parser = argparse.ArgumentParser(
    description="Upload edge app to Console",
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
    "--file",
    "-f",
    type=str,
    help="Path to the Edge App package",
    required=True,
)

def jsonify(data):
    """
    Dump data as a JSON element, pretty formated
    """
    return json.dumps(data, indent=4)

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
        Path(aitrios_secrets), Path("./json_schemas/console_configuration_schema.json")
    )
    return AitriosConsole(
        config["console_endpoint"],
        config["client_id"],
        config["client_secret"],
        config["portal_authorization_endpoint"],
    )


def check_result_success(response: dict):
    return "result" in response and "SUCCESS" in response["result"]

def upload_edge_app(client: AitriosConsole, edge_app: Path):
    response = client.UploadFile(
        "edge_app_pkg", file_name=edge_app.name, file=edge_app.read_bytes()
    )
    print(jsonify(response))

    if check_result_success(response):
        file_info = response["file_info"]
        response = client.Request(
            url=f"/edge_apps",
            method="POST",
            payload={
                "app_name": Path(file_info["name"]).stem,
                "description": "JR Test from CLI",
                "edge_app_package_id": file_info["file_id"]
            },
        )
        print(jsonify(response))


if __name__ == "__main__":
    print("Initiating Console connection")
    args = parser.parse_args()
    client = create_client(args.aitrios_secrets)

    try:
        upload_edge_app(client, Path(args.file))
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
