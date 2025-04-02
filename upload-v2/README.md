# AITRIOS V2 Uploader Tool

Use this tool to upload+convert models and to upload Edge App Packages.
This tool temporarily also contains functionality for controlling execution and logging. See the **TODO** below.

This tool is specific to Console V2.

## Usage Examples

```bash
# Do this once before using the tool.
python3 -m venv venv
venv/bin/python3 -m pip install -r requirements.txt

# Use this to upload+convert a model from a BrainBuilder bundle.
# The model type can be 'keras', 'onnx', or 'tflite', as long as such a model exists within the bundle.
venv/bin/python3 upload.py --secrets 'secrets.json' --bundle '/path/to/some-bundle.zip' --model-type tflite

# Use this to upload an Edge App Package.
venv/bin/python3 upload.py --secrets 'secrets.json' --package '/path/to/SomeEdgeApp.zip'

# Use this to enable logging on a given device+deployment.
venv/bin/python3 upload.py --secrets 'secrets.json' --enable-logging 'some-module-id' --device 'some-device-id'

# Use this to start inference.
venv/bin/python3 upload.py --secrets 'secrets.json' --start-inference 'some-module-id' --device 'some-device-id'

# Use this to stop inference.
venv/bin/python3 upload.py --secrets 'secrets.json' --stop-inference 'some-module-id' --device 'some-device-id'
```

Operations can be combined into one.

## TODO

Enabling logging and controlling inference should not belong to a script called `upload.py`. Either **(0)** rename this "module" to something that would encapsulate both uploading and execution, **(1)** put `AitriosAccess` into its own module and make separate scripts (e.g. `upload.py` and `execute.py`), or **(2)** add a `--v2` flag to the existing tools and smush the functionality into them.
