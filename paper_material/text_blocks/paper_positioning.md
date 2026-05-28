# Paper Positioning and Contribution

This document summarizes the positioning of the paper and the main contribution of the benchmark.

## 1. Core Positioning

This work investigates whether Large Language Models can perform conceptual-to-logical database design from textual EER specifications.

The paper is not only about asking LLMs to generate relational schemas.

Instead, it proposes a reproducible benchmark framework for evaluating LLMs on a database design task where correctness depends on preserving conceptual modeling semantics.

The benchmark focuses on the transformation from an expert-defined EER conceptual schema to a logical relational schema.

## 2. Main Problem

LLMs can generate plausible database schemas, but evaluating their outputs is difficult.

A simple exact-match comparison is insufficient because:

- LLMs may use different but reasonable names;
- conceptual-to-logical design may have more than one valid implementation;
- some errors are superficial, while others break core database semantics;
- foreign-key errors may be more serious than naming differences;
- relationship, cardinality, and specialization semantics must be preserved.

Therefore, the paper addresses the following problem:

How can we evaluate LLM-generated logical relational schemas in a way that distinguishes exact reproduction, structural equivalence, valid alternative mappings, and true design errors?

## 3. Main Research Question

The central research question is:

Can LLMs correctly transform textual EER conceptual schemas into logical relational schemas, and how should their outputs be evaluated when multiple valid logical mappings may exist?

## 4. Secondary Research Questions

The benchmark also supports the following questions:

1. Do explicit EER-to-relational mapping rules improve LLM outputs?
2. Does self-check prompting reduce schema design errors?
3. Does validation-guided repair improve previous LLM outputs?
4. Which schema components are most difficult for LLMs?
5. Do LLMs fail more often on foreign keys, relationship tables, weak entities, or specialization mappings?
6. How much of the apparent error is caused only by naming mismatch?
7. How often do LLMs generate valid alternatives instead of the preferred expert mapping?
8. How does dataset complexity affect performance?
9. What is the cost-quality trade-off across models and providers?
10. Are local models competitive with commercial API models for this task?

## 5. Main Contribution

The main contribution is an evaluation framework for LLM-based conceptual-to-logical database design.

The framework combines:

- textual EER ground truths;
- expert logical relational gold standards;
- preferred and alternative valid mappings;
- multiple prompting conditions;
- normalization of LLM outputs;
- strict, matched, and alternative-aware evaluation;
- weighted structural Manhattan distance;
- component-level schema metrics;
- mapping-decision metrics;
- usage, latency, and cost tracking;
- reproducible scripts and aggregate outputs.

## 6. Why This Is Different from Simple Schema Generation

A simple schema generation experiment would ask an LLM to create tables from a description and then manually inspect the result.

This work is different because it treats schema generation as a structured design evaluation problem.

The benchmark checks whether the generated schema preserves:

- conceptual entities;
- attributes;
- identifiers;
- cardinalities;
- participation constraints;
- relationship attributes;
- weak entity semantics;
- many-to-many relationship tables;
- specialization/generalization semantics;
- primary keys;
- foreign keys;
- valid discretionary mapping decisions.

This makes the evaluation more faithful to database design than a surface-level string comparison.

## 7. Why Exact Match Is Not Enough

Exact match can underestimate LLM performance.

For example, the gold schema may contain a relationship table named `OrderProduct`, while the LLM generates `OrdProd`.

If the generated table has the same columns, primary key, foreign keys, and relationship attribute, then the output is structurally correct even though the name differs.

For this reason, the benchmark reports both:

- strict evaluation;
- matched evaluation.

Strict evaluation measures whether the model reproduced the preferred schema exactly after basic normalization.

Matched evaluation measures whether the model produced a structurally equivalent schema despite naming variation.

## 8. Why Alternative-Aware Evaluation Is Needed

Conceptual-to-logical design may allow more than one valid implementation.

For example, an optional one-to-one profile relationship may be mapped as:

- a separate profile table;
- a merge of profile attributes into the owner table.

If both alternatives are documented by the expert, the second option should not be counted as a wrong design.

For this reason, the benchmark reports:

- preferred mapping accuracy;
- valid mapping accuracy;
- alternative mapping rate;
- invalid mapping rate;
- alternative-aware F1;
- alternative-aware structural distance.

This makes the evaluation more realistic for database design.

## 9. Expected Empirical Contribution

The experiments are expected to show:

