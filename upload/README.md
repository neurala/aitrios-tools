# AITRIOS Upload tool

Use this tool to upload your application to AITRIOS Console. This script is
adapted from [AITRIOS SDK jupyter notebook "import\_to\_console"][1].

## Content

```
.
├── aitrios_console_configuration.json.template # Fill this template with your AITRIOS keys
├── model_configuration.json.template           # Fill this template with your application info
├── json_schemas                                # Script JSON schemas
│   ├── configuration_schema.json
│   └── console_configuration_schema.json
├── README.md                                   # This file
├── requirements.txt                            # Python dependencies packages, INSTALL BEFORE USING SCRIPT!
└── upload_vision_app.py                        # Script to launch
```

## Synopsis

```bash
usage: upload_vision_app.py [-h] --configuration_file CONFIGURATION_FILE --aitrios_secrets AITRIOS_SECRETS

Uploads WASM application to AITRIOS Console

optional arguments:
  -h, --help            show this help message and exit
  --configuration_file CONFIGURATION_FILE, -f CONFIGURATION_FILE
                        The path to the PPL configuration file (default: None)
  --aitrios_secrets AITRIOS_SECRETS, -s AITRIOS_SECRETS
                        The path to your AITIRIOS console configuration file (default: None)
```

Example:
```
python -m venv ./venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python ./upload_vision_app.py -f app_config.json -s secrets.json
```

## Resources

[1]: https://github.com/SonySemiconductorSolutions/aitrios-sdk-vision-sensing-app/tree/main/tutorials/4_prepare_application/2_import_to_console
