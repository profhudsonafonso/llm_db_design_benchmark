# Final Execution Checklist

This checklist should be used when the expert ground truth files are available and the benchmark is ready to be executed on the real datasets.

The goal is to avoid missing operational steps before running the final experiments.

## 1. Ground Truth Readiness

For each dataset, verify that the following files exist:

- `datasets/<dataset>/ground_truth/conceptual_eer.yaml`
- `datasets/<dataset>/ground_truth/logical_relational_gold.json`

Datasets expected for the benchmark:

- `chinook`
- `imdb`
- `yelp`

For each dataset, apply:

- `docs/ground_truth_review_checklist.md`

Review decision must be one of:

- `approved`
- `approved_with_minor_notes`

Do not run experiments on a dataset marked as:

- `needs_revision`
- `rejected`

## 2. Prompt Input Generation

For each approved dataset, generate the prompt-ready EER input.

Example:

- `python scripts/generate_prompt_input.py --conceptual-yaml datasets/chinook/ground_truth/conceptual_eer.yaml --dataset chinook --run-id chinook_prompt_input --publish-to datasets/chinook/prompt_inputs/eer_input_text.md --notes "Chinook prompt input generation"`

Repeat for:

- `chinook`
- `imdb`
- `yelp`

Verify that each dataset has:

- `datasets/<dataset>/prompt_inputs/eer_input_text.md`

## 3. Model Configuration

Review:

- `configs/models.yaml`

For each model, verify:

- provider is correct;
- model name is correct;
- `enabled` status is correct;
- temperature is set;
- max token limit is set;
- seed is set when supported;
- Ollama model names match `ollama list`, when Ollama is available.

If a model/provider is unavailable, set:

- `enabled: false`

## 4. Provider Configuration

Create local provider settings from:

- `configs/provider_settings.example.yaml`

Local file:

- `configs/provider_settings.yaml`

Do not commit this file.

