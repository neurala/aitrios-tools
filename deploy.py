import console_access_library
import json
import jsonschema
import os
import sys
import time
import zipfile

from argparse import ArgumentParser
from base64 import b64decode, b64encode
from console_access_api.aitrios_console import AitriosConsole
from datetime import date, datetime
from io import BytesIO
from pathlib import Path


# Given a path to a BrainBuilder bundle and a model type ("keras", "onnx",
# or "tflite"), extracts it and returns its name and its raw data.
def extract_model_from_brain_builder_bundle(bundle_path, model_type):
    def find_brain(bundle):
        names = bundle.namelist()
        for name in names:
            if name.endswith(".zip"):
                return name
        return None
    def find_model(brain, model_type):
        names = brain.namelist()
        extension = f".{model_type}"
        for name in names:
            if name.endswith(extension):
                return name
        return None
    with zipfile.ZipFile(bundle_path, 'r') as bundle:
        brain = find_brain(bundle)
        if brain is None:
            raise Exception(f"Could not find a brain in \"{bundle_path}\".")
        brain = bundle.read(brain)
        brain = BytesIO(brain)
        with zipfile.ZipFile(brain, 'r') as brain:
            model_name = find_model(brain, model_type)
            if model_name is None:
                raise Exception(f"Could not find a {model_type} model in \"{bundle_path}\".")
            model_data = brain.read(model_name)
            return model_name, model_data


# Loads the configuration at the given path and validates it against the schema at the given path.
def load_configuration_file(configuration_path, schema_path):
    text = schema_path.read_text()
    json_schema = json.loads(text)
    text = configuration_path.read_text()
    configuration = json.loads(text)
    jsonschema.validate(configuration, json_schema)
    return configuration


# Checks whether the response reports a success.
def response_is_success(response):
    return response['result'] == "SUCCESS"


# A class for encapsulating access to the AITRIOS console.
class AitriosAccess:
    def __init__(self, secrets):
        secrets = Path(secrets)
        schema = Path("execute/json_schemas/console_configuration_schema.json")
        config = load_configuration_file(secrets, schema)
        console_endpoint = config["console_endpoint"]
        client_id = config["client_id"]
        client_secret = config["client_secret"]
        authorization_endpoint = config["portal_authorization_endpoint"]
        self.client = AitriosConsole(console_endpoint, client_id, client_secret, authorization_endpoint)

    def get_device_information(self, device_id):
        return self.client.GetDevice(device_id=device_id)

    def get_image_from_device(self, device_id, destination):
        response = self.client.GetDirectImage(device_id=device_id)
        if not response_is_success(response):
            raise Exception(response)
        contents = response['contents'].encode('ascii')
        contents = b64decode(contents)
        with open(destination, 'wb') as file:
            file.write(contents)

    def upload_non_converted_model_data(self, model_data, file_name):
        response = self.client.UploadFile(type_code="non_converted_model", file=model_data, file_name=file_name)
        if not response_is_success(response):
            raise Exception(response)
        return response['file_info']['file_id']

    def import_model(self, file_id, model_id, comment):
        payload = {'model_file_id':file_id, 'model_id':model_id, 'network_type':"0", 'comment':comment}
        response = self.client.ImportBaseModel(payload)
        if not response_is_success(response):
            raise Exception(response)

    def convert_model(self, model_id):
        response = self.client.PublishModel(model_id=model_id)
        if not response_is_success(response):
            raise Exception(response)
        while True:
            time.sleep(1)
            response = self.client.GetBaseModelStatus(model_id=model_id)
            try:
                projects = response['projects']
                count = len(projects)
                if count != 1:
                    print(f"There is more than one project (there are {count}), and I don't know what to do in this situation.")
                status = projects[0]['versions'][-1]['result']
                if status != "processing":
                    return status == "Import completed"
            # This happened once, but I never got to see what happened, so here is something for debugging that.
            except:
                print(response)
                raise Exception("Something went wrong during model conversion. Check whether the response above is unexpected.")

    def upload_edge_app_package(self, package, name):
        with open(package, 'rb') as file:
            contents = file.read()
            response = self.client.UploadFile(type_code="edge_app_pkg", file=contents, file_name=name)
            if not response_is_success(response):
                raise Exception(response)
            return response['file_info']['file_id']