- which LLMs produce the best relational schemas;
- whether rule-augmented prompts improve correctness;
- whether self-check prompts reduce omissions and hallucinations;
- whether validation-guided repair improves outputs;
- which database design elements are most error-prone;
- how much error is caused by naming mismatch;
- how often LLMs choose valid non-preferred mappings;
- how performance changes with dataset complexity;
- how quality relates to cost, latency, and token usage.

## 10. Positioning for Conceptual Modeling

The strongest positioning is in conceptual modeling.

The work contributes to the conceptual modeling community by evaluating whether LLMs can preserve EER semantics during logical design.

The paper is especially relevant to venues focused on:

- conceptual modeling;
- database design;
- model transformation;
- schema engineering;
- AI-assisted modeling;
- evaluation of generated models.

In this framing, the paper is not primarily a model-performance leaderboard.

It is a benchmark and evaluation methodology for a core modeling task.

## 11. Positioning for Database Conferences

For database venues, the paper should be positioned as a benchmark for LLM-assisted database design.

The strongest database-oriented angle is:

LLMs are increasingly used to generate database artifacts, but database design requires semantic correctness that cannot be evaluated by surface-level exact match.

The paper contributes:

- a reproducible benchmark;
- schema-level evaluation metrics;
- error analysis;
- cost-quality analysis;
- evidence across datasets and models.

This framing may fit database or data management venues if the experiments are sufficiently broad and the artifact is strong.

## 12. Positioning for AI Conferences

For AI venues, the paper should be positioned as an evaluation of structured reasoning in LLMs.

The task requires the model to map conceptual constraints into a formal logical schema.

The AI-oriented contribution is not a new model, but an evaluation framework for structured generation where correctness depends on constraints, alternatives, and semantic validity.

This framing is stronger if the paper emphasizes:

- structured output generation;
- semantic constraint preservation;
- alternative-aware evaluation;
- repair from validation feedback;
- cost-quality trade-offs across model families.

## 13. Recommended Primary Framing

The recommended framing is:

This paper presents a benchmark framework for evaluating LLMs on conceptual-to-logical database design from textual EER specifications. Unlike exact-match evaluations, the framework distinguishes strict reproduction, structural equivalence, valid alternative mappings, and invalid schema design errors.

## 14. Possible Title Directions

Possible title directions include:

1. Evaluating LLMs for Conceptual-to-Logical Database Design
2. Beyond Exact Match: Alternative-Aware Evaluation of LLM-Generated Relational Schemas
3. Benchmarking LLMs for EER-to-Relational Schema Transformation
4. Alternative-Aware Schema Matching for LLM-Based Database Design Evaluation
5. Can LLMs Perform Database Design? A Benchmark for EER-to-Relational Transformation

## 15. Compact Contribution Statement

A compact contribution statement could be:

We present a reproducible benchmark framework for evaluating LLMs on EER-to-relational schema transformation. The framework combines expert conceptual and logical ground truths, preferred and alternative valid mappings, strict and structure-aware schema matching, alternative-aware evaluation, weighted structural distance, component-level error analysis, and cost tracking across models and prompting conditions.

## 16. One-Sentence Positioning

One possible one-sentence positioning is:

This work evaluates LLMs as database design assistants by testing whether they can transform textual EER schemas into semantically valid relational schemas under strict, structure-aware, and alternative-aware evaluation.

## 17. Main Claim to Validate Experimentally

The main claim should be cautious:

LLMs can often generate plausible relational schemas from textual EER inputs, but their quality varies substantially across models, prompt conditions, schema components, and dataset complexity; reliable evaluation requires structure-aware and alternative-aware metrics rather than exact match alone.

## 18. What the Paper Should Avoid Claiming

The paper should avoid claiming that:

- LLMs fully automate database design;
- one model is universally best;
- exact match is sufficient for schema evaluation;
- the preferred expert schema is the only valid schema;
- prompt engineering alone solves schema design;
- local models are always worse or always better than commercial models.

## 19. Strongest Expected Message

The strongest expected message is:

Evaluating LLMs for database design requires database-aware metrics. Exact match hides the difference between naming variation, valid design alternatives, and real semantic errors. A fair benchmark must evaluate structural equivalence, alternative validity, and error severity.

## 20. Use in the Paper

This text can support:

- abstract;
- introduction;
- contribution paragraph;
- methodology motivation;
- related work positioning;
- discussion section;
- response to supervisor comments;
- submission targeting decisions.
