"""
Tests for ai_scan.py.

Run with pytest:   pytest tests/
Or standalone:     python tests/test_ai_scan.py
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from ai_scan import scan  # noqa: E402


def test_clean_academic_text_scores_high():
    """Well-punctuated, specific, varied academic prose should not be flagged as AI."""
    clean = (
        "Dust transport over the Gulf remains poorly constrained; satellite retrievals "
        "(MODIS) disagree with reanalysis by up to 40%. Why? Surface emission schemes are "
        "static. We tested three thresholds (0.15, 0.20, 0.25) against AERONET. The 0.20 cut "
        "performed best (F1 = 0.64), though it failed during the April 2021 event."
    )
    r = scan(clean)
    assert r["score"] >= 70, f"clean text scored too low: {r['score']}"


def test_banned_vocabulary_flagged():
    """Classic 2023-24 LLM vocabulary should trip pattern 1."""
    r = scan("This comprehensive and robust study delves into the intricate landscape.")
    pats = {v["pattern"] for v in r["violations"]}
    assert 1 in pats


def test_2026_crutches_flagged():
    """Formulaic 2026 openers/transitions should trip pattern 29."""
    slop = (
        "In conclusion, the model works. It is important to note the data is clean. "
        "Notably, accuracy is high. Importantly, recall is high. Overall, it works. "
        "Ultimately, it is sound. In summary, good. As a result, we are confident."
    )
    r = scan(slop)
    assert any(v["pattern"] == 29 for v in r["violations"])


def test_low_punctuation_entropy_flagged():
    """Text relying only on periods and commas (>150 words) should trip pattern 28."""
    base = (
        "The model was trained on the dataset, and the results were recorded. "
        "The accuracy was measured, the precision was computed, the recall was logged. "
    )
    r = scan(base * 8)
    assert any(v["pattern"] == 28 for v in r["violations"])
    assert r["stats"]["punctuation_entropy"] < 1.5


def test_citation_years_not_counted_as_numbers():
    """Citation years (e.g. 2024) must NOT inflate the 'specific numbers' count."""
    cites = "Smith (2024) found X. Jones (2019) found Y. Lee (2021) agreed. " * 4
    r = scan(cites)
    assert r["stats"]["numbers_per_100w"] == 0.0


def test_real_numbers_still_counted():
    """Genuine numeric values must still be counted after the year fix."""
    txt = "The RMSE was 0.11 and the bias was 0.04 across 1200 samples at 37 stations. " * 3
    r = scan(txt)
    assert r["stats"]["numbers_per_100w"] > 0


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
