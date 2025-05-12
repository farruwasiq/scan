import os
import sys
import re
import traceback

def process_trivy_results(trivy_output):
    """
    Processes the Trivy text output from k8s scan, counts misconfigurations by severity,
    and formats a summary string in Markdown table format.

    Args:
        trivy_output (str): The standard output from the Trivy k8s command.

    Returns:
        tuple: (summary_string, has_issues)
            summary_string (str): A formatted string with the summary of the scan.
            has_issues (bool): True if any misconfigurations were found, False otherwise.
    """
    summary = ""
    has_issues = False
    severity_counts = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
        "UNKNOWN": 0,
    }
    resource_counts = {}

    print(f"Received Trivy output (length: {len(trivy_output)}):\n{trivy_output}")  # Debug

    if not trivy_output:
        summary = "Trivy scan completed. No output from Trivy k8s."
        print(summary)
        return summary, False

    lines = trivy_output.splitlines()
    resource_pattern = r"^(.*?)\s+([A-Za-z0-9/-]+)\s+(CRITICAL|HIGH|MEDIUM|LOW|UNKNOWN):\s*(\d+)"

    for line in lines:
        match = re.search(resource_pattern, line)
        if match:
            namespace, resource, severity, count = match.groups()
            count = int(count)
            has_issues = True
            severity_counts[severity] += count
            resource_key = f"{namespace.strip()}-{resource.strip()}"
            if resource_key not in resource_counts:
                resource_counts[resource_key] = {
                    "Namespace": namespace.strip(),
                    "Resource": resource.strip(),
                    "CRITICAL": 0,
                    "HIGH": 0,
                    "MEDIUM": 0,
                    "LOW": 0,
                    "UNKNOWN": 0,
                }
            resource_counts[resource_key][severity] = count

    summary += "## Trivy Kubernetes Misconfiguration Scan Summary\n\n"
    if has_issues:
        summary += "| Namespace | Resource | CRITICAL | HIGH | MEDIUM | LOW | UNKNOWN |\n"
        summary += "|-----------|----------|----------|------|--------|-----|---------|\n"
        for resource_data in resource_counts.values():
            summary += (
                f"| {resource_data['Namespace']} | {resource_data['Resource']} | {resource_data['CRITICAL']} | {resource_data['HIGH']} |"
                f" {resource_data['MEDIUM']} | {resource_data['LOW']} | {resource_data['UNKNOWN']} |\n"
            )
        summary += "\n"
        summary += "| Severity | Count |\n"
        summary += "|----------|-------|\n"
        for severity, count in severity_counts.items():
            summary += f"| {severity} | {count} |\n"
    else:
        summary += "No misconfigurations found.\n"

    print(f"Generated summary:\n{summary}")
    return summary, has_issues



def main(trivy_output):
    """
    Main function to process Trivy results and output a summary for GitHub Actions.

    Args:
        trivy_output (str): The standard output from the Trivy k8s command (passed as a command-line argument).
    """
    print(f"Python script started. GITHUB_STEP_SUMMARY: {os.environ.get('GITHUB_STEP_SUMMARY')}")  # Debug

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
    if len(sys.argv) > 1:
        trivy_output = sys.argv[1]
        main(trivy_output)
    else:
        print("Error: Trivy output is missing.")
        sys.exit(1)
