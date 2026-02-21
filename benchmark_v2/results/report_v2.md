# AGI Grounding Benchmark v2.0 - Report

Generated: 2026-02-21 01:05

## 1. Overall Ranking

| Rank | Model | Score | CI 95% | Std Dev |
|------|-------|-------|--------|---------|
| 1 | ATIC (ON) | 0.867 | [0.814, 0.921] | 0.143 |
| 2 | Claude | 0.864 | [0.789, 0.939] | 0.200 |
| 3 | GPT-4o | 0.844 | [0.773, 0.914] | 0.189 |
| 4 | ATIC (OFF) | 0.835 | [0.785, 0.885] | 0.135 |
| 5 | Gemini | 0.824 | [0.750, 0.897] | 0.198 |

## 2. Scores by Category

| Model | citation-integrity | contradiction-awareness | epistemic-calibration | factual-grounding | self-correction | task-adaptation |
|-------|--------|--------|--------|--------|--------|--------|
| ATIC (ON) | 0.799 | 0.729 | 0.942 | 0.922 | 0.915 | 0.898 |
| Claude | 0.835 | 0.687 | 0.908 | 0.908 | 0.913 | 0.933 |
| GPT-4o | 0.794 | 0.703 | 0.863 | 0.884 | 0.891 | 0.926 |
| ATIC (OFF) | 0.786 | 0.740 | 0.821 | 0.864 | 0.902 | 0.897 |
| Gemini | 0.792 | 0.687 | 0.858 | 0.927 | 0.876 | 0.801 |

## 3. High Divergence Tests

| Test | Model | Structural | Reference | Judge | Divergence |
|------|-------|------------|-----------|-------|------------|
| CA-03 | ATIC (ON) | 0.000 | 0.000 | 1.000 | 1.000 |
| CA-03 | ATIC (OFF) | 0.000 | 0.000 | 1.000 | 1.000 |
| CI-03 | Claude | 1.000 | 1.000 | 0.000 | 1.000 |
| CI-03 | ATIC (OFF) | 1.000 | 0.952 | 0.000 | 0.976 |
| EC-03 | ATIC (OFF) | 0.500 | 0.000 | 1.000 | 0.750 |
| CI-03 | ATIC (ON) | 0.667 | 0.667 | 0.000 | 0.667 |
| CI-03 | GPT-4o | 1.000 | 0.952 | 0.333 | 0.643 |
| CI-03 | Gemini | 0.667 | 0.619 | 0.000 | 0.643 |
| CA-02 | Claude | 0.333 | 0.400 | 1.000 | 0.633 |
| CA-02 | Gemini | 0.333 | 0.400 | 1.000 | 0.633 |

## 4. Unstable Tests (std > 0.3)

**Claude** (3.3% unstable):
- CA-03 (std=0.000)

**GPT-4o** (3.3% unstable):
- CA-03 (std=0.000)


## 5. Judge Agreement

| Judge Pair | N | Kappa | Interpretation |
|------------|---|-------|----------------|
| atic_off_vs_gpt | 30 | 1.000 | Almost perfect |
| atic_on_vs_gpt | 30 | 1.000 | Almost perfect |
| claude_vs_gpt | 30 | 1.000 | Almost perfect |
| gemini_vs_claude | 30 | 1.000 | Almost perfect |
| gpt_vs_claude | 30 | 1.000 | Almost perfect |

## 6. Quality Criteria

| Criterion | Target | Achieved | Status |
|-----------|--------|----------|--------|
| Judge agreement (kappa) | >= 0.65 | 1.000 | PASS |
| Unstable tests (max) | <= 20% | 3.3% | PASS |
| Category coverage | 100% | 100% | PASS |
| Tests with ground_truth | >= 40% | 10% (3/30) | FAIL |
| No self-evaluation | check | 0 violations | PASS |

## 7. Limitations

- **LLM Judge bias**: Judge models have their own biases that may affect scoring
- **Temperature variance**: Non-zero temperature causes some score variance across seeds
- **Structural checks limited**: Regex-based checks cannot capture semantic correctness fully
- **Ground truth coverage**: Not all tests have verifiable ground truth
- **Provider availability**: Results depend on which providers were available during the run
- **Cultural bias**: Tests in PT/EN may advantage models trained more on one language
- **Benchmark author bias**: Test selection and rubrics reflect the author's priorities
- **Small sample size**: 30 tests across 6 categories may not represent all capabilities
- **API rate limits**: Gemini and other providers may throttle, affecting consistency