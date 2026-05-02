# Anti-AI Patterns for Academic Thesis Writing

Based on:
- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) (WikiProject AI Cleanup, 2025)
- Tercon (2025) "Linguistic Characteristics of AI-Generated Text: A Survey" (arXiv:2510.05136)
- Kujur (2025) "A Comparative Analysis of AI-Generated and Human-Written Text" (SSRN)

AI detectors measure **perplexity** (word predictability — AI median 21.2, human median 35.9) and **burstiness** (sentence length variation — AI is too uniform). Non-native English speakers face 61% false positive rates because simple syntax mimics AI patterns.

## PART A: What to AVOID (detection patterns)

The 14 patterns below are things AI does that humans don't. Remove them.

---

## 1. Banned Vocabulary

**Watch words:** delve, crucial, pivotal, paramount, vital, key (adjective), cornerstone, groundbreaking, transformative, indelible, enduring, landscape (figurative), tapestry, paradigm shift, interplay, synergy, ecosystem (figurative), comprehensive, robust, holistic, multifaceted, intricate, meticulous, nuanced, myriad, plethora, utilize, facilitate, leverage, garner, underscore, foster, cultivate, spearhead, bolster, vibrant, profound, showcasing, exemplifies, boasts, renowned, nestled, advent

**Problem:** Measurably higher frequency in post-2023 AI text. Detectors flag them.

**Before:**
> This study delves into the intricate interplay between dust emissions and meteorological conditions, leveraging a comprehensive dataset to facilitate a robust understanding of the multifaceted challenges.

**After:**
> This study examines the relationship between dust emissions and meteorological conditions using 10 years of station observations and reanalysis data across seven sites in the Arabian Gulf.

---

## 2. The However Chain

**Watch words:** However, / Moreover, / Furthermore, / Additionally, starting consecutive sentences

**Problem:** The single biggest AI tell in academic writing.

**Before:**
> CAMS performs well at coastal stations. However, performance degrades inland. Moreover, high-AOD events are systematically underestimated. Furthermore, near-source regions show the largest errors.

**After:**
> CAMS performs well at coastal stations, but performance degrades inland. High-AOD events are systematically underestimated — a pattern most pronounced near source regions, where seasonal biases compound the problem.

---

## 3. Uniform Sentence Length

**Problem:** AI produces sentences of 20-25 words consistently. Humans vary wildly.

**Before:**
> The model was trained on seven years of data. The test period covered four additional years. The features included meteorological variables. The target variable was binary forecast reliability.

**After:**
> Training covered 2015–2020. The test period — 2021 through 2024 — was deliberately chosen to include the anomalous 2022 dust season. Fifty-nine features went in. One binary label came out: reliable or not.

---

## 4. Copula Avoidance

**Watch words:** serves as, stands as, represents a, marks a, functions as, features, boasts, offers

**Problem:** AI substitutes elaborate constructions for "is" and "has."

**Before:**
> The Mesopotamian flood plain serves as a major dust source. AERONET represents the gold standard.

**After:**
> The Mesopotamian flood plain is a major dust source. AERONET is the gold standard.

---

## 5. Superficial -ing Endings

**Watch words:** highlighting the importance of, underscoring the need for, emphasizing the role of, contributing to the growing body of, reflecting broader trends

**Problem:** AI tacks present participle phrases onto sentences to add fake depth.

**Before:**
> The meta-model achieved an AUC of 0.87, highlighting the importance of meteorological predictors in identifying forecast failures, underscoring the potential for operational implementation.

**After:**
> The meta-model achieved an AUC of 0.87. Meteorological predictors — particularly boundary layer height and low-level wind speed — drove most of the discrimination.

---

## 6. Rule of Three

**Problem:** AI forces ideas into triads. "X, Y, and Z" every paragraph.

**Before:**
> Dust storms affect health, infrastructure, and economic productivity. The model captures spatial, temporal, and meteorological patterns.

**After:**
> Dust storms affect health and infrastructure, with economic costs reaching 2.5% of regional GDP (World Bank, 2019). The model captures how meteorological conditions vary across stations and seasons.

---

## 7. Elegant Variation (Synonym Cycling)

**Problem:** AI avoids repeating words by cycling through synonyms.

**Before:**
> The study examined dust events. The investigation also assessed aerosol episodes. The research further evaluated particulate matter occurrences.

