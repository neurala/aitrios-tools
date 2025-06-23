#!/usr/bin/env python

import argparse
import base64
import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

import numpy as np
import flatbuffers

from flatbuffer_generated.NeuralaRecognizer.HifiResults import HifiResults


class ResultType(Enum):
    """Enumeration of supported result types."""
    AnomalyHIFI = "anomaly_hifi"


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Deserialize and postprocess Neurala inference results",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--type", "-T", type=ResultType, dest="type",
        help="Type of model result to process", required=True
    )
    parser.add_argument(
        "--input_file", "-f", type=Path, dest="input_file",
        help="Path to the JSON file containing inference results", required=True
    )
    return parser.parse_args()


def get_case_insensitive_key(d: Dict[str, Any], target: str) -> Optional[str]:
    """Finds a key in a dictionary case-insensitively."""
    return next((k for k in d if isinstance(k, str) and k.lower() == target.lower()), None)


def extract_base64_from_inference(inference_dict: Dict[str, Any]) -> bytes:
    """Extracts and decodes base64 string from an inference dictionary."""
    o_key = get_case_insensitive_key(inference_dict, 'o')
    if o_key is None:
        raise KeyError("Missing 'O' key in inference result.")
    return base64.b64decode(inference_dict[o_key])


def try_extract_from_root(root: Dict[str, Any]) -> Optional[bytes]:
    """Tries to extract base64-decoded inference output from a root dict."""
    inferences_key = get_case_insensitive_key(root, 'inferences')
    if not inferences_key:
        return None
    inferences = root[inferences_key]
    if not isinstance(inferences, list) or not inferences:
        return None
    return extract_base64_from_inference(inferences[0])


def extract_data(json_file: Path) -> List[bytes]:
    """Extracts all valid inference results from a JSON input.

    Supports:
    - A flat dictionary with 'Inferences'
    - A dictionary with 'inference_results' list of inference roots
    - A top-level list of such dictionaries
    """
    content = json.loads(json_file.read_text())

    roots: List[Dict[str, Any]] = []
    if isinstance(content, dict):
        roots = [content]
    else:
        roots = content

    decoded_results: List[bytes] = []
    for root in roots:
        results_key = get_case_insensitive_key(root, 'inference_result')
        if results_key:
            results_list = root['inference_result']
            if isinstance(results_list, dict):
                result = try_extract_from_root(results_list)
                if result:
                    decoded_results.append(result)
        else:
            result = try_extract_from_root(root)
            if result:
                decoded_results.append(result)

    if not decoded_results:
        raise ValueError("No valid inference data found.")
    return decoded_results


def deserialize_as(data: bytes, result_type: ResultType) -> Any:
    """Deserializes flatbuffer binary based on model type."""
    if result_type == ResultType.AnomalyHIFI:
        return HifiResults.GetRootAsHifiResults(data, 0)
    else:
        raise ValueError(f'Unknown result type: {result_type}')


def postprocess_hifi(results: HifiResults) -> None:
    """Prints postprocessed output for Anomaly HIFI results."""
    width = results.Width()
    height = results.Height()
    score = results.AnomalyScore()
    heatmap = np.reshape(results.HeatmapAsNumpy(), (width, height))

    print(f'Width        : {width}')
    print(f'Height       : {height}')
    print(f'Anomaly Score: {score}')
    print('Heatmap:')
    for row in heatmap:
        print("\t".join(map(str, row)))


# Map from model type to postprocessing function
POSTPROCESSORS: Dict[ResultType, Callable[[Any], None]] = {
    ResultType.AnomalyHIFI: postprocess_hifi
}


def main() -> None:
    """Main entry point of the script."""
    args = parse_args()
    binary_data_list = extract_data(args.input_file)

    postprocessor = POSTPROCESSORS.get(args.type)
    if postprocessor is None:
        raise ValueError(f"No postprocessor defined for model type: {args.type}")

    for idx, binary in enumerate(binary_data_list):
        print(f"\n===== Inference Result {idx + 1} =====")
        results = deserialize_as(binary, args.type)
        postprocessor(results)


if __name__ == "__main__":
    main()

