import os
import pytest
from src.utils import clean_filename, format_time, get_timestamp

def test_clean_filename():
    assert clean_filename("Hello World!") == "Hello_World!"
    assert clean_filename("Script/Test:2.txt") == "ScriptTest2.txt"
    assert clean_filename("   Spaces   ") == "Spaces"
    assert clean_filename("") == "sin_nombre"

def test_format_time():
    assert format_time(3661) == "01:01:01"
    assert format_time(60) == "00:01:00"
    assert format_time(0) == "00:00:00"

def test_get_timestamp():
    ts = get_timestamp()
    assert len(ts) == 15 # YYYYMMDD_HHMMSS
    assert "_" in ts
