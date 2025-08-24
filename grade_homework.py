import json
import nbformat
import subprocess
import sys
import re
import traceback

def execute_notebook(notebook_path):
    """
    Executes a Jupyter notebook by extracting its code and running it as a script.
    """
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
    except Exception as e:
        return None, f"Error reading notebook file: {e}"

    full_code = ""
    for cell in nb.cells:
        if cell.cell_type == 'code':
            # Remove the placeholder lines to prevent syntax errors if student forgets
            clean_source = re.sub(r".*# YOUR CODE HERE.*", "", cell.source)
            full_code += clean_source + '\n'

    if "ga_qap = GeneticAlgorithmQAP" not in full_code:
        return None, "The GA instance `ga_qap` was not found. Please complete the configuration."

    try:
        process = subprocess.run(
            [sys.executable, '-c', full_code],
            capture_output=True,
            text=True,
            timeout=240  # 4-minute timeout
        )
        
        if process.returncode != 0:
            return None, f"Code execution failed with an error:\n{process.stderr}"
            
        return process.stdout, None
    except subprocess.TimeoutExpired:
        return None, "Code execution timed out after 4 minutes."
    except Exception as e:
        return None, f"An unexpected error occurred during execution: {e}"

def grade_result(output):
    """
    Parses the output to find the final cost and calculates a score.
    """
    if output is None:
        return 0, "Could not get output from the notebook."

    # The optimal value from the solution file
    OPTIMAL_COST = 1491.43
    TOLERANCE = 0.10  # 10% tolerance for full marks

    # Regex to find the line with the final cost
    match = re.search(r"Best Assignment Cost:\s*([0-9.]+)", output, re.IGNORECASE)

    if not match:
        return 0, "Could not find the 'Best Assignment Cost' in the output. Make sure it is printed."

    try:
        student_cost = float(match.group(1))
    except ValueError:
        return 0, f"Could not parse the cost value '{match.group(1)}'."

    # Calculate the absolute percentage error
    # Avoid division by zero if the optimal cost is somehow 0
    error = abs(student_cost - OPTIMAL_COST) / OPTIMAL_COST if OPTIMAL_COST != 0 else float('inf')

    score = 0
    if error <= TOLERANCE:
        score = 10.0
    elif error < 1.0: # Linear score decrease up to 100% error
        score = 10.0 * (1 - (error - TOLERANCE) / (1.0 - TOLERANCE))
    else:
        score = 0.0
    
    score = round(score, 2)
    
    feedback = (
        f"Grading based on the final assignment cost.\n"
        f"Target Cost: ~{OPTIMAL_COST:.2f}\n"
        f"Your Final Cost: {student_cost:.2f}\n"
        f"Error: {error:.2%}\n"
        f"Score: {score}/10"
    )
    
    return score, feedback

def main():
    notebook_path = 'L8_casestudy_assignment.ipynb'
    output, error_message = execute_notebook(notebook_path)

    if error_message:
        score = 0
        feedback = error_message
    else:
        score, feedback = grade_result(output)

    test_result = {
        'tests': [
            {
                'name': 'Facility Layout Optimization',
                'score': score,
                'max_score': 10,
                'output': feedback,
            }
        ]
    }
    
    print(json.dumps(test_result))

if __name__ == "__main__":
    main()
