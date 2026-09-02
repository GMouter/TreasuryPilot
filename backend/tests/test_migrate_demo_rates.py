import importlib.util
from pathlib import Path


migration_path = Path(__file__).parents[2] / "scripts" / "migrate_demo_rates.py"
migration_spec = importlib.util.spec_from_file_location("migrate_demo_rates", migration_path)
migration_module = importlib.util.module_from_spec(migration_spec)
migration_spec.loader.exec_module(migration_module)
DEMO_RATE_FIXES = migration_module.DEMO_RATE_FIXES


def test_demo_rate_fixes_use_gbp_per_foreign_unit_quotes():
    assert DEMO_RATE_FIXES["Northstar Imports Ltd"]["USD"] == 0.79
    assert DEMO_RATE_FIXES["Alpine Components GmbH"]["GBP"] == 1.16
    assert DEMO_RATE_FIXES["Orbit Systems Inc"]["JPY"] == 0.0067


def test_rate_fix_targets_only_known_demo_companies():
    assert set(DEMO_RATE_FIXES) == {
        "Northstar Imports Ltd",
        "Alpine Components GmbH",
        "Orbit Systems Inc",
        "Harbour & Field Co",
    }
