#! /usr/bin/env python

from NeuralaRecognizer.HifiResults import HifiResults as HifiResults
import numpy as np
import flatbuffers
import base64
import json

from enum import Enum

import argparse
from pathlib import Path

class ResultType(Enum):
    AnomalyHIFI = "anomaly_hifi"

parser = argparse.ArgumentParser(
        description="Deserialize Neurala application flatbuffer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("--type", "-T", type=ResultType, dest="type",
                    help=f"Type of results data to deserialize", required=True)
parser.add_argument("--input_file", "-f", type=Path, dest="input_file",
                    help=f"Path to the data to deserialize", required=True)

def extractData(json_file: Path):
    # Parse the JSON document
    with open(json_file, 'r', encoding='utf-8') as f:
        buf = json.load(f)

    # Decode base64 data
    if 'O' in buf['Inferences'][0]:
        return base64.b64decode(buf['Inferences'][0]['O'])
    else:
        raise f'{file} does not contain inference data'

def deserializeAs(data: str, type: ResultType):
    if type == ResultType.AnomalyHIFI:
        return HifiResults.GetRootAsHifiResults(data, 0)
    else:
        raise f'Unknown result type "{type}"'

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
