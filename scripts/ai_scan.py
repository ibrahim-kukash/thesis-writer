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
    python ai_scan.py --deep <file>           # enables optional NLP checks (needs spacy)
    python ai_scan.py --text "paste text here"
    python ai_scan.py --stdin < file.txt
    python ai_scan.py --json <file>           # emit ONLY the JSON report (clean, parseable)

Chapters: intro, litreview, methodology, results, discussion, conclusion
If no chapter specified, uses general defaults.

Deep mode: if spacy is installed, adds structural/semantic checks for
syntactic tree depth and discourse coherence. Falls back to stdlib
checks automatically if spacy is unavailable.

Output: JSON report with violations, stats, and overall score (0-100).
"""
import sys
import re
import json
import math
from pathlib import Path
from collections import Counter

# ─── Banned vocabulary (2023–24 lexical markers) ───
# Source: Kobak et al., "Delving into LLM-assisted writing in biomedical publications
# through excess vocabulary," Science Advances 2025 (arXiv:2406.07016; 14M PubMed
# abstracts, 2010–2024). The highest-ratio excess words were delves (~25x), showcasing
# (~9x) and underscores (~9x).
# CAVEAT: lexical tells decay as labs train them out. "delve" peaked in 2023–24 and
# faded through 2025, so a low-frequency hit here is only a WEAK signal in 2026. The
# durable signals are structural (sentence-length burstiness, punctuation entropy,
# clause density) — see patterns 21, 23, 28 and arXiv:2511.21744 / arXiv:2510.00890.
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

# ─── 2026 transition/opener crutches ───
# Post-"delve" era: as labs trained out the 2023–24 vocabulary, current-gen models
# leaned on formulaic transitions/openers instead (completeaitraining 2026 survey;
# Wikipedia "Signs of AI writing"). These are now the more reliable lexical tell.
LLM_2026_CRUTCHES = [
    "in conclusion,", "it is important to note", "it's important to note",
    "in summary,", "overall,", "ultimately,", "notably,", "importantly,",
    "as a result,", "to summarize,",
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
    """Parse command line arguments. Returns (text, chapter_profile_or_None, deep_mode, json_only)."""
    chapter = None
    deep = False
    json_only = False
    remaining = list(args[1:])

    # Extract --deep flag
    if "--deep" in remaining:
        deep = True
        remaining.remove("--deep")

    # Extract --json flag (emit only the JSON report, no human-readable text)
    if "--json" in remaining:
        json_only = True
        remaining.remove("--json")

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
        return " ".join(remaining[1:]), chapter, deep, json_only
    if len(remaining) >= 1 and remaining[0] == "--stdin":
        return sys.stdin.read(), chapter, deep, json_only
    if len(remaining) >= 1:
        path = Path(remaining[0])
        if path.suffix == ".docx":
            try:
                from docx import Document
                doc = Document(str(path))
                return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip()), chapter, deep, json_only
            except ImportError:
                print("python-docx not installed. Install: pip install python-docx", file=sys.stderr)
                sys.exit(1)
        else:
            return path.read_text(encoding="utf-8"), chapter, deep, json_only
    print(__doc__)
    sys.exit(0)


def deep_analysis(text, sentences):
    """Optional NLP analysis using spaCy. Returns list of deep violations.
    Falls back gracefully if spaCy or language model is not available."""
    deep_violations = []
    try:
        import spacy
    except ImportError:
        return [{"pattern": "DEEP", "name": "spaCy not installed",
                 "severity": "info",
                 "detail": "Install spacy + language model for deep mode: pip install spacy && python -m spacy download en_core_web_sm",
                 "fix": "Running stdlib checks only"}]

    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        return [{"pattern": "DEEP", "name": "spaCy model not downloaded",
                 "severity": "info",
                 "detail": "Run: python -m spacy download en_core_web_sm",
                 "fix": "Running stdlib checks only"}]

    doc = nlp(text[:100000])  # cap at 100k chars for memory

    # Syntactic tree depth variation
    depths = []
    for sent in doc.sents:
        def tree_depth(token):
            children = list(token.children)
            if not children:
                return 1
            return 1 + max(tree_depth(child) for child in children)
        root = [t for t in sent if t.head == t]
        if root:
            depths.append(tree_depth(root[0]))
    if depths:
        depth_std = (sum((d - sum(depths)/len(depths))**2 for d in depths) / len(depths)) ** 0.5
        if depth_std < 1.5 and len(depths) > 20:
            deep_violations.append({
                "pattern": "D1", "name": "Uniform syntactic depth",
                "severity": "medium",
                "detail": f"Syntactic tree depth std = {depth_std:.2f} (human writing typically >1.5). Sentence structures are too similar.",
                "fix": "Add complex embedded clauses OR simple short sentences"
            })

    # POS tag diversity
    pos_counts = Counter(token.pos_ for token in doc if not token.is_punct and not token.is_space)
    total_pos = sum(pos_counts.values())
    if total_pos > 0:
        noun_ratio = (pos_counts.get("NOUN", 0) + pos_counts.get("PROPN", 0)) / total_pos
        verb_ratio = pos_counts.get("VERB", 0) / total_pos
        if noun_ratio > 0.35:
            deep_violations.append({
                "pattern": "D2", "name": "Noun-heavy style",
                "severity": "minor",
                "detail": f"Nouns are {noun_ratio*100:.0f}% of content words. AI-generated academic text skews noun-heavy (nominalizations).",
                "fix": "Convert nominalizations to verbs: 'the investigation of' → 'we investigated'"
            })

    return deep_violations


def split_sentences(text):
    """Split text into sentences (rough but functional)."""
    # Split on period/question/exclamation followed by space and capital
    raw = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in raw if len(s.strip()) > 5]


def scan(text, chapter=None, deep=False):
    """Run all checks and return a report dict. chapter is a CHAPTER_PROFILES entry or None.
    If deep=True, also run NLP-based checks (requires spaCy)."""
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

    # 20. Specific numbers (exclude 4-digit citation years, which otherwise inflate
    # the count and make a citation-heavy lit review look falsely number-rich)
    all_numbers = re.findall(r'\b\d+\.?\d*\b', text)
    numbers_in_text = [n for n in all_numbers if not re.fullmatch(r'(19|20)\d{2}', n)]
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

    # ─── STRUCTURAL CHECKS (Patterns 24-27) ───
    # Based on: MDPI 2025 (AI structural uniformity), Kujur 2025 (cohesion), Nature 2025 (hedging overuse)

    # 24. Repeated paragraph openings
    if len(paragraphs) >= 5:
        para_first_words = [p.split()[0] for p in paragraphs if p.split()]
        opener_counts = Counter(para_first_words)
        most_common_opener, count = opener_counts.most_common(1)[0]
        pct = count / len(paragraphs) * 100
        if count >= 5 and pct > 40:
            violations.append({
                "pattern": 24, "name": "Repeated paragraph openings",
                "severity": "medium",
                "detail": f'"{most_common_opener}" opens {count}/{len(paragraphs)} paragraphs ({pct:.0f}%)',
                "fix": "Vary how paragraphs start — use questions, evidence, or contrast as openers"
            })

    # 25. Template sentence frames across paragraphs
    templates = [
        r'^Another\s+\w+\s+is',
        r'^The\s+\w+\s+is\s+\w+',
        r'^First,', r'^Second,', r'^Third,',
        r'^One\s+\w+\s+is', r'^This\s+approach',
    ]
    template_hits = 0
    for tmpl in templates:
        template_hits += len([s for s in sentences if re.match(tmpl, s)])
    if template_hits >= 4 and len(sentences) > 30:
        violations.append({
            "pattern": 25, "name": "Template sentence frames",
            "severity": "medium",
            "detail": f'{template_hits} sentences use rigid template frames (e.g., "Another X is", "First,", "The X is")',
            "fix": "Replace at least half with more varied constructions"
        })

    # 26. Hedging overuse
    hedges = ['may', 'might', 'could', 'possibly', 'perhaps', 'likely',
              'suggest', 'suggests', 'indicate', 'indicates', 'appears', 'appear',
              'seem', 'seems', 'potentially', 'arguably']
    hedge_count = 0
    for h in hedges:
        hedge_count += len(re.findall(r'\b' + h + r'\b', text_lower))
    hedges_per_1000 = hedge_count / max(1, word_count / 1000)
    if hedges_per_1000 > 15:
        violations.append({
            "pattern": 26, "name": "Hedging overuse",
            "severity": "medium",
            "detail": f'{hedge_count} hedging words in {word_count} words ({hedges_per_1000:.1f}/1000). AI over-hedges.',
            "fix": "Remove hedges from established facts. Hedge only interpretive claims."
        })

    # 27. Connective balance (logical vs narrative)
    logical_conn = ['therefore', 'thus', 'hence', 'consequently', 'accordingly']
    narrative_conn = ['but', 'though', 'although', 'anyway', 'still', 'yet', 'despite']
    logical_count = sum(len(re.findall(r'\b' + c + r'\b', text_lower)) for c in logical_conn)
    narrative_count = sum(len(re.findall(r'\b' + c + r'\b', text_lower)) for c in narrative_conn)
    if logical_count >= 5 and logical_count > narrative_count * 2:
        violations.append({
            "pattern": 27, "name": "Logical connective imbalance",
            "severity": "minor",
            "detail": f'{logical_count} logical connectives (therefore/thus/hence) vs {narrative_count} narrative (but/though/yet). AI skews logical.',
            "fix": "Replace some 'therefore' with 'but' or 'though' where the contrast fits"
        })

    # 28. Punctuation entropy (durable stylometric signal; arXiv:2511.21744, 2510.00890)
    # Human writing uses a varied punctuation mix; AI leans heavily on periods + commas,
    # giving low Shannon entropy over punctuation types. Unlike word lists, this does not
    # decay as models change, so it is a more future-proof check.
    punct_chars = [c for c in text if c in '.,;:!?()-—"‘’“”']
    p_entropy = 0.0
    if punct_chars:
        pcounts = Counter(punct_chars)
        tot_p = sum(pcounts.values())
        p_entropy = -sum((n / tot_p) * math.log2(n / tot_p) for n in pcounts.values())
    if word_count > 150 and p_entropy < 1.5:
        violations.append({
            "pattern": 28, "name": "Low punctuation entropy",
            "severity": "medium",
            "detail": f"Punctuation entropy {p_entropy:.2f} bits (target >1.5). Text leans almost entirely on periods and commas — a robotic-rhythm tell.",
            "fix": "Introduce semicolons, colons, parentheses, or dashes where natural"
        })

    # 29. 2026 transition/opener crutches (post-'delve' era)
    crutch_hits = sum(text_lower.count(c) for c in LLM_2026_CRUTCHES)
    crutch_per_1000 = crutch_hits / max(1, word_count / 1000)
    if crutch_hits >= 2 and crutch_per_1000 > 4:
        violations.append({
            "pattern": 29, "name": "Formulaic transition/opener crutches (2026)",
            "severity": "medium",
            "detail": f"{crutch_hits} formulaic openers/transitions ({crutch_per_1000:.1f}/1000 words), e.g. 'In conclusion,', 'It is important to note', 'Notably,'. The current-gen tell now that 2023-24 vocabulary has faded.",
            "fix": "Cut or vary formulaic openers; start sentences with evidence or specifics"
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

    # ─── DEEP MODE (optional, uses spaCy) ───
    deep_notes = []
    if deep:
        deep_violations = deep_analysis(text, sentences)
        for dv in deep_violations:
            if dv.get("severity") == "info":
                deep_notes.append(dv)
            else:
                violations.append(dv)

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
            "punctuation_entropy": round(p_entropy, 2),
            "numbers_per_100w": round(numbers_per_100, 1),
        }
    }


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    text, chapter, deep, json_only = parse_args(sys.argv)
    report = scan(text, chapter, deep)

    # Machine-readable mode: emit only clean JSON (no human-readable text before it)
    if json_only:
        json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
        print()
        return

    # Print human-readable summary
    print(f"\n{'='*60}")
    ch_label = f" [{chapter['name']}]" if chapter else ""
    deep_label = " [DEEP]" if deep else ""
    print(f"THESIS AI SCAN REPORT{ch_label}{deep_label}")
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
