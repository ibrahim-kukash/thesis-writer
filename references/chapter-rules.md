# Chapter-Specific Rules

## Chapter 1: Introduction

Use the **funnel**: broad context (1-2 paragraphs) → specific area (2-3 paragraphs) → research problem (what's known → what's missing → why the gap matters) → aim (one sentence) → numbered objectives (3-5, each testable) → research questions (optional) → significance (concrete, not "contributes to the body of knowledge") → scope and limitations → thesis structure (1-2 sentences per chapter).

**Write this chapter LAST** so it matches what was actually done.

**Examiner questions:**
- Why did you choose this topic?
- What is the original contribution?
- How do your objectives relate to the research gap?
- What would happen if your research was never done?

---

## Chapter 2: Literature Review

**Organise thematically, NEVER chronologically.**

BAD: "Smith (2010) studied X. Jones (2012) studied Y. Lee (2015) studied Z."

GOOD: "Smith (2010) and Jones (2012) both reported CAMS underestimation, but Smith used only AOD while Jones included Angstrom exponent filtering — a distinction that may explain the different bias magnitudes."

Within each theme:
- Compare findings across studies
- Evaluate methodologies ("limited by only 2 years of data")
- Note consensus AND disagreement
- End each theme connecting to YOUR work

End the chapter so the gap is obvious without stating it.

**Examiner questions:**
- Why did you include/exclude study X?
- How has the field changed since you wrote this?
- Which paper influenced your approach most?
- What is the strongest counter-argument?
- Are there contradicting studies?

---

## Chapter 3: Methodology

**Replicable, not textbook.** Do NOT explain how random forests work. Explain why you chose them and how you configured them.

Structure: study area → data sources (variables, resolution, time period, QC) → methods per objective (mirror Chapter 1) → justification of choices → methodology limitations.

**Examiner questions:**
- Why this method and not X?
- How did you handle missing data?
- What are the model assumptions? Are they met?
- How would results change with a different threshold?
- Could confounding variables explain your results?
- How did you validate your implementation?

---

## Chapter 4: Results

**Mirror your objectives.** N objectives = N sections. No exceptions.

- Introduce every figure/table in text BEFORE it appears
- After presenting a figure, describe what to notice (2-3 sentences)
- Report WHAT, not WHY — save interpretation for Discussion
- Consistent figure formatting across the entire chapter

BAD: "Table 4.1 shows the results."
GOOD: "Table 4.1 presents validation metrics per station. RMSE ranged from 0.12 at Masdar to 0.41 at Kuwait, with the highest errors during spring dust events (Figure 4.2)."

**Examiner questions:**
- Why this figure and not others?
- What happens if you remove outliers?
- Is this statistically significant?
- Explain the unexpected result at station X.
- Did you check for overfitting?

---

## Chapter 5: Discussion

**Interpret, don't repeat.** For each finding:
1. Interpret physically — what does this mean?
2. Compare with literature — agrees or contradicts?
3. Explain discrepancies — if different, why?

Also include: unexpected findings, practical implications, specific limitations (not "more research is needed"), future research directions.

**Examiner questions:**
- What is the most important finding and why?
- How do you explain result X?
- What would you do differently?
- How generalisable are your results?
- What are the practical implications?
- What is the weakest part of your thesis?

---

## Chapter 6: Conclusion

Short (2-4 pages). Map findings to objectives. State contributions. Practical recommendations. Brief limitations. Future directions (specific). Final statement.

NEVER introduce new information or new citations.

---

## Abstract

Write LAST. 250-350 words. One paragraph.

Structure: context (1-2 sentences) → gap (1 sentence) → aim (1 sentence) → method (2-3 sentences) → key results with specific numbers (3-4 sentences) → significance (1 sentence).

No citations. No figures. No undefined acronyms.

---

## Chapter Transitions

**End every chapter** with 2-3 sentences previewing the next:
> "The three-way validation confirmed systematic underestimation during extreme events. The following chapter describes the meta-model developed to predict these failures."

**Start every chapter** (after Ch1) by linking back:
> "Chapter 2 identified a gap: no study has compared failure conditions of physics-based and AI-based dust models. This chapter describes the methods used to address that gap."

**Cross-reference throughout:** "As shown in Section 4.1..." "Table 4.2 confirms the pattern identified in the three-way validation (Section 4.1)."

---

## Academic Voice

| Context | Tense |
|---------|-------|
| Established knowledge | Present: "Dust events affect..." |
| Specific past study | Past: "Karami et al. (2021) found..." |
| Your methods/results | Past: "The model achieved..." |
| Your figures | Present: "Figure 4.1 shows..." |

**Hedging:** One per claim. "The results indicate that..." Not "might possibly suggest that could potentially..."

**Voice:** Passive for methods. Active for attributions. No first person unless university allows it.

**Citations:** Mix narrative ("Rémy et al. described..."), parenthetical ("...updated (Rémy et al., 2022)"), and grouped ("Three studies confirmed (A; B; C)").
