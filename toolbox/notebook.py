"""Jupyter notebook tools — re-exports from pyskills.edit
Mirrors solveit's notebook editing capabilities.
"""
from pyskills.edit import (
    view_nb,
    view_cell,
    cell_str_replace,
    cell_strs_replace,
    cell_insert_line,
    cell_replace_lines,
    cell_del_lines,
    Notebook,
    mk_cell,
    read_nb,
    write_nb,
)

__all__ = [
    "view_nb",
    "view_cell",
    "cell_str_replace",
    "cell_strs_replace",
    "cell_insert_line",
    "cell_replace_lines",
    "cell_del_lines",
    "nb_add_cell",
    "nb_delete_cell",
    "Notebook",
    "mk_cell",
    "read_nb",
    "write_nb",
]


def nb_add_cell(
    path: str,
    source: str,
    cell_type: str = "code",
    idx: int = None
) -> str:
    """Add a new cell to notebook at `path`.
    
    Args:
        path: Path to .ipynb file
        source: Cell content
        cell_type: 'code' or 'markdown' (default: 'code')
        idx: Insert position (default: end)
    
    Returns:
        Status message with index of new cell.
    """
    nb = Notebook.open(path)
    cell = mk_cell(source, cell_type=cell_type)
    
    if idx is None:
        nb.cells.append(cell)
        idx = len(nb.cells) - 1
    else:
        nb.cells.insert(idx, cell)
    
    nb.save()
    return f"added {cell_type} cell at index {idx}"


def nb_delete_cell(path: str, idx: int) -> str:
    """Delete cell at index `idx` from notebook at `path`.
    
    Args:
        path: Path to .ipynb file
        idx: Cell index to delete
    
    Returns:
        Status message confirming deletion.
    """
    nb = Notebook.open(path)
    del nb[idx]
    nb.save()
    return f"deleted cell {idx}"