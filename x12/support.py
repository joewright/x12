"""
support.py

Convenience functions for X12 Processing
"""
import os
from x12.config import get_config, X12Config


def is_x12_data(input_data: str) -> bool:
    """
    Returns True if the input data appears to be a X12 message.
    :param input_data: Input data to evaluate
    :return: True if the input data is a x12 message, otherwise False
    """
    return input_data.startswith("ISA") if input_data else False


def is_x12_file(file_path: str) -> bool:
    """
    Returns true if the file path exists and is a x12 file.
    Environment and user variables are expanded within the file path.
    :param file_path: The file path to test.
    :return: True if the file path is a x12 file, otherwise false
    """
    if not file_path:
        return False

    expanded_path = os.path.expandvars(os.path.expanduser(file_path))
    if not os.path.exists(expanded_path) or os.path.isdir(expanded_path):
        return False

    with (open(expanded_path, "r")) as f:
        f.seek(0)
        # ISA segment is first 106 characters
        config: X12Config = get_config()
        isa_segment = f.read(config.x12_isa_segment_length)
        return is_x12_data(isa_segment)