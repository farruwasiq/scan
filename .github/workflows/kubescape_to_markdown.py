#!/usr/bin/env python3
import subprocess
import sys
from tabulate import tabulate

if len(sys.argv) < 2:
    print("Usage: python kubescape_to_markdown.py <results.json>")
    sys.exit(1)

input_file = sys.argv[1]

try:
    # Use jq to extract the needed control information directly
    jq_query = (
        ".summaryDetails.controls | to_entries | map({\"severity\": \"Medium\", "
        "\"control_name\": .value.name, "
        "\"doc_link\": \"https://hub.armosec.io/docs/\" + (.key | ascii_downcase), "
        "\"remediation\": (.value.resourceIDs | to_entries | map(.value.relatedObjects[] | "
        "(.rules?[]?.resources?[0] // .rules?[]?.verbs?[0] // .rules?[]?.apiGroups?[0] // .roleRef?.name // .subjects?[]?.name)) | join(\"\\n\"))
        })"
    )

    # Run the jq command to parse and filter the JSON
    result = subprocess.run(
        ["jq", "-c", jq_query, input_file],
        capture_output=True,
        text=True,
        check=True
    )

    # Convert the jq output to a table
    controls = eval(result.stdout)  # Convert to Python dict
    headers = ["Severity", "Control Name", "Docs", "Assisted Remediation"]
    table_data = [[ctrl['severity'], ctrl['control_name'], ctrl['doc_link'], ctrl['remediation']] for ctrl in controls]

    # Print the markdown table
    markdown_table = tabulate(table_data, headers, tablefmt="github")
    print(markdown_table)

except subprocess.CalledProcessError as e:
    print(f"Error running jq: {e}")
    sys.exit(1)
except FileNotFoundError:
    print(f"Error: File '{input_file}' not found.")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)
