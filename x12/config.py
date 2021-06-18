"""
config.py
"""
from pydantic import BaseSettings, Field
import os
from os.path import dirname, abspath
from functools import lru_cache


class X12Config(BaseSettings):
    """
    X12 Parsing and Validation Configurations
    """

    # index positions for character delimiters in ISA segment
    x12_isa_component_separator: int = 104
    x12_isa_element_separator: int = 3
    x12_isa_repetition_separator: int = 82
    x12_isa_segment_length: int = 106
    x12_isa_segment_terminator: int = 105

    # version field positions in tokenized segments
    x12_isa_control_version: int = 12
    x12_gs_functional_code: int = 1
    x12_gs_function_version: int = 8
    x12_st_transaction_code: int = 1

    x12_character_set: str = Field(regex="^(BASIC|EXTENDED)$")
    x12_reader_buffer_size: int = 1024000

    class Config:
        case_sensitive = False
        env_file = os.path.join(dirname(dirname(abspath(__file__))), ".env")


@lru_cache
def get_config():
    """Returns the X12Config"""
    return X12Config()