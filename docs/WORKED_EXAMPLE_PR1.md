# Worked example: PR.1, A9, Execution999

## Original evidence

The exact workbook record ID is `Execution999|PR.1|A9`. Find it in `data/flag_explanations.csv`.

The LLM explanation says:

> The ±2.5 mm tolerance value is not traceable to any stated stakeholder need, ConOps element, or supporting analysis in the provided context.

The supplied requirement PR1 states:

> The system shall execute FR1 accurately with +/- 2.5mm [0.1”] accuracy in every Cartesian direction.

The supplied ConOps describes displacement and return; it does not state a numerical accuracy tolerance. A9 asks whether the requirement accurately represents its source need or higher-level requirement.

## Proposed reason

`R01 — Missing stated provenance`.

This label captures the argument actually expressed: the source of the numerical target is not shown. It does not label the target as wrong. The rule match is a proposal; verify the complete sentence yourself.

## Two separate review questions

1. **Is the source observation supported?** You can verify that the supplied ConOps contains no accuracy number. You cannot establish that no supporting engineering analysis exists anywhere. The phrase "provided context" limits the claim, but the exact original model input is unavailable. Explain that scope in your evidence note.
2. **Does the observation justify A9?** Source absence alone makes correctness difficult to verify. It does not demonstrate a numerical contradiction. You may judge the A9 argument partly aligned or not judgable, depending on your documented criterion interpretation. State why; do not automatically turn it into an incorrectness finding.

The interface leaves both judgment fields pending because these are your research judgments. The software does not choose a final answer for you.

## Possible evidence note to adapt after your review

"The supplied ConOps does not specify an accuracy tolerance. This supports a concern about missing provenance within the provided materials. The documents do not establish that ±2.5 mm is incorrect, and the full original model input is unavailable. Therefore, evidence for a confirmed A9 violation remains limited."

Suggested evidence locator: `Point Mass PDF p.1 §2 and p.2 PR1; Task PDF p.1 Table 1 A9`.

## Frequency and consistency

The raw workbook flags PR.1 under A9 in all 100 runs. This is a directly observed flag count. The code separately counts how often R01 appears in those explanations. Even when those two counts coincide, they answer different questions: one is criterion selection; the other is the argument used.

## Counterexample to your interpretation

If an authoritative parent requirement stated a tighter necessary tolerance and PR1 permitted a larger error, that could provide evidence of a numerical conflict. Such a parent specification is not included. Do not invent it.

## What to say in the presentation

"I separated repeated flagging from evidence of a real violation. For PR1, the model consistently flags correctness, but the reason concerns missing provenance. I therefore assessed the source claim and the criterion fit separately, and retained uncertainty where the supplied documents cannot settle the issue."
