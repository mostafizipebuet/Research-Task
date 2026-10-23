# Your practical sequence

## 1. Understand the three inputs

- **Task PDF:** what the professor asks and what each of the seven criteria means.
- **Point Mass PDF:** the actual system context, ConOps and 13 requirements. It is a reference; we do not have the complete original LLM prompt.
- **Workbook:** 100 sets of the LLM's judgments. Each A2 cell is a JSON object containing the flags and explanations.

You study the LLM's expressed reasons. You are not asked to design the mechanical system or train a new LLM.

## 2. Start with the exact count figure

Open Figure 2. A value of 81 in PR.1/A4 means that 81 of the 100 runs flagged that requirement as ambiguous. It does not mean there is an 81% probability the requirement is defective. A value of 0 means the LLM did not flag that criterion in any run; it is not an expert certificate of compliance.

## 3. Work through one explanation

Read `WORKED_EXAMPLE_PR1.md`. Then open `review.html` and search `Execution999|PR.1|A9`. Read its exact text, the actual PR1 statement, and the A9 definition. Decide what the explanation says and what evidence supports it.

## 4. Understand the codebook

An explanation is the full text of one flag. A reason is a reusable category for one argument in that text. The same explanation can contain several arguments. For example, an explanation may question both endpoint-versus-path accuracy and unit equivalence. Those are two reasons, even though the LLM produced only one A4 flag.

The initial codebook is a proposal based on this dataset. Check whether its boundaries are useful, whether some labels should merge or split, and whether rare arguments need new labels. Do not force a case to match a category because the category exists.

## 5. Review in batches

Start with the high-priority queue: source uncertainty, notes, rare arguments and compound explanations. Include every criterion and requirement in the early reading. Revise the codebook and keep a change log. Then review the remaining corpus systematically.

The priority queue is not a random validation sample. If you report coding reliability, use a documented independent review sample, do not tune the rules on that sample and still call it held-out, and report actual disagreements. If working alone, report that limitation and use a documented second pass; do not claim two coders.

## 6. Separate two judgments

**Source evidence:** Is the LLM's factual description supported by the supplied source? Use supported, partly supported, contradicted, or not verifiable. Example: a statement that notes are absent may disagree with the PDF's explicit Note labels. Exact original input formatting is still unknown.

**Criterion fit:** Does the reason justify the criterion that the LLM selected? Use aligned, partly aligned, misaligned, or not judgable. A real missing detail may relate to completeness, while the LLM labels it ambiguity. Explain that decision instead of applying a word-matching rule.

These judgments concern the explanation and its category. They do not automatically prove the engineering requirement is defective.

## 7. Read the statistical outputs correctly

- **All-run reason rate:** runs containing a reason / all 100 runs, for one requirement and criterion.
- **Conditional reason rate:** runs containing a reason / runs where that criterion was flagged.
- **Example (hypothetical):** 60 reason occurrences among 80 flagged runs gives 60% of all runs, or 75% of flagged runs. Both are meaningful, but answer different questions.
- **Jaccard similarity:** shared reasons divided by all distinct reasons in the two compared sets. {A,B} versus {A,C} gives 1/3. Two empty sets are excluded from positive Jaccard rather than assigned perfect similarity.
- **Wilson interval:** uncertainty in a repeated-run frequency, not uncertainty about real requirement correctness.

If a reason occurs under A4 and A5, this may be a legitimate relationship between ambiguity and missing information. The overlap table identifies examples to inspect; it does not automatically identify mistakes.

## 8. Prepare the professor's deliverables

Use Report_Draft.md as a methods/results scaffold. Replace provisional interpretations with your reviewed findings. Use the six figures selectively and cite specific records. Read Presentation_Outline.md to prepare your slides. Include the code, raw data, codebook, reviewed annotations, complete generated tables and audit files so each conclusion can be traced to the source.

You should be able to explain: why your categories are distinct; how you handled multi-reason text; which denominators you used; what changed in repeated runs; which cases are uncertain; and what the study cannot establish.
