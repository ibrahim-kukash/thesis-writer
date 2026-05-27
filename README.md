# thesis-writer

Write publication-quality MSc/PhD thesis chapters that pass examiner scrutiny and AI detection tools.

## What it does

- **Writes** thesis chapters following academic conventions, with proper hedging, citations, and chapter structure
- **Scans** existing text for 14 AI writing patterns (based on [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing))
- **Fixes** flagged patterns while preserving meaning and citations
- **Prepares** for viva with 35+ categorised examiner questions

## Install

```bash
# Claude Code
claude skill add /path/to/thesis-writer

# Or clone and point to it
git clone https://github.com/futureweapons2022-crypto/thesis-writer.git ~/.claude/skills/thesis-writer
```

## Usage

```
# In Claude Code
/thesis-writer write chapter 2 section 2.1

/thesis-writer scan my-chapter.docx

/thesis-writer prepare for viva
```

### Standalone AI scanner

```bash
python scripts/ai_scan.py thesis_draft.docx
python scripts/ai_scan.py --text "paste your text here"
```

Output:
```
============================================================
THESIS AI SCAN REPORT
============================================================
Score: 72/100
Words: 2515 | Sentences: 89 | Paragraphs: 29
Violations: 2 critical, 3 medium, 1 minor

VIOLATIONS:

  ❌ [CRITICAL] Pattern 1: Banned vocabulary
    Found: "comprehensive" (2x)
    Fix: Replace with a plain alternative

  ⚠️ [MEDIUM] Pattern 2: However chain
    Detail: 5 transition starters in 2515 words (2.0 per 1000)
    Fix: Use subordinate clauses or plain conjunctions
```

## What's inside

```
thesis-writer/
├── SKILL.md                        # Main skill (3 modes: Write, Scan, Fix)
├── README.md
├── LICENSE
├── references/
│   ├── ai-patterns.md              # 14 patterns to avoid + 9 human-writing signals
│   ├── chapter-rules.md            # Chapter-by-chapter writing rules
│   └── viva-questions.md           # 35+ examiner questions by difficulty
└── scripts/
    └── ai_scan.py                  # Standalone AI pattern scanner (stdlib only)
```

## The 14 AI patterns it catches

| # | Pattern | Severity | Example tell |
|---|---------|----------|-------------|
| 1 | Banned vocabulary | Critical | "delve," "comprehensive," "leverage" |
| 2 | However chain | Critical | However, / Moreover, / Furthermore, back-to-back |
| 3 | Uniform sentence length | Critical | Every sentence 20-25 words |
| 4 | Copula avoidance | Medium | "serves as" instead of "is" |
| 5 | Superficial -ing endings | Medium | "highlighting the importance of..." |
| 6 | Rule of three | Minor | "X, Y, and Z" in every paragraph |
| 7 | Synonym cycling | Medium | Same concept, different words each time |
| 8 | Negative parallelisms | Minor | "Not just X, but also Y" |
| 9 | False ranges | Minor | "From X to Y, from A to B" |
| 10 | Em dash overuse | Minor | More than 2 per page |
| 11 | Filler phrases | Minor | "It is worth noting that..." |
| 12 | Formulaic endings | Medium | "These findings highlight the importance..." |
| 13 | Generic attribution | Medium | "Several studies have shown..." |
| 14 | Descriptive lit review | Critical | Listing studies without comparing them |

## Anti-AI detection approach

Based on how detectors work:

- **Perplexity**: AI text is too predictable. The skill forces less obvious word choices.
- **Burstiness**: AI sentences are too uniform. The skill enforces dramatic length variation (5-word and 40-word sentences in the same paragraph).

Non-native English speakers face 61% false positive rates in AI detectors. This skill is especially useful for international students.

## Research basis

The patterns are grounded in published work — and deliberately updated as the models change:

- **Lexical tells** (the banned-word list) come from Kobak et al., *Delving into LLM-assisted writing in biomedical publications through excess vocabulary*, **Science Advances 2025** ([arXiv:2406.07016](https://arxiv.org/abs/2406.07016)) — a 14M-abstract study of which words surged after ChatGPT (*delves* ×25, *showcasing* ×9, *underscores* ×9).
- **These tells decay.** "delve" peaked in 2023–24 and faded through 2025 as labs trained it out, so current-gen models lean on formulaic transitions instead — "In conclusion," "It is important to note," "Notably" — flagged separately (pattern 29).
- **The durable signals are structural, not lexical:** sentence-length burstiness, clause-density variation, and **punctuation entropy** (pattern 28). Stylometric research ([arXiv:2511.21744](https://arxiv.org/abs/2511.21744), [arXiv:2510.00890](https://arxiv.org/abs/2510.00890)) finds combined structural features reach F1 ≈ 0.94, well above perplexity alone — and unlike word lists, they don't expire.

> **Honest caveat:** even the best stylometric detectors top out at ~80–95% accuracy and drop when text is edited. Treat this as a guide, not proof.

## Credits

- AI patterns based on [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) by WikiProject AI Cleanup
- Viva questions compiled from University of Calgary, Oxford, and Edinburgh examiner guides
- Skill structure follows the [claude-skills authoring standard](https://github.com/alirezarezvani/claude-skills)

## License

MIT
