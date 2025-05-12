import json
import os
import sys

def process_trivy_results(report_file="trivy-k8s-report.json"):
    """
    Processes the Trivy JSON report, counts vulnerabilities by severity,
    and formats a summary string.

    Args:
        report_file (str): The path to the Trivy JSON report file.

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

    try:
        with open(report_file, "r") as f:
            report_data = json.load(f)
    except FileNotFoundError:
        summary = f"Error: Trivy report file not found at {report_file}.  Trivy may have failed."
        return summary, True  # Return True to indicate an issue

    if not report_data:
        return "Trivy scan completed. No results to report (empty report).", False

    if not isinstance(report_data, list):
        summary = "Error: Trivy report data is not a list.  Unexpected format."
        return summary, True

    for result in report_data:
        if not isinstance(result, dict):
            summary = "Error: Result is not a dict. Unexpected format."
            return summary, True
        if 'Vulnerabilities' not in result:
            continue  #  No vulnerabilities in this result
        if not isinstance(result['Vulnerabilities'], list):
            summary = "Error: Vulnerabilities is not a list.  Unexpected format"
            return summary, True
        for vulnerability in result['Vulnerabilities']:
            if not isinstance(vulnerability, dict):
                summary = "Error: vulnerability is not a dict.  Unexpected format"
                return summary, True
            severity = vulnerability.get("Severity", "UNKNOWN")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            has_issues = True

    summary += "Trivy Kubernetes Misconfiguration Scan Summary:\n"
    if has_issues:
        for severity, count in severity_counts.items():
            summary += f"- {severity}: {count}\n"
    else:
        summary += "No misconfigurations found.\n"

    return summary, has_issues


def main():
    """
    Main function to process Trivy results and output a summary for GitHub Actions.
    """
    summary, has_issues = process_trivy_results()

    if os.environ.get("GITHUB_STEP_SUMMARY") == "true":
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            print(summary, file=f)  # Print to the summary file
    else:
        print(summary)  # Print to standard output

    if has_issues:
        print("::warning title=Trivy Scan Issues::Misconfigurations were found. Check the scan results for details.")
        #  Don't fail the action here.  We use continue-on-error
        #sys.exit(1) #  Remove this.  Let the workflow complete.


if __name__ == "__main__":
    main()