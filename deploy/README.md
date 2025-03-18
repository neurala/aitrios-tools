# AITRIOS Deployment Tool

Use this tool to upload+convert models and to upload Edge App Packages.
This tool is specific to Console V2.

## Usage Examples

```bash
# Do this once before using the tool.
python3 -m venv venv
venv/bin/python3 -m pip install -r requirements.txt

# Use this to upload+convert a model from a BrainBuilder bundle.
# The model type can be 'keras', 'onnx', or 'tflite', as long as such a model exists within the bundle.
venv/bin/python3 deploy.py --secrets 'secrets.json' --bundle '/path/to/some-bundle.zip' --model-type tflite

# Use this to upload an Edge App Package.
venv/bin/python3 deploy.py --secrets 'secrets.json' --package '/path/to/SomeEdgeApp.zip'
```

Both operations can be combined into one.
