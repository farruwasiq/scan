import os
import sys
import re
import traceback

def process_trivy_results(trivy_output):
    """
    Processes the Trivy text output from k8s scan and formats it into a detailed Markdown report.

    Args:
        trivy_output (str): The standard output from the Trivy k8s --report all command.

    Returns:
        tuple: (summary_string, has_issues)
            summary_string (str): A formatted string with the detailed summary of the scan.
            has_issues (bool): True if any misconfigurations were found, False otherwise.
    """
    summary = ""
    has_issues = False
    
    # Improved regex patterns
    resource_pattern = r"namespace:\s*(.*?),.*?([A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)?)(?:\s+\((.*?)\))?:\s*(\d+-\d+|\d+)"
    avd_pattern = r"AVD-KSV-(\d+)\s*\((.*?)\):\s*(.*)"
    code_snippet_pattern = r"^\s*(\d+\s*[│┌└]\s*.*)"
    
    print(f"Received Trivy output (length: {len(trivy_output)}):\n{trivy_output}")  # Debug

    if not trivy_output:
        summary = "Trivy scan completed. No output from Trivy k8s."
        print(summary)
        return summary, False

    lines = trivy_output.splitlines()
    current_namespace = ""
    current_resource = ""
    resource_type = "" # Addded resource type

    for i, line in enumerate(lines):
        namespace_match = re.search(r"namespace:\s*(.*?),", line)
        if namespace_match:
            current_namespace = namespace_match.group(1).strip()
            print(f"Found namespace: {current_namespace}")  # Debug

        resource_match = re.search(resource_pattern, line)
        if resource_match:
            current_resource = resource_match.group(2).strip()
            resource_type = resource_match.group(3).strip() # Capture resource type
            if resource_type:
                print(f"Found resource: {current_resource}, type: {resource_type}")
            else:
                print(f"Found resource: {current_resource}")
            
        avd_match = re.search(avd_pattern, line)
        if avd_match:
            has_issues = True
            avd_id, severity, title = avd_match.groups()
            severity = severity.strip().upper()
            title = title.strip()
            print(f"Found AVD: {avd_id}, Severity: {severity}, Title: {title}")  # Debug
            summary += f"### {avd_id} ({severity}): {title}\n\n"

            description_start = i + 1
            description_end = i + 1
            while description_end < len(lines) and not re.match(resource_pattern, lines[description_end]) and not re.match(avd_pattern, lines[description_end]):
                description_end += 1
            description = "\n".join(lines[description_start:description_end]).strip()
            summary += f"{description}\n\n"
            
            summary += f"* **Namespace**: {current_namespace}, **Resource**: {current_resource}\n\n"
            if resource_type:
                 summary += f"  **Resource Type**: {resource_type}\n\n"

            code_snippet = ""
            code_start_line = i + 1
            while code_start_line < len(lines):
                code_match = re.search(code_snippet_pattern, lines[code_start_line])
                if code_match:
                    code_snippet += code_match.group(1) + "\n"
                    code_start_line += 1
                elif re.match(resource_pattern, lines[code_start_line]) or re.match(avd_pattern, lines[code_start_line]):
                    break
                else:
                    code_start_line += 1
            if code_snippet:
                summary += "<details><summary>Code Snippet</summary>\n\n```yaml\n"
                summary += code_snippet.strip()
                summary += "\n```\n</details>\n\n"

    if not has_issues:
        summary = "No misconfigurations found.\n"
        print("No issues found")

    print(f"Generated summary:\n{summary}")
    return summary, has_issues



def main():
    """
    Main function to process Trivy results and output a summary for GitHub Actions.

    Args:
        trivy_output (str): The standard output from the Trivy k8s command (passed as a command-line argument).
    """
    print(f"Python script started. GITHUB_STEP_SUMMARY: {os.environ.get('GITHUB_STEP_SUMMARY')}")  # Debug
    trivy_output = sys.stdin.read() # Read from stdin

    summary, has_issues = process_trivy_results(trivy_output)

    if os.environ.get("GITHUB_STEP_SUMMARY"):
        summary_file_path = os.environ["GITHUB_STEP_SUMMARY"]
        print(f"Writing summary to: {summary_file_path}")  # Debug
        try:
            with open(summary_file_path, "a") as f:
                f.write(summary)
            print("Successfully wrote to GITHUB_STEP_SUMMARY")
        except Exception as e:
            print(f"Error writing to GITHUB_STEP_SUMMARY: {e}")
            traceback.print_exc()
    else:
        print(summary)

    if has_issues:
        print("::warning title=Trivy Scan Issues::Misconfigurations were found. Check the scan results for details.")



if __name__ == "__main__":
    main()