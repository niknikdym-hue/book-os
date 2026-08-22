# BOOK OS — BOOKBENCH v0.1

**Status:** ACCEPTED FOR V0.1 IMPLEMENTATION  
**Version:** 0.1.0  
**Date:** 2026-08-22

## 1. Mission

BookBench is BOOK OS's internal evaluation system for manuscript and editorial quality. It is not a “book score” and does not declare that a manuscript is a bestseller.

Its job is to turn editorial quality from vibes into traceable tests, findings, comparisons and human-labeled learning data.

## 2. Evaluation object

Every check is a versioned `EvaluationRun` against exact target revision(s), with:

- check/rubric ID and version;
- target revisions;
- inputs/configuration;
- deterministic/model/human evaluator identity;
- result/findings;
- confidence/severity;
- cost/latency when applicable;
- provenance.

Evaluation cannot edit authority directly.

## 3. v0.1 quality dimensions

1. Book Contract fulfillment.
2. Chapter Contract fulfillment.
3. Chapter semantic novelty / structural function.
4. Idea repetition across book.
5. Example/scene repetition.
6. Contradictions/inconsistency.
7. Thought/argument density.
8. Specificity vs generic/banal prose.
9. Evidence/unsupported claims.
10. Author voice preservation.
11. AI-prose pathology.
12. Opening/ending/transition quality.
13. Cross-book coherence and promise coverage.

Do not combine these into one magic “87/100 book quality” number.

## 4. Check classes

### A. Deterministic / lexical / statistical

Examples:

- repeated phrases/n-grams;
- sentence-start repetition;
- paragraph/sentence length distributions;
- rhetorical-question frequency;
- repeated transition templates;
- repeated chapter-ending phrases;
- unresolved placeholders/TODOs;
- claim-without-evidence counts;
- duplicated example IDs.

### B. Semantic

Examples:

- paraphrased idea duplication;
- concept overlap;
- contradiction candidates;
- chapter novelty;
- promise coverage gaps;
- semantic drift from chapter function.

### C. LLM-as-judge

Used only when judgment is genuinely semantic/literary:

- developmental quality;
- argument clarity;
- reader confusion;
- banality/genericness;
- opening/ending strength;
- voice fidelity;
- contract fulfillment.

### D. Pairwise comparison

For proposed edits and model selection, prefer blind pairwise comparisons when possible:

`A vs B against explicit rubric`, randomizing order and storing judge rationale/confidence.

### E. Human labels

Owner acceptance/rejection + reason is the highest-value ground truth for editorial decisions.

## 5. AI-prose pathology detector v0.1

BookBench must explicitly look for measured versions of:

- excessive `не X, а Y` / false contrast;
- “это не про X, это про Y” templates;
- pseudo-aphoristic sentence patterns;
- artificial threes/tricolons;
- repeated paragraph architecture;
- repetitive chapter conclusions;
- unnecessary rhetorical questions;
- over-explaining obvious points;
- empty therapeutic/corporate abstractions;
- false profundity/banal generalization;
- excessive syntactic symmetry;
- overly smooth depersonalized prose;
- repeated AI transition phrases.

The detector must show examples/locations and avoid blanket stylistic bans. Frequency, context and author Style Profile matter.

## 6. Author Voice Fingerprint v0.1

StyleProfile can capture:

- sentence-length distribution/variance;
- paragraph-length distribution;
- punctuation tendencies;
- syntactic patterns;
- pronoun/author-presence tendencies;
- concrete vs abstract noun density;
- dialogue/quotation usage;
- metaphor/analogy density;
- transition types;
- rhetorical-question tolerance;
- phrase/construction blacklist/alerts;
- accepted reference passages.

Voice checks are diagnostic, not automatic homogenization.

## 7. Judge independence

A critical output should not be written and solely judged by the same run/model configuration.

For release-critical dimensions:

- deterministic evidence where possible;
- independent judge run;
- cross-provider judge where evals justify it and region/policy allows;
- human acceptance for material decisions.

## 8. Model/prompt eval datasets

BookBench maintains datasets for roles such as:

- architecture proposals;
- section drafting;
- developmental diagnosis;
- factual evidence analysis;
- repetition detection;
- literary edit;
- voice/style judgment.

Each dataset grows from real editorial decisions:

`input authority + task → outputs/proposals → human accepted/rejected + reason → final`.

Dataset versions are immutable snapshots for reproducible model comparisons.

## 9. Model promotion gate

A provider/model/prompt configuration may be assigned a production role only if it:

- passes hard schema/instruction tests;
- meets minimum quality thresholds on role dataset;
- does not regress critical dimensions versus current production baseline beyond accepted tolerance;
- has acceptable cost/latency/privacy/region profile;
- has no known severe failure pattern for the role.

Brand reputation does not bypass the gate.

## 10. BookBench report shape

User-facing report is a set of findings grouped by dimension:

`finding → location → evidence → severity → confidence → recommended action → status`.

A release dashboard may show pass/attention/blocking counts per dimension, but never hide blocking findings behind an average.

## 11. Initial release gates

Before Literary Master:

- no unresolved blocking Book/Chapter Contract violations;
- material factual claims meet evidence policy or have explicit human waiver;
- no unresolved severe contradictions;
- whole-book repetition audit completed;
- style/AI-prose audit completed;
- final BookBench run references exact release revisions;
- Owner final approval exists.

## 12. Evaluation infrastructure principle

Use our own domain-specific datasets/rubrics as authority. Vendor eval platforms may be used as commodity execution tooling, but BookBench definitions/results remain portable.

Current platforms demonstrate useful patterns: OpenAI exposes graders/evals primitives; Google Gen AI Evaluation supports pointwise/pairwise/custom/rubric evaluation and explicitly recommends data-driven, task-specific evaluation. BOOK OS adopts these patterns without outsourcing its editorial standard.