'''
    def upload_configuration(self, configuration_file_path, name):
        with open(configuration_file_path) as configuration_file:
            data = configuration_file.read().encode('utf-8')
            encoded_data = b64encode(data).decode('utf-8')
            payload = {'file_name':name, 'parameter':encoded_data}
            response = self.client.RegistCommandParameterFile(payload)
            print(response)
            return response_is_success(response)

    def create_deployment_configuration(self):
        pass

    def debug(self):
        response = self.client.GetCommandParameterFile()
        if not response_is_success(response):
            print(response)
            return
        parameters = response['parameter_list']
        count = len(apps)
        print(f"There are {count} parameter files.")
        for parameter in parameters:
            print(parameter)
'''


def do_everything(arguments):
    timestamp = datetime.now().strftime(r"%Y%m%d%H%M%S")
    access = AitriosAccess(arguments.secrets)
    print(f"Extracting {arguments.model_type} model from \"{arguments.bundle}\"...")
    model_name, model_data = extract_model_from_brain_builder_bundle(arguments.bundle, arguments.model_type)
    model_name = os.path.splitext(model_name)[0]
    model_name = f"{model_name}.{timestamp}.{arguments.model_type}"
    print(f"Uploading model as \"{model_name}\"...")
    file_id = access.upload_non_converted_model_data(model_data, model_name)
    print(f"The file ID of the uploaded model is \"{file_id}\".")
    print("Importing model...")
    access.import_model(file_id, model_name, f"A {arguments.model_type} model uploaded by an automated deployment script.")
    print("Converting model...")
    access.convert_model(model_name)
    package_name = os.path.basename(arguments.package)
    package_name = os.path.splitext(package_name)[0]
    print(f"Uploading Edge App Package \"{arguments.package}\" as \"{package_name}\"...")
    file_id = access.upload_edge_app_package(arguments.package, package_name)
    print(f"The file ID of the uploaded Edge App Package is \"{file_id}\".")
  # create_deployment_configuration()
  # somehow_deploy_said_configuration()
    print("Done.")

def mock_everything(arguments):
    timestamp = datetime.now().strftime(r"%Y%m%d%H%M%S")
    print(f"[MOCK] Extracting {arguments.model_type} model from \"{arguments.bundle}\"...")
    model_name, model_data = extract_model_from_brain_builder_bundle(arguments.bundle, arguments.model_type)
    model_name = os.path.splitext(model_name)[0]
    model_name = f"{model_name}.{timestamp}.{arguments.model_type}"
    print(f"[MOCK] Uploading model as \"{model_name}\"...")
    print("[MOCK] Importing model...")
    print("[MOCK] Converting model...")
    package_name = os.path.basename(arguments.package)
    package_name = os.path.splitext(package_name)[0]
    print(f"[MOCK] Uploading Edge App Package \"{arguments.package}\" as \"{package_name}\"...")
    print("[MOCK] Done.")

if __name__ == "__main__":
    possible_model_types = ["keras", "onnx", "tflite"]
    parser = ArgumentParser(add_help=False)
    parser.add_argument("--help", "-h", action='help', help="Show this help message and exit.")
    parser.add_argument("--bundle", type=Path, required=True, help="A path to the BrainBuilder bundle to upload.")
    parser.add_argument("--model-type", type=str, required=True, choices=possible_model_types, help="The type of model in the bundle to upload.")
    parser.add_argument("--package", type=Path, required=True, help="A path to the Edge App Package to upload.")
    parser.add_argument("--secrets", type=Path, required=True, help="Your deepest secrets.")
    parser.add_argument("--dry-run", "--mock", action='store_true', dest="mock", help="Print what would happen if this were not a dry run.")
    if "-h" in sys.argv or "--help" in sys.argv:
        parser.print_help()
        exit(0)
    arguments = parser.parse_args()
    if arguments.mock:
        mock_everything(arguments)
        exit(0)
    try:
        do_everything(arguments)
    except Exception as exception:
        print(exception)
        exit(1)
