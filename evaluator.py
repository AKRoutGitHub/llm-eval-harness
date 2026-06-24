import json
import ast
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("evaluation.log"),
        logging.StreamHandler()
    ]
)

def check_docstring(node) -> bool:
    """Check if function has a docstring."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return bool(ast.get_docstring(node))
    return False

def check_variable_naming(node) -> list:
    """Check for poor variable naming (single letter, etc.)."""
    issues = []
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id.islower() and len(child.id) == 1:
            if child.id not in ['i', 'j', 'k', 'x', 'y', 'z']:  # Allow common loop vars
                issues.append(f"Poor variable name: '{child.id}'")
    return issues

def evaluate_code(code: str) -> dict:
    """Evaluate a single code snippet with advanced rubric."""
    result = {
        "syntax_valid": False,
        "has_placeholder": False,
        "has_docstring": False,
        "naming_issues": [],
        "pass": False,
        "score": 0,           # 0-100 score
        "issues": []
    }
    
    # 1. Syntax Check
    try:
        tree = ast.parse(code)
        result["syntax_valid"] = True
        logging.info("Syntax is valid")
    except SyntaxError as e:
        result["issues"].append(f"Syntax Error: {str(e)}")
        logging.error(f"Syntax Error: {str(e)}")
        result["score"] = 0
        return result
    
    # 2. Placeholder Check
    placeholder_patterns = [
        "# To be implemented", "# TODO", "placeholder", 
        "implement later", "TBD", "coming soon"
    ]
    lower_code = code.lower()
    for pattern in placeholder_patterns:
        if pattern.lower() in lower_code:
            result["has_placeholder"] = True
            result["issues"].append("Contains weak placeholder comments")
            break
    
    # 3. Advanced Checks (only if syntax is valid)
    if result["syntax_valid"]:
        # Docstring check
        has_docstring = any(check_docstring(node) for node in ast.walk(tree))
        result["has_docstring"] = has_docstring
        if not has_docstring:
            result["issues"].append("Missing function docstring")
        
        # Variable naming check
        result["naming_issues"] = check_variable_naming(tree)
        result["issues"].extend(result["naming_issues"])
    
    # 4. Scoring Rubric (0-100)
    score = 100
    if result["has_placeholder"]:
        score -= 40
    if not result["has_docstring"]:
        score -= 20
    if result["naming_issues"]:
        score -= 15 * len(result["naming_issues"])
    
    result["score"] = max(0, score)
    result["pass"] = result["score"] >= 70  # Passing threshold
    
    return result

def main():
    try:
        logging.info("Starting AI Evaluation Harness")
        
        # Load data
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        report = []
        passed_count = 0
        
        for item in data:
            logging.info(f"Evaluating item {item['id']}")
            eval_result = evaluate_code(item["code"])
            
            report_item = {
                "id": item["id"],
                "expected": item.get("expected", ""),
                "syntax_valid": eval_result["syntax_valid"],
                "has_placeholder": eval_result["has_placeholder"],
                "has_docstring": eval_result["has_docstring"],
                "naming_issues": eval_result["naming_issues"],
                "score": eval_result["score"],
                "pass": eval_result["pass"],
                "issues": eval_result["issues"]
            }
            report.append(report_item)
            
            if eval_result["pass"]:
                passed_count += 1
        
        # Generate final report
        summary = {
            "total": len(report),
            "passed": passed_count,
            "failed": len(report) - passed_count,
            "average_score": round(sum(r["score"] for r in report) / len(report), 2),
            "timestamp": datetime.now().isoformat()
        }
        
        final_report = {
            "evaluations": report,
            "summary": summary
        }
        
        # Save report
        with open('report.json', 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2)
        
        logging.info("Evaluation completed successfully!")
        print("✅ Evaluation complete!")
        print(f"📊 Summary: {summary['passed']}/{summary['total']} passed | Avg Score: {summary['average_score']}")
        print("📁 Check report.json and evaluation.log for details")
        
    except Exception as e:
        logging.error(f"Critical error: {str(e)}")
        print(f"❌ Error occurred: {str(e)}")

if __name__ == "__main__":
    main()