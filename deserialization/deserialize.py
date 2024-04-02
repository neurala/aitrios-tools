#! /usr/bin/env python

import argparse
import base64
import json
from enum import Enum
from pathlib import Path

import numpy as np
import flatbuffers

from flatbuffer_generated.NeuralaRecognizer.HifiResults import HifiResults as HifiResults

class ResultType(Enum):
    AnomalyHIFI = "anomaly_hifi"

parser = argparse.ArgumentParser(
        description="Deserialize Neurala application flatbuffer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("--type", "-T", type=ResultType, dest="type",
                    help="Type of results data to deserialize", required=True)
parser.add_argument("--input_file", "-f", type=Path, dest="input_file",
                    help="Path to the data to deserialize", required=True)

def extractData(json_file: Path):
    # Parse the JSON document
    root = json.load(json_file.load_text())

    # Decode base64 root
    if 'O' in root['Inferences'][0]:
        return base64.b64decode(root['Inferences'][0]['O'])
    else:
        raise ValueError(f'{json_file} does not contain inference data')

def deserializeAs(data: str, type: ResultType):
    if type == ResultType.AnomalyHIFI:
        return HifiResults.GetRootAsHifiResults(data, 0)
    else:
        raise ValueError(f'Unknown result type "{type}"')

def printHiFiResults(results: HifiResults):
    print(f'Width :{results.Width()}')
    print(f'Height: {results.Height()}')
    print(f'AnomalyScore: {results.AnomalyScore()}')

    print('Heatmap:')
    for row in np.reshape(results.HeatmapAsNumpy(), (results.Width(), results.Height())):
        print("\t".join(map(str, row)))


if __name__ == "__main__":
    args = parser.parse_args()
    data = extractData(args.input_file)
    results = deserializeAs(data, args.type)
    printHiFiResults(results)
