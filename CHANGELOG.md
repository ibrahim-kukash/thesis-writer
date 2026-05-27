# Changelog

## v6.2.0 (2026-05-27)

Research-grounded 2026 update: re-based the lexical checks on current findings and added durable structural detection.

- **Pattern 28: Low punctuation entropy** — Shannon entropy over punctuation types; flags text that leans almost entirely on periods and commas. A structural tell that does not decay as models change (arXiv:2511.21744, arXiv:2510.00890).
- **Pattern 29: 2026 transition/opener crutches** — flags formulaic openers ("In conclusion," "It is important to note," "Notably," etc.). These replaced the 2023–24 vocabulary as the current-gen lexical tell after "delve" and similar words faded through 2025.
- **Time-versioned the banned-word list** — documented (with citation) that lexical tells decay: Kobak et al., *Science Advances* 2025 (arXiv:2406.07016, 14M PubMed abstracts). Low-frequency hits are now treated as weak signals.
- **Bug fix:** citation years are no longer counted as "specific numbers" — 4-digit years (1900–2099) are excluded, so a citation-heavy literature review no longer looks falsely number-rich.
- **Added `--json` flag** — emits only the JSON report (no human-readable text first), so output parses reliably.
- **Added a test suite** (`tests/test_ai_scan.py`) — pytest-compatible, also runnable standalone.

## v6.0.0 (2026-04-11)

- Added 4 structural patterns (based on MDPI 2025, Kujur 2025, Nature 2025 research):
  - Pattern 24: Repeated paragraph openings (>40% same opener)
  - Pattern 25: Template sentence frames ("Another X is", "First,", etc.)
  - Pattern 26: Hedging overuse (>15 per 1000 words)
  - Pattern 27: Logical connective imbalance (therefore/thus vs but/though)
- Added optional `--deep` flag for NLP analysis (requires spaCy)
  - Syntactic tree depth variation
  - POS tag diversity / noun-heavy style detection
- Falls back gracefully to stdlib checks if spaCy not installed

## v5.0.0 (2026-04-11)

- Full restructure following claude-skills authoring standard
- SKILL.md: practitioner voice, 3 modes (Write/Scan/Fix), proactive triggers, output artifacts table
- references/ai-patterns.md: 14 negative patterns (what to avoid) + 6 positive patterns (what to add)
- references/chapter-rules.md: chapter-by-chapter rules with examiner questions
- references/viva-questions.md: 35+ questions across 4 difficulty levels
- scripts/ai_scan.py: standalone scanner with scoring (0-100), violation detection, positive signal detection
- Sources: Wikipedia Signs of AI writing, Tercon 2025, Kujur 2025, GPTZero/Turnitin research
- README.md with install instructions and pattern table
- MIT license

## v4.0.0 (2026-04-11)

- Restructured as action-oriented skill with numbered patterns and before/after examples
- Added full worked example

## v3.0.0 (2026-04-11)

- Expanded from 240 to 577 lines
- Added viva questions, workflow, formatting, self-check system
- Still textbook-style (not action-oriented) — replaced by v4

## v1.0.0 (2026-04-05)

- Initial version: 240 lines
- Basic chapter structure rules and banned word list
