#!/usr/bin/env python3
"""
AI Pattern Scanner for Academic Thesis Writing
Detects AI-generated writing patterns based on Wikipedia's "Signs of AI writing"
and flags violations with severity levels. Chapter-aware: adjusts thresholds
based on which chapter is being scanned.

Usage:
    python ai_scan.py <file.txt or file.docx>
    python ai_scan.py --chapter litreview <file>
    python ai_scan.py --chapter methodology <file>
    python ai_scan.py --chapter results <file>
    python ai_scan.py --chapter discussion <file>
    python ai_scan.py --text "paste text here"
    python ai_scan.py --stdin < file.txt

Chapters: intro, litreview, methodology, results, discussion, conclusion
If no chapter specified, uses general defaults.

Output: JSON report with violations, stats, and overall score (0-100).
"""
import sys
import re
import json
import math
from pathlib import Path
from collections import Counter

# ─── Banned vocabulary ───
BANNED_WORDS = [
    "delve", "crucial", "pivotal", "paramount", "vital", "cornerstone",
    "groundbreaking", "transformative", "indelible", "enduring",
    "tapestry", "paradigm shift", "interplay", "synergy",
    "comprehensive", "robust", "holistic", "multifaceted", "intricate",
    "meticulous", "nuanced", "myriad", "plethora",
    "utilize", "facilitate", "leverage", "garner", "underscore",
    "foster", "cultivate", "spearhead", "bolster",
    "vibrant", "profound", "showcasing", "exemplifies", "boasts",
    "renowned", "nestled", "advent",
]

# Only flag "landscape" when used figuratively (not geographic)
CONTEXT_BANNED = {
    "landscape": ["research landscape", "political landscape", "evolving landscape",
                   "current landscape", "broader landscape", "changing landscape"],
    "key": ["key role", "key factor", "key finding", "key aspect", "key element",
            "key challenge", "key contribution"],
}

FILLER_PHRASES = [
    "it is worth noting that", "it should be mentioned that",
    "it is important to note that", "in order to",
    "due to the fact that", "at this point in time",
    "plays a crucial role", "serves as a cornerstone",
    "a wide range of", "in recent years",
    "shed light on", "pave the way", "bridge the gap",
]

COPULA_AVOIDANCE = [
    "serves as", "stands as", "represents a", "marks a",
    "functions as", "acts as a",
]

TRANSITION_STARTERS = ["However,", "Moreover,", "Furthermore,", "Additionally,"]

ING_ENDINGS = [
    "highlighting the", "underscoring the", "emphasizing the",
    "contributing to the", "reflecting the", "symbolizing the",
    "showcasing the", "fostering the", "ensuring the",
]

