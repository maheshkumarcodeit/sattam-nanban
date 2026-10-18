# Sattam Nanban: Product Requirements Document

Version 0.2 (draft) | Author: Maheshkumar S | Date: 18 October 2026

**Status:** working prototype on a laptop. User needs in this document are assumptions; no real users have been interviewed yet.

A Word version of this document is in the same folder: `Sattam_Nanban_PRD_v0.2.docx`.

## 1. Product summary

Sattam Nanban (சட்டம் நண்பன்) is a Tamil-first assistant that answers questions about Tamil Nadu government registration and schemes. It answers only from saved official pages, shows its sources, and says so when the answer is not in the documents.

## 2. Problem

Entrepreneurs find rules for Udyam registration and the UYEGP loan-subsidy scheme mostly in English, spread across many pages, and sometimes inconsistent. General chatbots can answer confidently from memory and be wrong, which is costly for legal and compliance topics.

## 3. Target users (assumed)

- First-time entrepreneurs in Tamil Nadu.
- Young people exploring UYEGP.
- Small shop owners who prefer reading in Tamil.

## 4. Goals

- Answer in Tamil from official text only.
- Show sources with every answer.
- Say "not found" instead of guessing.
- Flag conflicting figures instead of choosing one.

## 5. Non-goals (version 1)

- Legal or financial advice, or eligibility decisions.
- Filling forms for the user.
- Voice input.
- States other than Tamil Nadu, and schemes beyond Udyam and UYEGP.

## 6. Scope (version 1)

Four indexed pages: Udyam registration, UYEGP overview, UYEGP application procedure, and the bilingual UYEGP FAQ (23 items). A Streamlit web demo, with a limit of 10 questions per visit.

## 7. Functional requirements

1. The user types a Tamil question and gets a Tamil answer.
2. The answer lists the sources it used.
3. If the documents lack the answer, say so and point to the nearest District Industries Centre (DIC).
4. If sources give different figures, state each figure and name its source.
5. If the documents answer only part of the question, say what is missing.
6. The user can view the passages the answer was based on.
7. A visible warning states that this is a prototype and answers must be confirmed with the DIC.

## 8. Success metrics

Baseline is round 7: 10 questions, scored by hand by the author, same questions used for tuning, one run each. Treat as a starting point only.

| Metric | Baseline | Target |
|---|---|---|
| Clear pass rate | 5 of 10 | 80% or more on 20 unseen questions |
| Invented-fact rate | 0 found | 0 (no tolerance) |
| Honest "not found" rate | 1 of 1 (GST) | 100% on at least 5 trap questions |
| Sources shown | 10 of 10 | 100% |
| Conflicts flagged | 2 of 3 fully (age only partly) | 100% of known conflicts |
| Tamil quality (no stray words) | About 9 of 10 | 95% or more |

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Documents are outdated or contradict each other | Show sources, flag conflicting figures, add document dates, advise confirming with the DIC |
| Answer is true to the page but incomplete | Prompt says what is missing; retrieved text is viewable |
| Retrieval miss gives a wrong "not found" (seen in rounds 5 and 6) | Balanced retrieval across FAQ and other pages; check retrieval before blaming the model |
| Tamil wording slips from the model | Tamil-only prompt rule; native speaker review; unseen-question tests |
| Free-tier request limits and model busy errors | Model fallback, retries, per-visit question cap; choose a paid plan before any public launch |
| Users treat answers as official advice | Prototype warning on every page; DIC referral in answers |

## 10. Key findings so far

- Two official UYEGP pages disagree on upper age, family income limit and maximum subsidy, and neither shows a date.
- Adding the Tamil FAQ pushed English page chunks out of retrieval (round 5); searching the FAQ and other pages separately fixed most of it.
- An old-font PDF can look perfect on screen while its text is unreadable by code; reading page images solved it.
- Round 6 to 7 differences are within run-to-run noise, so tuning on the same 10 questions was stopped.

## 11. Open questions

- Which UYEGP page is current?
- Which paid model fits real traffic and budget?
- What do real business owners actually ask?

## 12. Roadmap

1. Write 20 unseen test questions and re-score.
2. Show document dates; add a GST source.
3. Interview 5 to 10 real business owners and update this PRD.
4. Choose a model and plan, then consider a public demo.
