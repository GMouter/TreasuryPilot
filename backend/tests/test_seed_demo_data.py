import importlib.util
from pathlib import Path


seed_path = Path(__file__).parents[2] / "scripts" / "seed_demo_data.py"
seed_spec = importlib.util.spec_from_file_location("seed_demo_data", seed_path)
seed_module = importlib.util.module_from_spec(seed_spec)
seed_spec.loader.exec_module(seed_module)
DEMO_COMPANIES = seed_module.DEMO_COMPANIES


def test_demo_data_has_diverse_company_profiles():
    assert len(DEMO_COMPANIES) == 4
    assert len({company["base_currency"] for company in DEMO_COMPANIES}) >= 3
    assert len({company["country"] for company in DEMO_COMPANIES}) >= 3


def test_demo_exposures_cover_multiple_risk_shapes():
    exposures = [
        exposure
        for company in DEMO_COMPANIES
        for exposure in company["exposures"]
    ]

    assert len(exposures) >= 8
    assert len({exposure[0] for exposure in exposures}) >= 4
    assert min(exposure[3] for exposure in exposures) <= 30
    assert max(exposure[3] for exposure in exposures) >= 180
    assert min(exposure[4] for exposure in exposures) < 50
    assert max(exposure[4] for exposure in exposures) >= 90
