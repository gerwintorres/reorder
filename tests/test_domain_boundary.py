import subprocess
import sys

FORBIDDEN = {"fastapi", "pydantic", "sqlalchemy", "pandas", "numpy"}

# Importing reorder.domain alone only runs its empty __init__.py, so every
# module in the package is imported explicitly before checking.
CHECK = f"""
import importlib, pkgutil, sys
import reorder.domain as domain
for module in pkgutil.iter_modules(domain.__path__):
    importlib.import_module(f"reorder.domain.{{module.name}}")
found = {FORBIDDEN!r} & set(sys.modules)
assert not found, f"domain imports {{sorted(found)}}"
"""


def test_domain_does_not_import_frameworks() -> None:
    # A fresh interpreter: pytest's own process may already have these modules
    # loaded by other tests, which would make the check meaningless.
    result = subprocess.run(
        [sys.executable, "-c", CHECK], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
