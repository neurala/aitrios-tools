#!/usr/bin/env python
# coding: utf-8

# Copyright 2022-2023 Sony Semiconductor Solutions Corp. All rights reserved.
# Copyright 2024 Neurala, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import base64
import errno
import json
from enum import Enum
from pathlib import Path

import jsonschema
from console_access_library.client import Client
from console_access_library.common.config import Config

parser = argparse.ArgumentParser(
        description="Uploads WASM application to AITRIOS Console",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("--configuration_file", "-f", type=str, dest="configuration_file",
                    help=f"The path to the PPL configuration file", required=True)
parser.add_argument("--aitrios_secrets", "-s", type=str, dest="aitrios_secrets",
                    help=f"The path to your AITIRIOS console configuration file", required=True)


def load_configuration_file(configuration_path: Path, schema_path: Path):
    # Load configuration file
    with open(configuration_path, "r") as f:
        configuration = json.load(f)

    # Load configuration schema file
    with open(schema_path, "r") as f:
        json_schema = json.load(f)

    # Validate configuration
    jsonschema.validate(configuration, json_schema)
    return configuration

# file encode to base64
def convert_file_to_b64_string(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read())

def prepare_ppl_file(ppl_path: Path):
    file_content = convert_file_to_b64_string(ppl_path)

    print(f"{ppl_path} is loaded.")
    return ppl_path.name, file_content


def get_device_app_status(app_name: str, version_number: str):
    # Status of Vision and Sensing Application on Console
    status_dictionary = {
        "0": "Importing completed (Before conversion)",
        "1": "Converting...",
        "2": "Conversion completed",
        "3": "Conversion failed",
    }
    # Flag for import check
    import_flag = False
    # Call an API to get Vision and Sensing Application info
    response = deployment_obj.get_device_apps()

    # response error check
    if "result" in response and response["result"] != "SUCCESS":
        # ERROR
        raise ValueError("ERROR", response)

    # SUCCESS
    # Create output list
    apps = response.get("apps", [])
    for app in apps:
        if "name" in app and app["name"] == app_name:
            versions = app.get("versions", [])
            for version in versions:
                if "version" in version and version["version"] == version_number:
                    import_flag = True
                    version_status = version.get("status", "")
                    break
            if import_flag:
                break
    if import_flag:
        return status_dictionary.get(
            version_status, "Unknown status '" + version_status + "'"
        )
    else:
        raise RuntimeError(
            "Vision and Sensing Application is not found. "
            + " \n\tapp_name: "
            + app_name
            + "\n\tversion_number: "
            + version_number
        )

class CompilationMethod(Enum):
    WASM = "0"
    AOT = "1"

def create_client(aitrios_secrets):
    json_load = load_configuration_file(aitrios_secrets, "./json_schemas/console_configuration_schema.json")
    client_obj = Client(Config(**json_load))

    device_management_obj = client_obj.get_device_management()
    response = device_management_obj.get_devices()
    if "result" in response and response["result"] != "SUCCESS":
        raise ValueError("ERROR", response)

    return client_obj


if __name__ == "__main__":
    args = parser.parse_args()

    configuration_file = Path(args.configuration_file)
    if not configuration_file.exists():
        raise RuntimeError(f"File {args.configuration_file} does not exist")

    configuration = load_configuration_file(args.configuration_file, "./json_schemas/configuration_schema.json")
    ppl_file = Path(configuration["ppl_file"])
    if not ppl_file.exists():
        ppl_file = args.configuration_file.parent / ppl_file
    file_name, file_content = prepare_ppl_file(ppl_file)

    client_obj = create_client(args.aitrios_secrets)
    deployment_obj = client_obj.get_deployment()

    # Set app entry point:
    entry_point = "main"

    deployment_parameters = {}
    deployment_parameters["app_name"] = configuration["app_name"]
    deployment_parameters["version_number"] = configuration["version_number"]
    deployment_parameters["comment"] = configuration["comment"]
    deployment_parameters["compiled_flg"] = str(CompilationMethod.WASM.value)
    deployment_parameters["entry_point"] = entry_point
    deployment_parameters["file_name"] = file_name
    deployment_parameters["file_content"] = file_content

    # Call an API to import Vision and Sensing Application into Console for AITRIOS
    try:
        response = deployment_obj.import_device_app(**deployment_parameters)
    except Exception as e:
        # EXCEPTION
        raise e

    # response error check
    if "result" in response and response["result"] != "SUCCESS":
        # ERROR
        raise ValueError("ERROR", response)

    # SUCCESS
    print(
        "Start to import the Vision and Sensing Application."
        + " \n\tapp_name: "
        + configuration["app_name"]
        + "\n\tversion_number: "
        + configuration["version_number"]
    )

    get_status = get_device_app_status(
        app_name=configuration["app_name"], version_number=configuration["version_number"]
    )
    print(
        get_status
        + " \n\tapp_name: "
        + configuration["app_name"]
        + "\n\tversion_number: "
        + configuration["version_number"]
    )

