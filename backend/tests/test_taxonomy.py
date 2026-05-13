import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas import ProvisionCategory, ValuationImpact
from app.taxonomy import SPA_TAXONOMY, taxonomy_categories


def test_taxonomy_includes_all_provision_categories() -> None:
    assert set(taxonomy_categories()) == set(ProvisionCategory)
    assert set(SPA_TAXONOMY) == set(ProvisionCategory)


def test_taxonomy_items_have_required_metadata() -> None:
    required_fields = {
        "label",
        "description",
        "what_to_look_for",
        "common_signals",
        "commercial_importance",
        "typical_valuation_impacts",
    }

    for category, item in SPA_TAXONOMY.items():
        assert required_fields.issubset(item.keys()), category.value
        assert item["label"]
        assert item["description"]
        assert item["what_to_look_for"]
        assert item["common_signals"]
        assert item["commercial_importance"]
        assert item["typical_valuation_impacts"]
        assert all(isinstance(impact, ValuationImpact) for impact in item["typical_valuation_impacts"])
