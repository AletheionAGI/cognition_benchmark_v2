"""
Auto-import de todas as categorias de teste.
Importar este modulo registra todos os 30 testes.
"""

from .test_defs import (
    TestDef,
    StructuralCheck,
    get_all_tests,
    get_test,
    get_tests_by_category,
    get_categories,
)

# Auto-registro: importar cada modulo dispara register_tests()
from . import self_correction  # noqa: F401
from . import epistemic_cal  # noqa: F401
from . import factual_grounding  # noqa: F401
from . import contradiction  # noqa: F401
from . import task_adaptation  # noqa: F401
from . import citation_integrity  # noqa: F401

__all__ = [
    "TestDef",
    "StructuralCheck",
    "get_all_tests",
    "get_test",
    "get_tests_by_category",
    "get_categories",
]
