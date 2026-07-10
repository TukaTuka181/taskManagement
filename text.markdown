
# Detection of Abnormal Access to SQL
SecurityAlert
| where ProductName == "Microsoft Defender for Cloud"
| where AlertType startswith "SQL"
| where AlertSeverity in ("High", "Medium")

# SQL Configuration Risk Detection
SecurityRecommendation
| where AssessedResourceId contains "/Microsoft.Sql/"
      or DisplayName has "SQL"




# Detection of Abnormal Access to VM
SecurityAlert
| where ProductName == "Microsoft Defender for Cloud"
| where ResourceId contains "/Microsoft.Compute/"

# VM Configuration Risk Detection
SecurityRecommendation
| where AssessedResourceId contains "/Microsoft.Compute/"
      or DisplayName has "VM"
