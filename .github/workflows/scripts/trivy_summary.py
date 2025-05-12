import os
import sys
import re

def process_trivy_results(trivy_output):
    """
    Processes the Trivy text output from k8s scan, counts vulnerabilities by severity,
    and formats a summary string.

    Args:
        trivy_output (str): The standard output from the Trivy k8s command.

    Returns:
        tuple: (summary_string, has_issues)
            summary_string (str): A formatted string with the summary of the scan.
            has_issues (bool): True if any vulnerabilities were found, False otherwise.
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

    if not trivy_output:
        return "Trivy scan completed. No output from Trivy k8s.", False

    #  Parse the text output.  This is more fragile than JSON, but necessary for trivy k8s
    lines = trivy_output.splitlines()
    for line in lines:
        if "CRITICAL" in line:
            match = re.search(r"CRITICAL:\s*(\d+)", line)
            if match:
                severity_counts["CRITICAL"] += int(match.group(1))
                has_issues = True
        elif "HIGH" in line:
            match = re.search(r"HIGH:\s*(\d+)", line)
            if match:
                severity_counts["HIGH"] += int(match.group(1))
                has_issues = True
        elif "MEDIUM" in line:
            match = re.search(r"MEDIUM:\s*(\d+)", line)
            if match:
                severity_counts["MEDIUM"] += int(match.group(1))
                has_issues = True
        elif "LOW" in line:
            match = re.search(r"LOW:\s*(\d+)", line)
            if match:
                severity_counts["LOW"] += int(match.group(1))
                has_issues = True
        elif "UNKNOWN" in line:
            match = re.search(r"UNKNOWN:\s*(\d+)", line)
            if match:
                severity_counts["UNKNOWN"] += int(match.group(1))
                has_issues = True

    summary += "Trivy Kubernetes Misconfiguration Scan Summary:\n"
    if has_issues:
        for severity, count in severity_counts.items():
            summary += f"- {severity}: {count}\n"
    else:
        summary += "No misconfigurations found.\n"

    return summary, has_issues



def main(trivy_output):
    """
    Main function to process Trivy results and output a summary for GitHub Actions.

    Args:
        trivy_output (str): The standard output from the Trivy k8s command (passed as a command-line argument).
    """
    summary, has_issues = process_trivy_results(trivy_output)

    if os.environ.get("GITHUB_STEP_SUMMARY") == "true":
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            print(summary, file=f)  # Print to the summary file
    else:
        print(summary)  # Print to standard output

    if has_issues:
        print("::warning title=Trivy Scan Issues::Misconfigurations were found. Check the scan results for details.")



if __name__ == "__main__":
    if len(sys.argv) > 1:
        trivy_output = sys.argv[1]
        main(trivy_output)
    else:
        print("Error: Trivy output is missing.")
        sys.exit(1)
