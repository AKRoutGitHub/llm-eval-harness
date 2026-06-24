# LLM Evaluation Harness

An AI-powered evaluation framework for grading Large Language Model code outputs.

## Project Context & Origin
> This evaluation harness was originally developed and iterated in a localized, private workspace to test model behavior benchmarks. It has been refactored, decoupled, and published here as a public portfolio piece to demonstrate programmatic dataset validation pipelines and strict QA edge-case screening.

## Features

- Syntax validation using Python's `ast` module
- Detection of placeholder comments (`TODO`, `# To be implemented`, etc.)
- Docstring quality checking
- Variable naming convention analysis
- Detailed scoring rubric (0-100)
- Comprehensive logging and JSON reporting

## Project Structure
```
llm-eval-harness/
├── data.json           # Test cases
├── evaluator.py        # Main evaluation engine
├── report.json         # Generated evaluation report
├── evaluation.log      # Detailed logs
└── README.md
```
## How to run
```bash
python evaluator.py
```

### Rubric
```
Criteria                   Weight           Passing Threshold
-----------             ------------     ------------------------
Syntax correctness          40%                 Required
No Placeholders             40%                 Required
Has Docstring               10%                    -
Good Variable Names         10%                    -

pass mark: 70+
```
