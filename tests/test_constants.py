import pytest
import importlib
from src import constants
import copy


def test_initial_definitions_dont_use_screen_vars():
    """
    Reads constants.py as text and checks that SCREEN_WIDTH/HEIGHT are not
    used in variable assignments outside the block defined by the start of 
    calculate_dependent_constants and a specific end-marker comment.
    This helps prevent accidental calculation based on the initial default values.
    """
    constants_file_path = constants.__file__
    recalc_func_def_line = "def calculate_dependent_constants():"
    end_marker_line = "# ---- End of Screen-Dependent Constants recalculation  ----"
    
    try:
        with open(constants_file_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        pytest.fail(f"Could not find constants file at: {constants_file_path}")
        return
        
    start_line_index = -1
    end_line_index = -1

    for i, line in enumerate(lines):
        # Find start and end line indices
        if recalc_func_def_line in line:
            if start_line_index == -1: # Find the first occurrence
                start_line_index = i
        # Use strip() to handle potential leading/trailing whitespace on the marker line
        if end_marker_line.strip() in line.strip():
            if end_line_index == -1:
                end_line_index = i
        
    if start_line_index == -1:
        pytest.fail(f"Could not find the start line '{recalc_func_def_line}' in {constants_file_path}")
        return
    if end_line_index == -1:
        pytest.fail(f"Could not find the end marker line '{end_marker_line}' in {constants_file_path}")
        return
        
    # Combine lines before the start index and after the end index
    lines_before = lines[:start_line_index]
    lines_after = lines[end_line_index + 1:]
    text_to_check = "".join(lines_before + lines_after)
    # print(f"\nDEBUG TEST: Text being checked:\n---\n{text_to_check}\n---") # Optional debug
    
    # Count occurrences in the text outside the excluded block
    sw_count = text_to_check.count("SCREEN_WIDTH")
    sh_count = text_to_check.count("SCREEN_HEIGHT")
    
    # We expect exactly one occurrence for the initial definition of each
    expected_sw_count = 1 
    expected_sh_count = 1
    
    print(f"\nDEBUG TEST: Found {sw_count} occurrences of 'SCREEN_WIDTH' outside excluded block.")
    print(f"DEBUG TEST: Found {sh_count} occurrences of 'SCREEN_HEIGHT' outside excluded block.")
    
    assert sw_count == expected_sw_count, \
        f"Expected exactly {expected_sw_count} usage of SCREEN_WIDTH outside the block defined by calculate_dependent_constants, but found {sw_count}. " \
        f"Ensure dependent variables are initialized to None, not calculated early."
        
    assert sh_count == expected_sh_count, \
        f"Expected exactly {expected_sh_count} usage of SCREEN_HEIGHT outside the block defined by calculate_dependent_constants, but found {sh_count}. " \
        f"Ensure dependent variables are initialized to None, not calculated early."

    print("  OK: SCREEN_WIDTH and SCREEN_HEIGHT only used for initial definition outside the excluded block.")
