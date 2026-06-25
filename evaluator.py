import json
import ast
import logging
import re
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

def build_parent_map(node):
    parent_map = {}
    for parent in ast.walk(node):
        for child in ast.iter_child_nodes(parent):
            parent_map[child] = parent
    return parent_map


def node_has_docstring(node) -> bool:
    """Check if a module/class/function node has a docstring."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
        return bool(ast.get_docstring(node))
    return False


def is_loop_or_comprehension_target(name_node, parent_map) -> bool:
    parent = parent_map.get(name_node)
    if parent is None:
        return False
    if isinstance(parent, (ast.For, ast.AsyncFor, ast.comprehension)):
        return any(child is name_node for child in ast.walk(parent.target))
    if isinstance(parent, ast.NamedExpr):
        return parent.target is name_node
    return False


def is_function_arg(name_node, parent_map) -> bool:
    parent = parent_map.get(name_node)
    return isinstance(parent, ast.arg)


def is_math_context(name_node, parent_map) -> bool:
    parent = parent_map.get(name_node)
    if isinstance(parent, (ast.BinOp, ast.UnaryOp, ast.Compare, ast.BoolOp, ast.IfExp)):
        return True
    return False


def get_short_named_parameters(node) -> set:
    params = set()
    for child in ast.walk(node):
        if isinstance(child, ast.FunctionDef):
            for arg in child.args.args:
                if arg.arg.islower() and len(arg.arg) == 1:
                    params.add(arg.arg)
            for arg in child.args.kwonlyargs:
                if arg.arg.islower() and len(arg.arg) == 1:
                    params.add(arg.arg)
            if child.args.vararg and child.args.vararg.arg.islower() and len(child.args.vararg.arg) == 1:
                params.add(child.args.vararg.arg)
            if child.args.kwarg and child.args.kwarg.arg.islower() and len(child.args.kwarg.arg) == 1:
                params.add(child.args.kwarg.arg)
    return params


def get_loop_targets(node) -> set:
    targets = set()
    for child in ast.walk(node):
        if isinstance(child, (ast.For, ast.AsyncFor, ast.comprehension)):
            for name_node in ast.walk(child.target):
                if isinstance(name_node, ast.Name) and name_node.id.islower() and len(name_node.id) == 1:
                    targets.add(name_node.id)
    return targets


def check_variable_naming(node) -> list:
    """Check for poor variable naming, allowing short names in loops, params, or math contexts."""
    issues = set()
    parent_map = build_parent_map(node)
    allowed_math_vars = {'x', 'y', 'z', 'n', 'm', 't'}
    param_names = get_short_named_parameters(node)
    loop_names = get_loop_targets(node)

    for child in ast.walk(node):
        if not isinstance(child, ast.Name):
            continue
        name = child.id
        if not name.islower() or len(name) != 1:
            continue

        if name in param_names or name in loop_names:
            continue

        if name in allowed_math_vars and is_math_context(child, parent_map):
            continue

        issues.add(name)

    return [f"Poor variable name: '{name}'" for name in sorted(issues)]

def detect_placeholder(tree, code: str) -> bool:
    """Detect placeholder comments or placeholder text in docstrings using regex with word boundaries."""
    placeholder_regex = re.compile(r"\b(?:to be implemented|todo|placeholder|implement later|tbd|coming soon)\b", re.I)

    # Check inline comments only (reduce false positives)
    for line in code.splitlines():
        if "#" in line:
            comment = line.split("#", 1)[1]
            if placeholder_regex.search(comment):
                return True

    # Check docstrings on module, classes and functions
    try:
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node)
                if doc and placeholder_regex.search(doc):
                    return True
    except Exception:
        # If docstring extraction fails for any reason, fall back to regex over entire code
        pass

    # Fallback: search whole code with word boundaries
    return bool(placeholder_regex.search(code))

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
    
    # 2. Placeholder Check (robust via regex in comments/docstrings)
    if result["syntax_valid"]:
        if detect_placeholder(tree, code):
            result["has_placeholder"] = True
            result["issues"].append("Contains weak placeholder comments")
    
    # 3. Advanced Checks (only if syntax is valid)
    if result["syntax_valid"]:
        # Docstring check (module, class, and function-level)
        has_docstring = any(node_has_docstring(node) for node in ast.walk(tree))
        result["has_docstring"] = has_docstring
        if not has_docstring:
            result["issues"].append("Missing docstring (module, class, or function level)")
        
        # Variable naming check
        result["naming_issues"] = check_variable_naming(tree)
        result["issues"].extend(result["naming_issues"])
    
    # 4. Scoring Rubric (0-100) - follows README percentages exactly
    # Weights: Syntax (40), No Placeholders (40), Docstring (10), Good Variable Names (10)
    score = 100
    if result["has_placeholder"]:
        score -= 40
    # Docstring check weight: 10 points
    if not result["has_docstring"]:
        score -= 10
    # Variable naming: if any naming issues, deduct the full 10 points
    if result["naming_issues"]:
        score -= 10

    result["score"] = max(0, score)
    # Syntax correctness is required: if syntax invalid we've already returned with score 0
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