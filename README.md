# Neurala Tools for Sony AITRIOS

## How to use

You may use this repository directly or as reference for your own project.

It is recommended to use python `venv` when using the tools. Example process:

**Linux**

```python
python -m venv ./venv
./venv/bin/python -m pip install -r <tool>/requirements.txt
./venv/bin/python <tool>/<tool>.py <args>
```

**Windows**

```python
python -m venv .\venv
.\venv\Scripts\python -m pip install -r <tool>\requirements.txt
.\venv\Scripts\python <tool>\<tool>.py <args>
```

## Content

### Ouput Deserialization

Deserialization allow you to parse Neurala Applications output.

### Model Upload

Allows to upload a WASM appliation to your AITRIOS console.

### Webpages

Collection of statc HTML pages.