# ─── Chapter profiles ───
# Based on published norms:
# - Passive voice: ~50%+ in methodology, ~20-30% overall (ScienceDirect 2025)
# - Citation density: lit review 3-5 per paragraph, methodology 1-2, results 0-1, discussion 2-3
# - Hedging: required in discussion, rare in methodology/results
# - Numbers: few in intro/litreview, many in methodology, required in results
CHAPTER_PROFILES = {
    "intro": {
        "name": "Introduction",
        "citations_per_para_min": 0.5,  # some paragraphs are context-setting
        "citations_per_para_max": 3,
        "numbers_per_100w_min": 0,      # broad context, fewer numbers OK
        "hedging_expected": "medium",    # some hedging for gap statement
        "passive_ok": False,            # prefer active in intro
        "comparison_required": False,    # not needed in intro
    },
    "litreview": {
        "name": "Literature Review",
        "citations_per_para_min": 1.5,  # every paragraph should cite
        "citations_per_para_max": 6,
        "numbers_per_100w_min": 0.5,    # some numbers from cited studies
        "hedging_expected": "medium",
        "passive_ok": False,
        "comparison_required": True,     # MUST compare, not describe
    },
    "methodology": {
        "name": "Methodology",
        "citations_per_para_min": 0.3,  # cite methods, not every paragraph
        "citations_per_para_max": 3,
        "numbers_per_100w_min": 1.5,    # lots of specifics: resolutions, thresholds, sizes
        "hedging_expected": "low",       # factual, not hedged
        "passive_ok": True,             # passive is correct here: "data were obtained"
        "comparison_required": False,
    },
    "results": {
        "name": "Results",
        "citations_per_para_min": 0,    # results are YOUR findings, few citations
        "citations_per_para_max": 1,
        "numbers_per_100w_min": 3,      # numbers required: metrics, values, counts
        "hedging_expected": "low",       # report facts, not interpretations
        "passive_ok": True,
        "comparison_required": False,
    },
    "discussion": {
        "name": "Discussion",
        "citations_per_para_min": 1,    # compare with literature
        "citations_per_para_max": 4,
        "numbers_per_100w_min": 1,      # reference your own numbers
        "hedging_expected": "high",      # interpretation requires hedging
        "passive_ok": False,
        "comparison_required": True,     # MUST compare with published work
    },
    "conclusion": {
        "name": "Conclusion",
        "citations_per_para_min": 0,    # no new citations
        "citations_per_para_max": 0.5,
        "numbers_per_100w_min": 1,      # restate key numbers
        "hedging_expected": "low",
        "passive_ok": False,
        "comparison_required": False,
    },
}


def parse_args(args):
    """Parse command line arguments. Returns (text, chapter_profile_or_None)."""
    chapter = None
    remaining = list(args[1:])

    # Extract --chapter flag
    if "--chapter" in remaining:
        idx = remaining.index("--chapter")
        if idx + 1 < len(remaining):
            ch_name = remaining[idx + 1].lower()
            if ch_name in CHAPTER_PROFILES:
                chapter = CHAPTER_PROFILES[ch_name]
            else:
                print(f"Unknown chapter: {ch_name}. Options: {', '.join(CHAPTER_PROFILES.keys())}", file=sys.stderr)
                sys.exit(1)
            remaining = remaining[:idx] + remaining[idx+2:]

    # Read text
    if len(remaining) >= 2 and remaining[0] == "--text":
        return " ".join(remaining[1:]), chapter
    if len(remaining) >= 1 and remaining[0] == "--stdin":
        return sys.stdin.read(), chapter
    if len(remaining) >= 1:
        path = Path(remaining[0])
        if path.suffix == ".docx":
            try:
                from docx import Document
                doc = Document(str(path))
                return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip()), chapter
            except ImportError:
                print("python-docx not installed. Install: pip install python-docx", file=sys.stderr)
                sys.exit(1)
        else:
            return path.read_text(encoding="utf-8"), chapter
    print(__doc__)
    sys.exit(0)


def split_sentences(text):
    """Split text into sentences (rough but functional)."""
    # Split on period/question/exclamation followed by space and capital
    raw = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in raw if len(s.strip()) > 5]


