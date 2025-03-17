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
        self_path = os.path.realpath(__file__)
        here = os.path.dirname(self_path)
        schema = Path(os.path.dirname(here) + "/execute/json_schemas/console_configuration_schema.json")
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

    def upload_edge_app_package(self, package):
        package = Path(package)
        contents = package.read_bytes()
        name = package.stem
        response = self.client.UploadFile(type_code="edge_app_pkg", file=contents, file_name=name)
        if not response_is_success(response):
            raise Exception(response)
        file_id = response['file_info']['file_id']
        payload = {'app_name':name, 'edge_app_package_id':file_id, 'description':"An Edge App Package uploaded by an automated deployment script."}
        response = self.client.Request(url="/edge_apps", method='POST', payload=payload)
        if not response_is_success(response):
            raise Exception(response)

'''
    def create_deployment_configuration(self, model_id, application_name):
        model_information = {'model_id':model_id, 'version_number':"1.0.0"}
        edge_application = {'app_name':application_name, 'app_version':"1.0.0"}
        description = "A deployment configuration created by an automated deployment script."
        payload = {'config_id':model_id, 'models':[model_information], 'edge_apps':[edge_application], 'description':description}
        print(f"This method does not work at the moment, but the current payload looks like this.\n{payload}")

    def upload_configuration(self, configuration_file_path, name):
        with open(configuration_file_path) as configuration_file:
            data = configuration_file.read().encode('utf-8')
            encoded_data = b64encode(data).decode('utf-8')
            payload = {'file_name':name, 'parameter':encoded_data}
            response = self.client.RegistCommandParameterFile(payload)
            if not response_is_success(response):
                raise Exception(response)
'''


timestamp = datetime.now().strftime(r"%Y%m%d%H%M%S")


def upload_bundle(access, arguments):
    print(f"Extracting {arguments.model_type} model from \"{arguments.bundle}\"...")
    model_name, model_data = extract_model_from_brain_builder_bundle(arguments.bundle, arguments.model_type)
    model_name = os.path.splitext(model_name)[0]
    model_name = f"{model_name}.{timestamp}.{arguments.model_type}"
    print(f"Uploading model as \"{model_name}\"...")
    if not arguments.mock:
        file_id = access.upload_non_converted_model_data(model_data, model_name)
        print(f"The file ID of the uploaded model is \"{file_id}\".")
    print("Importing model...")
    if not arguments.mock:
        access.import_model(file_id, model_name, f"A {arguments.model_type} model uploaded by an automated deployment script.")
    print("Converting model...")
    if not arguments.mock:
        access.convert_model(model_name)


def upload_edge_app(access, arguments):
    print(f"Uploading Edge App Package \"{arguments.package}\"...")
    if not arguments.mock:
        access.upload_edge_app_package(arguments.package)
    print("Done.")


if __name__ == "__main__":
    parser = ArgumentParser(add_help=False)
    parser.add_argument("--help", "-h", action='help', help="Show this help message and exit.")
    parser.add_argument("--bundle", type=Path, required=False, help="A path to the BrainBuilder bundle to upload.")
    parser.add_argument("--model-type", type=str, required=False, choices=["keras", "onnx", "tflite"], help="The type of model in the bundle to upload.")
    parser.add_argument("--package", type=Path, required=False, help="A path to the Edge App Package to upload.")
    parser.add_argument("--secrets", type=Path, required=True, help="Your deepest secrets.")
    parser.add_argument("--dry-run", "--mock", action='store_true', dest="mock", help="Print what would happen if this were not a dry run.")
    if "-h" in sys.argv or "--help" in sys.argv:
        parser.print_help()
        exit(0)
    arguments = parser.parse_args()
    access = AitriosAccess(arguments.secrets) if not arguments.mock else None
    try:
        if arguments.bundle is not None:
            if arguments.model_type is None:
                print("Please specify a model type.")
                exit(2)
            upload_bundle(access, arguments)
        if arguments.package is not None:
            upload_edge_app(access, arguments)
    except Exception as exception:
        print(exception)
        exit(1)