**After:**
> The study examined dust events across all seven stations. Events were defined as days when AOD exceeded 0.5, following the threshold used by Cuevas et al. (2015).

---

## 8. Negative Parallelisms

**Watch words:** not just X, but also Y / not only X but Y / it's not about X, it's about Y

**Before:**
> It's not just about predicting dust — it's about predicting when predictions fail.

**After:**
> The meta-model predicts when dust forecasts will fail, and SHAP analysis identifies the conditions behind each failure.

---

## 9. False Ranges

**Watch words:** from X to Y, from A to B (when not on a meaningful scale)

**Before:**
> From data collection to model validation, from feature engineering to deployment, the pipeline addresses every stage.

**After:**
> The pipeline covers data collection, feature engineering, model training, and validation.

---

## 10. Em Dash Overuse

**Problem:** AI uses em dashes far more than humans. Limit to 1-2 per page.

**Before:**
> CAMS — the most widely used system — relies on static source maps — a known limitation — that cannot represent new sources.

**After:**
> CAMS relies on static source maps, which cannot represent new dust sources such as dried marshes or abandoned farmland.

---

## 11. Filler Phrases

Replace or delete:
- "It is worth noting that" → cut entirely
- "It should be mentioned that" → cut entirely
- "In order to" → "To"
- "Due to the fact that" → "Because"
- "At this point in time" → "Now"
- "It is important to note that" → just state the fact
- "plays a crucial role in" → say what it does
- "serves as a cornerstone" → "is"
- "In recent years" as opener → give the actual year
- "a wide range of" → be specific or give the count

---

## 12. Formulaic Section Endings

**Problem:** AI closes sections with generic importance statements.

**Before:**
> These findings highlight the importance of accurate dust forecasting and underscore the need for continued research.

**After:**
> CAMS correlation at Kuwait (R = 0.34) was the lowest of any station, consistent with near-source degradation reported by Cuevas et al. (2015) and Karami et al. (2021).

---

## 13. Generic Attribution

**Problem:** AI attributes claims to unnamed authorities.

**Before:**
> Several studies have demonstrated that dust models underperform near source regions. Research suggests that static source maps contribute.

**After:**
> Karami et al. (2021) tested nine operational dust models and found that all underestimated peak AOD near sources. Tuygun and Elbir (2024) confirmed this for CAMS: correlations dropped from 0.85 at coastal sites to 0.57 inland.

---

## 14. Descriptive Literature Review

**Problem:** Listing what authors found without comparison or critique.

**Before:**
> Smith (2018) studied dust in Kuwait. Jones (2019) examined dust in the UAE. Lee (2020) analysed dust in Saudi Arabia.

**After:**
> Smith (2018) and Jones (2019) both reported CAMS underestimation, but Smith used only AOD while Jones included Angstrom exponent filtering to isolate dust — a distinction that may explain Smith's higher reported bias.

---

## PART B: What to DO (human writing signals)

The patterns above tell you what to remove. These tell you what to add. Based on Tercon (2025), Kujur (2025), and detection research from GPTZero and Originality.ai.

---

## 15. Vary Punctuation

**Research finding:** AI uses mostly commas and periods. Humans use semicolons, colons, parentheses, and question marks naturally.

**AI-typical:**
> The model performed well. The results were consistent. The validation confirmed the findings.

**Human-typical:**
> The model performed well; validation confirmed this across all stations. One result stood out (Kuwait, R = 0.34) — why did CAMS fail so badly there?

**Rule:** Use at least 3 different punctuation types per page: periods, commas, semicolons, colons, parentheses, question marks. Not forced — only where natural.

---

## 16. Use Field-Specific Idioms

**Research finding:** AI text contains fewer idiomatic expressions than human text. Academic writing has its own idioms.

**AI-typical:**
> The results did not match expectations, which requires further investigation.

**Human-typical:**
> The results fell short of expectations, raising the question of whether the validation period was too short to capture the full range of conditions.

**Academic idioms that signal human writing:** "fell short of," "at odds with," "on closer inspection," "taken at face value," "at first glance," "the picture that emerges," "a closer look reveals," "this begs the question." Use sparingly — one or two per section.

---

## 17. Modulate Voice Between Sections

**Research finding:** Humans naturally shift their linguistic style between sections. AI maintains a consistent voice throughout.

