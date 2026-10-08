# PatentLLM Prompting Guide

## Principles

1. **Evidence first**: retrieved patent passages are inserted before generation.
2. **Audience-specific output**: R&D, sales, marketing, and executive reports use different personas and schemas.
3. **Structured output**: every report follows a predictable section layout.
4. **Uncertainty handling**: the model must say when evidence is insufficient.
5. **No legal overreach**: the system must not provide legal opinions, infringement conclusions, or freedom-to-operate conclusions.

## Prompt experiments to try

- Zero-shot report prompt
- Few-shot report prompt
- Strict JSON output prompt
- Claim-prioritized prompt
- Abstract + claims only prompt
- Persona-specific prompt

## Failure modes

- invented patent IDs
- unsupported assignee claims
- overstated novelty
- vague generic summaries
- evidence not cited
- legal conclusions without expert review
