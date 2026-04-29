"""File editing tools — re-exports from pyskills.edit
Mirrors solveit's message editing but for raw files.
"""
from pyskills.edit import (
    file_str_replace,
    file_strs_replace,
    file_insert_line,
    file_replace_lines,
    file_del_lines,
)

__all__ = [
    "str_replace",
    "strs_replace", 
    "insert_line",
    "replace_lines",
    "del_lines",
]

# Friendlier aliases (consistent with toolbox naming)
str_replace = file_str_replace
strs_replace = file_strs_replace
insert_line = file_insert_line
replace_lines = file_replace_lines
del_lines = file_del_lines