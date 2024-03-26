# Neurala deserialization tool

Use this tool to deserialize application result obtained from
AITRIOS console. You do not need `flatc` to excute this application,
flatbuffer parsers were generated ahead of time.

> At the moment, only Anomaly HiFi application are supported

## Content

```
.
├── deserialize.py        # Script to run the application
├── flatbuffer_schemas    # Reference schemas for application data
│   └── anomaly_hifi.fbs
├── NeuralaRecognizer     # FlatC generated files
│   ├── HifiResults.py
├── README.md             # This file
└── requirements.txt      # Script dependencies
```


## Synopsis

```
usage: deserialize.py [-h] --type TYPE --input_file INPUT_FILE

Deserialize Neurala application flatbuffer

optional arguments:
  -h, --help            show this help message and exit
    --type TYPE, -T TYPE  Type of results data to deserialize (default: None)
  --input_file INPUT_FILE, -f INPUT_FILE
                          Path to the data to deserialize (default: None)
```

## Example

```
python -m venv ./venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python ./deserialize.py -f hifi_console_result.json -T anomaly_hifi
```

> NOTE: At the monent, the only type supported is `anomaly_hifi`
