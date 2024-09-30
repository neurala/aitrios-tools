# AITRIOS Execute tool

Use this tool to launches processing and retrieve resutls and logs.

## Content

```
.
├── json_schemas                                # Script JSON schemas
│   └── console_configuration_schema.json
├── README.md                                   # This file
├── requirements.txt                            # Python dependencies packages, INSTALL BEFORE USING SCRIPT!
└── execute.py                        # Script to launch
```

## Synopsis

```bash
Initiating Console connection
usage: execute.py [-h] --aitrios_secrets AITRIOS_SECRETS --device_name DEVICE_NAME

Uploads WASM application to AITRIOS Console

optional arguments:
  -h, --help            show this help message and exit
  --aitrios_secrets AITRIOS_SECRETS, -s AITRIOS_SECRETS
                        The path to your AITIRIOS console configuration file (default: None)
  --device_name DEVICE_NAME, -D DEVICE_NAME
                          Device Name to search for (default: None)
```

Example:
```
python -m venv ./venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python ./execute.py --aitrios_secrets ./secrets.json -D <Device>
```