def scan(text, chapter=None):
    """Run all checks and return a report dict. chapter is a CHAPTER_PROFILES entry or None."""
    violations = []
    text_lower = text.lower()
    sentences = split_sentences(text)
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]
    word_count = len(text.split())

    # 1. Banned vocabulary
    for word in BANNED_WORDS:
        count = len(re.findall(r'\b' + re.escape(word) + r'\b', text_lower))
        if count > 0:
            violations.append({
                "pattern": 1, "name": "Banned vocabulary",
                "severity": "critical", "word": word, "count": count,
                "fix": f'Replace "{word}" with a plain alternative'
            })

    # 1b. Context-dependent banned words
    for word, contexts in CONTEXT_BANNED.items():
        for ctx in contexts:
            count = text_lower.count(ctx)
            if count > 0:
                violations.append({
                    "pattern": 1, "name": "Banned vocabulary (context)",
                    "severity": "medium", "word": ctx, "count": count,
                    "fix": f'Replace figurative use of "{word}"'
                })

    # 2. However chain
    transition_count = 0
    for t in TRANSITION_STARTERS:
        c = text.count(t)
        transition_count += c

    if word_count > 0 and transition_count / (word_count / 1000) > 3:
        violations.append({
            "pattern": 2, "name": "However chain",
            "severity": "critical",
            "detail": f'{transition_count} transition starters in {word_count} words ({transition_count/(word_count/1000):.1f} per 1000)',
            "fix": "Use subordinate clauses, mid-sentence qualifications, or plain conjunctions"
        })

    # Check for consecutive transition starters
    for i in range(len(sentences) - 1):
        s1_starts = any(sentences[i].startswith(t.rstrip(",")) for t in TRANSITION_STARTERS)
        s2_starts = any(sentences[i+1].startswith(t.rstrip(",")) for t in TRANSITION_STARTERS)
        if s1_starts and s2_starts:
            violations.append({
                "pattern": 2, "name": "Consecutive transitions",
                "severity": "critical",
                "detail": f'Back-to-back transition starters near: "{sentences[i][:50]}..."',
                "fix": "Restructure one of the sentences"
            })

    # 3. Sentence starter repetition
    if sentences:
        starters = [s.split()[0] for s in sentences if s.split()]
        starter_counts = Counter(starters)
        total = len(starters)
        for word, count in starter_counts.most_common(5):
            pct = count / total * 100
            if pct > 30 and word in ("The", "This", "These", "It", "There"):
                violations.append({
                    "pattern": 3, "name": "Sentence starter repetition",
                    "severity": "medium",
                    "detail": f'"{word}" starts {count}/{total} sentences ({pct:.0f}%)',
                    "fix": f"Vary sentence openers — {word} should start <30% of sentences"
                })

    # 4. Uniform sentence length
    if len(sentences) >= 5:
        lengths = [len(s.split()) for s in sentences]
        mean_len = sum(lengths) / len(lengths)
        std_len = math.sqrt(sum((l - mean_len) ** 2 for l in lengths) / len(lengths))
        if std_len < 5:
            violations.append({
                "pattern": 3, "name": "Uniform sentence length",
                "severity": "critical",
                "detail": f"Sentence length std dev = {std_len:.1f} (target: >5). Mean = {mean_len:.0f} words",
                "fix": "Mix short (5-8 word) and long (30-40 word) sentences deliberately"
            })

    # 5. Paragraph uniformity
    if len(paragraphs) >= 3:
        para_lengths = [len(p.split()) for p in paragraphs]
        mean_para = sum(para_lengths) / len(para_lengths)
        std_para = math.sqrt(sum((l - mean_para) ** 2 for l in para_lengths) / len(para_lengths))
        if std_para < 15:
            violations.append({
                "pattern": 4, "name": "Uniform paragraph length",
                "severity": "medium",
                "detail": f"Paragraph length std dev = {std_para:.1f} (target: >15). Mean = {mean_para:.0f} words",
                "fix": "Let some paragraphs be 2 sentences, others 6-8"
            })

    # 6. Copula avoidance
    for phrase in COPULA_AVOIDANCE:
        count = text_lower.count(phrase)
        if count > 0:
            violations.append({
                "pattern": 4, "name": "Copula avoidance",
                "severity": "medium", "word": phrase, "count": count,
                "fix": f'Replace "{phrase}" with "is" or "has"'
            })

    # 7. -ing endings
    for phrase in ING_ENDINGS:
        count = text_lower.count(phrase)
        if count > 0:
            violations.append({
                "pattern": 5, "name": "Superficial -ing ending",
                "severity": "medium", "word": phrase, "count": count,
                "fix": "Replace with a specific statement about what the finding means"
            })

    # 8. Em dash overuse
    em_dash_count = text.count("\u2014") + text.count(" -- ")
    pages_approx = max(1, word_count / 250)
    if em_dash_count / pages_approx > 2:
        violations.append({
            "pattern": 10, "name": "Em dash overuse",
            "severity": "minor",
            "detail": f"{em_dash_count} em dashes in ~{pages_approx:.0f} pages ({em_dash_count/pages_approx:.1f}/page)",
            "fix": "Use commas, parentheses, or restructure. Target: <2 per page"
        })

    # 9. Filler phrases
    for phrase in FILLER_PHRASES:
        count = text_lower.count(phrase)
        if count > 0:
            violations.append({
                "pattern": 11, "name": "Filler phrase",
                "severity": "minor", "word": phrase, "count": count,
                "fix": "Delete or simplify"
            })

    # 10. Rule of three (X, Y, and Z pattern)
    triples = re.findall(r'\b\w+,\s+\w+,\s+and\s+\w+', text)
    if len(triples) / max(1, len(paragraphs)) > 0.5:
        violations.append({
            "pattern": 6, "name": "Rule of three overuse",
            "severity": "minor",
            "detail": f"{len(triples)} triple constructions in {len(paragraphs)} paragraphs",
            "fix": "Vary list lengths — sometimes two items, sometimes four"
        })

    # 11. Clause density variation (Turnitin 2026)
    if len(sentences) >= 5:
        clause_counts = []
        for s in sentences:
            # Rough clause count: count commas, semicolons, "which", "that", "because", "although", "while"
            clauses = 1 + s.count(',') + s.count(';') + len(re.findall(r'\b(which|that|because|although|while|where|when)\b', s.lower()))
            clause_counts.append(min(clauses, 5))  # cap at 5
        clause_std = math.sqrt(sum((c - sum(clause_counts)/len(clause_counts))**2 for c in clause_counts) / len(clause_counts))
        if clause_std < 0.8:
            violations.append({
                "pattern": 21, "name": "Uniform clause density",
                "severity": "medium",
                "detail": f"Clause density std dev = {clause_std:.2f} (target: >0.8). Mix simple and complex sentences.",
                "fix": "Alternate between single-clause sentences and multi-clause ones"
            })

    # 12. Grammatical symmetry (consecutive sentences with same structure)
    if len(sentences) >= 4:
        # Check if 3+ consecutive sentences start with "The [noun] [verb]" pattern
        same_start_runs = 0
        for i in range(len(sentences) - 2):
            words_i = sentences[i].split()[:2]
            words_j = sentences[i+1].split()[:2]
            words_k = sentences[i+2].split()[:2]
            if len(words_i) >= 2 and len(words_j) >= 2 and len(words_k) >= 2:
                if words_i[0] == words_j[0] == words_k[0]:
                    same_start_runs += 1
        if same_start_runs > 0:
            violations.append({
                "pattern": 23, "name": "Grammatical symmetry",
                "severity": "medium",
                "detail": f"{same_start_runs} run(s) of 3+ sentences with identical opening word",
                "fix": "Vary sentence openings — rearrange clauses, use different subjects"
            })

    # ─── POSITIVE CHECKS (human signals) ───

    positive_signals = []

    # 15. Punctuation variety
    punct_types = set()
    for ch in text:
        if ch in '.!?,;:()?"\'':
            punct_types.add(ch)
    if len(punct_types) >= 5:
        positive_signals.append({"pattern": 15, "name": "Punctuation variety", "detail": f"{len(punct_types)} types used"})
    elif len(punct_types) <= 2 and word_count > 100:
        violations.append({
            "pattern": 15, "name": "Low punctuation variety",
            "severity": "medium",
            "detail": f"Only {len(punct_types)} punctuation types (commas and periods only). Humans use semicolons, colons, parentheses, questions.",
            "fix": "Add semicolons, colons, or parentheses where natural"
        })

    # 16. Field-specific idioms
    idioms = ["at odds with", "on closer inspection", "taken at face value", "at first glance",
              "the picture that emerges", "a closer look", "fell short", "begs the question",
              "remains to be seen", "broadly consistent", "in keeping with", "by the same token",
              "to put it differently", "that said"]
    idiom_count = sum(1 for idiom in idioms if idiom in text_lower)
    if idiom_count >= 1:
        positive_signals.append({"pattern": 16, "name": "Academic idioms present", "detail": f"{idiom_count} found"})

    # 18. Genuine uncertainty expressions
    uncertainty = ["remains unclear", "difficult to explain", "cannot fully resolve",
                   "remains a concern", "open question", "not yet understood",
                   "beyond the scope", "we do not know", "it is unclear",
                   "the reasons are not well understood", "this is speculative"]
    uncert_count = sum(1 for u in uncertainty if u in text_lower)
    if uncert_count >= 1:
        positive_signals.append({"pattern": 18, "name": "Genuine uncertainty", "detail": f"{uncert_count} expressions"})

    # 19. Paragraph length variety (positive check)
    if len(paragraphs) >= 3:
        has_short = any(len(p.split()) < 40 for p in paragraphs)
        has_long = any(len(p.split()) > 100 for p in paragraphs)
        if has_short and has_long:
            positive_signals.append({"pattern": 19, "name": "Paragraph length variety", "detail": "Mix of short and long paragraphs"})

    # 20. Specific numbers
    numbers_in_text = re.findall(r'\b\d+\.?\d*\b', text)
    numbers_per_100 = len(numbers_in_text) / max(1, word_count / 100)
    if numbers_per_100 >= 2:
        positive_signals.append({"pattern": 20, "name": "Specific numbers used", "detail": f"{len(numbers_in_text)} numbers ({numbers_per_100:.1f} per 100 words)"})
    elif numbers_per_100 < 0.5 and word_count > 200:
        violations.append({
            "pattern": 20, "name": "Lack of specificity",
            "severity": "medium",
            "detail": f"Only {len(numbers_in_text)} numbers in {word_count} words. Academic writing needs specific values.",
            "fix": "Replace vague claims ('improved significantly') with numbers ('RMSE decreased from 0.15 to 0.11')"
        })

    # ─── CHAPTER-SPECIFIC CHECKS ───
    if chapter and word_count > 100:
        ch_name = chapter["name"]

        # Citation density check (rough: count "(YYYY)" and "(Author" patterns)
        citation_count = len(re.findall(r'\(\d{4}\)', text)) + len(re.findall(r'et al\.', text))
        cit_per_para = citation_count / max(1, len(paragraphs))
        expected_min = chapter["citations_per_para_min"]
        expected_max = chapter["citations_per_para_max"]

        if cit_per_para < expected_min:
            violations.append({
                "pattern": "CH", "name": f"Low citation density for {ch_name}",
                "severity": "medium",
                "detail": f"{citation_count} citations in {len(paragraphs)} paragraphs ({cit_per_para:.1f}/para). {ch_name} expects >{expected_min:.1f}/para.",
                "fix": f"Add more citations — {ch_name} chapters typically have {expected_min:.0f}-{expected_max:.0f} per paragraph"
            })
        elif cit_per_para > expected_max + 2:
            violations.append({
                "pattern": "CH", "name": f"Excessive citation density for {ch_name}",
                "severity": "minor",
                "detail": f"{cit_per_para:.1f} citations/para. {ch_name} typically has <{expected_max:.0f}/para.",
                "fix": "Not every sentence needs a citation — some should be your own analysis"
            })

        # Numbers check
        numbers_min = chapter["numbers_per_100w_min"]
        if numbers_per_100 < numbers_min:
            violations.append({
                "pattern": "CH", "name": f"Too few numbers for {ch_name}",
                "severity": "medium",
                "detail": f"{numbers_per_100:.1f} numbers per 100 words. {ch_name} expects >{numbers_min:.1f}.",
                "fix": "Add specific values — metrics, counts, thresholds, percentages"
            })

        # Comparison check (lit review and discussion)
        if chapter["comparison_required"]:
            compare_words = ["in contrast", "unlike", "whereas", "while", "although",
                            "consistent with", "contradicts", "agrees with", "differs from",
                            "compared to", "relative to", "better than", "worse than"]
            compare_count = sum(1 for w in compare_words if w in text_lower)
            if compare_count < 2 and len(paragraphs) >= 3:
                violations.append({
                    "pattern": "CH", "name": f"Insufficient comparison for {ch_name}",
                    "severity": "critical",
                    "detail": f"Only {compare_count} comparative expressions. {ch_name} must compare, contrast, and critique — not just describe.",
                    "fix": "Add comparisons between studies or between your results and published work"
                })

    # Score: 100 minus deductions, plus bonuses for positive signals
    critical_count = sum(1 for v in violations if v["severity"] == "critical")
    medium_count = sum(1 for v in violations if v["severity"] == "medium")
    minor_count = sum(1 for v in violations if v["severity"] == "minor")
    bonus = min(15, len(positive_signals) * 3)  # up to 15 bonus points
    score = max(0, min(100, 100 - (critical_count * 15) - (medium_count * 5) - (minor_count * 2) + bonus))

    return {
        "score": score,
        "word_count": word_count,
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "violations": violations,
        "positive_signals": positive_signals,
        "summary": {
            "critical": critical_count,
            "medium": medium_count,
            "minor": minor_count,
            "positive": len(positive_signals),
            "total_violations": len(violations),
        },
        "stats": {
            "sentence_length_mean": round(sum(len(s.split()) for s in sentences) / max(1, len(sentences)), 1),
            "sentence_length_std": round(math.sqrt(sum((len(s.split()) - sum(len(s.split()) for s in sentences) / max(1, len(sentences))) ** 2 for s in sentences) / max(1, len(sentences))), 1) if sentences else 0,
            "however_per_1000": round(transition_count / max(1, word_count / 1000), 1),
            "em_dashes": em_dash_count,
            "punctuation_types": len(punct_types),
            "numbers_per_100w": round(numbers_per_100, 1),
        }
    }


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    text, chapter = parse_args(sys.argv)
    report = scan(text, chapter)

    # Print human-readable summary
    print(f"\n{'='*60}")
    ch_label = f" [{chapter['name']}]" if chapter else ""
    print(f"THESIS AI SCAN REPORT{ch_label}")
    print(f"{'='*60}")
    print(f"Score: {report['score']}/100")
    print(f"Words: {report['word_count']} | Sentences: {report['sentence_count']} | Paragraphs: {report['paragraph_count']}")
    print(f"Violations: {report['summary']['critical']} critical, {report['summary']['medium']} medium, {report['summary']['minor']} minor")
    print(f"\nStats:")
    for k, v in report['stats'].items():
        print(f"  {k}: {v}")

    if report['violations']:
        print(f"\n{'-'*60}")
        print("VIOLATIONS:")
        for v in report['violations']:
            icon = {"critical": "[X]", "medium": "[!]", "minor": "[i]"}.get(v['severity'], "?")
            print(f"\n  {icon} [{v['severity'].upper()}] Pattern {v['pattern']}: {v['name']}")
            if 'word' in v:
                print(f"    Found: \"{v['word']}\" ({v.get('count', '?')}x)")
            if 'detail' in v:
                print(f"    Detail: {v['detail']}")
            print(f"    Fix: {v['fix']}")

    if report.get('positive_signals'):
        print(f"\n{'-'*60}")
        print("POSITIVE SIGNALS (human writing indicators):")
        for p in report['positive_signals']:
            print(f"  [+] Pattern {p['pattern']}: {p['name']} - {p['detail']}")

    print(f"\n{'='*60}")
    if report['score'] >= 80:
        print("PASS - Low AI detection risk")
    elif report['score'] >= 50:
        print("WARNING - Moderate AI detection risk. Fix critical violations.")
    else:
        print("FAIL - High AI detection risk. Major rewrite needed.")
    print(f"{'='*60}\n")

    # Also output JSON for programmatic use
    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