**Rule:** Methodology should read dry and precise. Results should be factual and number-heavy. Discussion should be more interpretive and engaged. The reader should feel a subtle shift in tone as they move through the thesis. Don't force it — it happens naturally when you write each section with its purpose in mind.

**Methodology voice:** "Data were obtained from... Observations below the quality threshold were excluded."
**Discussion voice:** "The sharp drop in correlation at Kuwait is difficult to explain by lead time alone. A more likely explanation is..."

---

## 18. Express Genuine Uncertainty

**Research finding:** AI text emphasises positive emotions (especially "joy" framing). Human academic writing expresses uncertainty, surprise, frustration, and genuine not-knowing.

**AI-typical:**
> The results demonstrate the effectiveness of the proposed approach.

**Human-typical:**
> The results are encouraging, though the low precision at aggressive thresholds remains a concern. Whether this tradeoff is acceptable depends on the operational context — a question this study cannot fully resolve.

**Rule:** Include at least one moment of genuine uncertainty or limitation per major section. Not a formulaic "more research is needed" — a specific, honest acknowledgment of something you don't know.

**Sub-rule (Lit Review and Discussion):** Where the literature genuinely conflicts, name the contradiction explicitly. Use phrasing such as "It remains unclear whether…" or "The literature is at odds regarding…" and do not attempt to resolve it. Do NOT manufacture a contradiction where none exists — a fake disagreement is worse than no disagreement.

---

## 19. Vary Paragraph Length Deliberately

**Research finding:** AI paragraphs cluster around 4-6 sentences. Human paragraphs range from 1 sentence to 10+.

**Rule:** At least once per page, use a 1-2 sentence paragraph for emphasis. At least once, let a paragraph run to 7-8 sentences when the argument requires it. Never write three consecutive paragraphs of the same length.

---

## 20. Use Specific Numbers Over Adjectives

**Research finding:** AI uses more adjectives and vague quantifiers. Humans use specific numbers.

**AI-typical:**
> The model showed significant improvement across multiple metrics.

**Human-typical:**
> AUC rose from 0.81 to 0.87, F1 from 0.57 to 0.64. The improvement was concentrated at lead times under 12 hours.

**Rule:** Every claim about performance, change, or comparison must include a number. If you don't have the number, say so — "the exact improvement was not quantified" is better than "significant improvement."

---

## 21. Clause Density Variation

**Research finding (Turnitin 2026):** Turnitin analyses "clause density" — the number of clauses per sentence. AI uses similar clause density throughout. Humans vary between simple single-clause sentences and complex multi-clause ones.

**AI-typical (uniform clause density):**
> The model was trained on historical data, which included meteorological variables. The results showed improved performance, which was consistent across stations. The validation confirmed the findings, which supported the hypothesis.

**Human-typical (varied clause density):**
> The model was trained on historical data. Results improved across stations, though the degree of improvement varied — Kuwait showed the largest gains, while Mezaira, which already had strong baseline performance, barely changed. Validation supported the hypothesis.

**Rule:** Mix simple sentences (one clause) with complex ones (2-3 clauses). Never write three consecutive sentences with the same number of clauses.

---

## 22. The Polish Paradox

**Research finding (Turnitin 2026):** Heavily edited, polished writing paradoxically scores HIGHER on AI detection because editing removes natural variation. Turnitin flags "uniform sophistication" — when every paragraph reads at the same formal register with identical sentence complexity.

**What this means:** Do NOT over-edit to perfect uniformity. Leave some natural roughness:
- One section can be slightly more formal than another
- Not every transition needs to be perfectly smooth
- An occasional slightly awkward phrasing is more human than mechanical perfection
- Methodology can be dry and technical; Discussion can be more conversational

This does NOT mean write badly. It means don't sand every sentence to identical smoothness.

---

## 23. Grammatical Symmetry

**Research finding (Turnitin 2026):** Turnitin flags "consistent grammatical symmetry" — when the same grammatical template repeats across paragraphs.

**AI-typical (same template repeated):**
> The study found that wind speed affects dust emission. The analysis showed that humidity influences particle size. The results indicated that temperature controls aerosol loading.

**Human-typical (varied templates):**
> Wind speed affects dust emission — a finding consistent across all stations. What the analysis showed about humidity was less expected: particle size varied non-linearly with relative humidity, and only below 30% did the relationship become strong. Temperature effects, by contrast, were negligible once wind speed was controlled for.
