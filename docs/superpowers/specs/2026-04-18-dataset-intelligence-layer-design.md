# Dataset Intelligence Layer Design (SPIDER)

## Problem

The current dataset pipeline extracts, filters, and labels prompt-injection payloads, but it does not yet produce the full dual-tier intelligence layer required by Planner, Mutation Engine, Vector DB Builder, and Attack Loop modules. We need deterministic, embedding-ready outputs with strict taxonomy coverage, scaffold extraction, and cross-file metadata alignment.

## Scope

This design covers the dataset intelligence layer only:

1. schema normalization
2. taxonomy enforcement
3. template/mutation tier split
4. scaffold extraction
5. irrelevant-prompt removal
6. deduplication
7. English filtering
8. category index generation
9. metadata alignment generation
10. size-target balancing

## Goals and Success Criteria

The pipeline is complete when all outputs are generated and consumable:

- `datasets/templates/prompts.json` (template tier, embedding-ready)
- `datasets/templates/metadata.json` (aligned with template order)
- `datasets/templates/prompts_metadata.json` (backward-compatible mirror of metadata)
- `datasets/mutation_reservoir/mutation_prompts.json`
- `datasets/mutation_reservoir/scaffolds.json`
- `datasets/taxonomy/categories.json`

Target sizes:

- templates: 80k-120k
- mutation reservoir: 400k-700k
- scaffold fragments/sequences: 5k-50k

## Architecture

Implement a single-pass orchestrator script (`dataset_intelligence_builder.py`) as the canonical finalization step. It uses `datasets/normalized/prompts.json` as source-of-truth input, with optional use of existing filtered/templates files as priors for source/category hints.

High-level flow:

1. load records from normalized corpus
2. normalize to strict schema
3. pre-filter irrelevant/non-LLM content
4. enforce English-only policy
5. classify into strict taxonomy
6. dedupe with canonicalization
7. assign tier (template or mutation)
8. extract scaffolds from staged prompts
9. expand mutation-tier variants deterministically to meet target size
10. write all outputs with deterministic ordering
11. run validation checks and print a summary report

## Data Model

All working records conform to:

```json
{
  "prompt": "...",
  "category": "...",
  "source": "...",
  "tier": "template | mutation",
  "language": "en"
}
```

Categories are strictly limited to:

- `system_leak`
- `override`
- `roleplay`
- `indirect_injection`
- `tool_exploit`
- `encoding`
- `general`
- `multi_turn_setup`
- `context_poisoning`

## Classification Strategy

Use ordered keyword/regex scoring with category-specific lexicons and tie-break precedence:

1. system leakage patterns
2. explicit override/bypass patterns
3. roleplay/developer mode patterns
4. tool/function/plugin exploitation patterns
5. encoding/obfuscation markers
6. indirect wrappers (markdown/html/comment/document context)
7. context poisoning/memory overwrite markers
8. multi-turn setup/framing markers
9. fallback to general

If category is missing, infer from required keyword rules:

- `ignore previous instructions` -> `override`
- `reveal system prompt` -> `system_leak`
- `developer mode simulation` -> `roleplay`
- `HTML comment wrapper` -> `indirect_injection`

## Relevance Filtering

Drop prompts dominated by:

- violence-only content
- toxicity/hate-only content
- generic unsafe queries with no LLM control-targeting
- non-LLM vulnerability content

Keep prompts related to:

- prompt injection
- policy leakage
- system prompt extraction
- agent manipulation
- tool misuse
- indirect injection

## Deduplication Strategy

Apply two-level dedupe:

1. strict dedupe by exact prompt text
2. canonical dedupe by normalized text (trim, lowercase, collapse whitespace, strip punctuation-only differences)

Retain:

- meaningful encoding variants
- wrapper-format variants
- semantic paraphrases

## Tiering Rules

Template tier (`template`):

- high-signal direct payloads for retrieval and planning:
  - direct override payloads
  - system prompt extraction attempts
  - policy leakage probes
  - tool misuse payloads

Mutation tier (`mutation`):

- transformation-heavy and wrapper-rich payloads:
  - encoding variants
  - markdown/html wrappers
  - JSON/YAML structures
  - persona framing
  - indirect scaffolds

## Mutation Expansion

To reach 400k-700k mutation prompts from available injection corpus, generate deterministic synthetic variants from mutation-eligible seeds:

- wrapper transforms (markdown, HTML comments, quoted context blocks)
- format transforms (JSON/YAML/message-role framing)
- persona/authority framing transforms
- reversible encoding transforms (base64/hex wrappers where semantically valid)
- chain-link scaffold variations

Every generated variant inherits source lineage metadata and is dedupe-checked against canonical forms.

## Scaffold Extraction

Detect staged jailbreak sequences and split them into phases:

- `setup`
- `framing`
- `override`
- `extraction`

Persist scaffold entries in `datasets/mutation_reservoir/scaffolds.json` with stable IDs and sequence grouping to support multi-turn escalation logic in the Attack Loop.

## Output Contracts

### `datasets/templates/prompts.json`

Ordered list of template-tier records, schema-complete and embedding-ready.

### `datasets/templates/metadata.json`

Ordered metadata list where each item includes:

```json
{
  "id": 0,
  "prompt": "...",
  "category": "...",
  "source": "...",
  "tier": "template"
}
```

IDs map exactly to template prompt order for vector index alignment.

### `datasets/templates/prompts_metadata.json`

Backward-compatible mirror of `metadata.json`.

### `datasets/mutation_reservoir/mutation_prompts.json`

Ordered list of mutation-tier prompts (source-derived + deterministic variants).

### `datasets/mutation_reservoir/scaffolds.json`

Phase-fragmented sequence artifacts for multi-turn attack assembly.

### `datasets/taxonomy/categories.json`

Category count index, e.g.:

```json
{
  "system_leak": 12000,
  "override": 18000
}
```

## Error Handling

The builder fails fast on:

- missing required input files
- malformed JSON
- schema contract violations
- non-whitelisted category labels in final output
- metadata alignment mismatch

It emits explicit terminal diagnostics with counts and failed check details.

## Validation

Validation checks run before completion:

1. schema completeness (`prompt/category/source/tier/language`)
2. category whitelist compliance
3. dedupe statistics (input vs retained)
4. English-only compliance
5. template/mutation/scaffold count ranges
6. metadata ID-order alignment with template prompts

## Testing Strategy

Add tests for:

1. category inference rules and precedence
2. dedupe canonicalization behavior
3. tier assignment correctness
4. scaffold phase extraction
5. metadata alignment integrity
6. output-file generation and structural validity

## Implementation Notes

- Keep deterministic ordering to make outputs reproducible.
- Keep transformations deterministic and explainable.
- Preserve source lineage where possible.
- Avoid broad exception swallowing; surface actionable failures.

