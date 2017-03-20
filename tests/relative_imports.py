from typing import List

from . import another_sibling_module
from .. import another_parent_module


def fun(
    elements: List[another_sibling_module.Element]
) -> another_parent_module.Class:
    return another_parent_module.Class(elements=elements)