Verify environment variables:

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`

Check Ollama availability, if applicable:

- `ollama list`

## 5. Pricing Configuration

Review and update:

- `configs/model_pricing.yaml`

Before final experiments, verify prices from official provider pricing pages.

If a price is unknown, keep it as:

- `null`

If using Ollama local models, financial token price may remain:

- `0.0`

## 6. Experiment Matrix

Review:

- `configs/experiment_matrix.yaml`

Enable real datasets only after approval:

- `chinook`
- `imdb`
- `yelp`

Disable toy example for final real experiments unless running a sanity check.

Recommended final condition setup:

- C1 enabled
- C2 enabled
- C3 enabled
- C4 disabled initially

C4 should be enabled only after C1-C3 outputs have been generated, normalized, evaluated, and validation reports are available.

## 7. Dry-Run Sanity Check

Before real API calls, run a dry-run batch:

- `python scripts/run_llm_batch.py --matrix configs/experiment_matrix.yaml --batch-id final_dryrun_check --dry-run --notes "Final dry-run check"`

Verify:

- `results/batch_runs/final_dryrun_check/batch_manifest.json`
- `results/batch_runs/final_dryrun_check/batch_runs.csv`
- `results/llm_runs/<run_id>/rendered_prompt.txt`

Check that rendered prompts contain:

- the expected EER input;
- the correct prompt condition;
- the correct output format;
- no missing placeholders.

## 8. Run Real LLM Experiments

Run C1-C3 with real provider calls:

- `python scripts/run_llm_batch.py --matrix configs/experiment_matrix.yaml --batch-id final_c1_c2_c3 --execute --notes "Final C1-C3 LLM execution"`

Verify:

- no unexpected provider errors;
- response files are not empty;
- manifests are created;
- usage and cost metadata are saved.

Expected output folder:

- `results/llm_runs/`

## 9. Batch Normalization and Evaluation

After LLM execution, run:

- `python scripts/run_evaluation_batch.py --batch-id final_eval_c1_c2_c3 --notes "Final C1-C3 normalization and evaluation"`

Verify outputs:

- `results/evaluation_batch_runs/final_eval_c1_c2_c3/evaluation_batch_manifest.json`
- `results/normalization_runs/`
- `results/evaluation_runs/`

Check whether any run has:

- normalization error;
- evaluation error;
- empty response;
- missing gold file.

## 10. Aggregate C1-C3 Results

Run:

- `python scripts/aggregate_results.py --run-id final_aggregate_c1_c2_c3 --notes "Final C1-C3 aggregation"`

Verify:

- `results/aggregate_runs/final_aggregate_c1_c2_c3/aggregate_run_summary.csv`
- `results/aggregate_runs/final_aggregate_c1_c2_c3/aggregate_component_metrics.csv`
- `results/aggregate_runs/final_aggregate_c1_c2_c3/aggregate_cost_quality.csv`
- `results/aggregate_runs/final_aggregate_c1_c2_c3/aggregate_manifest.json`

Inspect:

- number of LLM runs;
- number of evaluation runs;
- number of successful runs;
- missing values;
- unexpected zeros.

## 11. Prepare C4 Repair

C4 requires:

- previous LLM output;
- validation/evaluation report;
- original EER input;
- repair prompt.

Before enabling C4, verify:

- C1-C3 outputs exist;
- evaluation errors exist;
- validation feedback can be passed to the C4 prompt.

C4 should be run selectively if cost or time is high.

Suggested C4 targets:

- best model per provider;
- worst or most interesting failure cases;
- outputs with high invalid mapping rate;
- outputs with low foreign-key or relationship-table F1.

## 12. Run C4 Repair

Enable C4 in:

- `configs/experiment_matrix.yaml`

Run C4 batch when repair inputs are configured.

Then run:

- normalization;
- evaluation;
- aggregation.

Suggested aggregate run:

- `final_aggregate_with_c4`

## 13. Final Aggregation

After all final runs, execute:

- `python scripts/aggregate_results.py --run-id final_aggregate_all --notes "Final aggregation with all conditions"`

This is the main folder for paper analysis:

- `results/aggregate_runs/final_aggregate_all/`

Main files:

- `aggregate_run_summary.csv`
- `aggregate_component_metrics.csv`
- `aggregate_error_counts.csv`
- `aggregate_cost_quality.csv`
- `aggregate_by_model.csv`
- `aggregate_by_condition.csv`
- `aggregate_by_dataset_complexity.csv`
- `aggregate_by_model_condition.csv`
- `aggregate_by_dataset_condition.csv`

## 14. Analysis Checklist

Use:

- `paper_material/text_blocks/expected_analysis_plan.md`

Analyze:

- model quality;
- prompt condition effects;
- dataset complexity effects;
- component-level weaknesses;
- naming mismatch;
- valid alternative mappings;
- invalid mappings;
- C4 repair effect;
- cost-quality trade-off.

## 15. Minimum Tables for Supervisor

Prepare at least:

1. dataset summary table;
2. model/provider table;
3. main quality table by model and condition;
4. strict vs matched vs alternative-aware table;
5. component-level error table;
6. cost-quality table;
7. representative error cases table.

## 16. Minimum Figures

Prepare if time allows:

1. pipeline figure;
2. alternative-aware F1 by model;
3. F1 by prompt condition;
4. score by dataset complexity;
5. cost vs quality scatter plot;
6. error type distribution.

## 17. Repository Check Before Sharing

Before sending to supervisor or reviewers, verify:

- README is updated;
- reproduction pipeline is updated;
- experiment protocol is updated;
- aggregate result folder exists;
- no API keys are committed;
- no large private files are committed;
- ground truth files are present;
- final aggregate manifest exists;
- scripts run without syntax errors.

## 18. Final Git Commands

Check status:

- `git status`

Add relevant files:

- `git add <files>`

Commit:

- `git commit -m "Add final experiment results"`

Push:

- `git push`

## 19. Final Decision

Before writing final results, mark the execution status:

| Area | Status | Notes |
|---|---|---|
| Ground truths reviewed | pending |  |
| Prompt inputs generated | pending |  |
| Models configured | pending |  |
| Dry-run completed | pending |  |
| C1-C3 executed | pending |  |
| C1-C3 normalized/evaluated | pending |  |
| C1-C3 aggregated | pending |  |
| C4 configured | pending |  |
| C4 executed | pending |  |
| Final aggregation completed | pending |  |
| Analysis tables prepared | pending |  |
| Supervisor version prepared | pending |  |

Allowed status values:

- pending
- ok
- needs_fix
- not_applicable
