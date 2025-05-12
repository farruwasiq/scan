{
  apiVersion: .apiVersion,
  kind: .kind,
  name: .name,
  namespace: .namespace,
  controlsSummary: {
    total: .summaryDetails.controls | length,
    failed: (.summaryDetails.controls | map(select(.statusInfo.status == "failed")) | length),
    actionRequired: (.summaryDetails.controls | map(select(.statusInfo.status == "actionRequired")) | length)
  },
  resources: [.resourceResults[] | {
    resourceID: .resourceID,
    controls: (.controls[] | {
      controlName: .name,
      controlId: .controlID,
      severity: (.rules[0].severity // "N/A"),
      docs: (.rules[0].remediation // "N/A"),
      assistedRemediation: (.rules[0].fixPaths | join("\\n") // "N/A")
    })
  }]
}