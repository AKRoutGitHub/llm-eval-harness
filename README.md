# LLM Evaluation Harness

An AI-powered evaluation framework for grading Large Language Model code outputs.

## Features

- Syntax validation using Python's `ast` module
- Detection of placeholder comments (`TODO`, `# To be implemented`, etc.)
- Docstring quality checking
- Variable naming convention analysis
- Detailed scoring rubric (0-100)
- Comprehensive logging and JSON reporting
 - Syntax validation using Python's `ast` module
 - Improved detection of placeholder comments (regex search in comments and docstrings)
 - Docstring quality checking (function-level)
 - Variable naming convention analysis
 - Deterministic scoring rubric that follows README weights (0-100)
 - Comprehensive logging and JSON reporting

## Project Structure

llm-eval-harness/
├── data.json           # Test cases
├── evaluator.py        # Main evaluation engine
├── report.json         # Generated evaluation report
├── evaluation.log      # Detailed logs
└── README.md

## How to run
```bash
python evaluator.py

### Rubric
Criteria                   Weight           Passing Threshold
-----------             ------------     ------------------------
Syntax correctness          40%                 Required
No Placeholders             40%                 Required
Has Docstring               10%  (function-level docstrings)
Good Variable Names         10%  (any naming issues deduct full 10 points)

Scoring details:
- Start at 100 points.
- Subtract 40 if placeholder comments/text are detected (regex in comments/docstrings).
- Subtract 10 if no function-level docstrings are present.
- Subtract 10 if any variable-naming issues are found.
- Syntax errors short-circuit to score 0 (syntax correctness is required).

Pass mark: 70+