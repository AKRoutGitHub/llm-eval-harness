import json
import ast

def evaluate_code(code: str) -> dict:
    """Evaluate a single code snippet."""
    result = {
        "syntax_valid": False,
        "has_placeholder": False,
        "pass": False,
        "issues": []
    }
    
    # Check syntax using ast
    try:
        ast.parse(code)
        result["syntax_valid"] = True
    except SyntaxError as e:
        result["issues"].append(f"Syntax Error: {str(e)}")
    
    # Check for weak placeholder text
    placeholder_patterns = ["# To be implemented", "# TODO", "placeholder", "implement later"]
    lower_code = code.lower()
    for pattern in placeholder_patterns:
        if pattern.lower() in lower_code:
            result["has_placeholder"] = True
            result["issues"].append("Contains weak placeholder comments")
            break
    
    # Simple rubric
    if result["syntax_valid"] and not result["has_placeholder"]:
        result["pass"] = True
    elif result["syntax_valid"] and result["has_placeholder"]:
        result["pass"] = False  # Treat as partial fail
        result["issues"].append("Code is syntactically correct but contains placeholders")
    else:
        result["pass"] = False
    
    return result

def main():
    # Load data
    with open('data.json', 'r') as f:
        data = json.load(f)
    
    report = []
    
    for item in data:
        eval_result = evaluate_code(item["code"])
        
        report_item = {
            "id": item["id"],
            "expected": item["expected"],
            "syntax_valid": eval_result["syntax_valid"],
            "has_placeholder": eval_result["has_placeholder"],
            "pass": eval_result["pass"],
            "issues": eval_result["issues"]
        }
        report.append(report_item)
    
    # Save report
    with open('report.json', 'w') as f:
        json.dump({"evaluations": report, "summary": {
            "total": len(report),
            "passed": sum(1 for r in report if r["pass"]),
            "failed": sum(1 for r in report if not r["pass"])
        }}, f, indent=2)
    
    print("Evaluation complete! Check report.json")
    print(f"Summary: {report[-1]['summary']}")

if __name__ == "__main__":
    main()