- 30m:コンテナレジストリの監視(不審なPush/Pull)
    コンテナレジストリへの不審なPushやPullを検知したい。
    目的は、サプライチェーンに脆弱性がないようにするため。
    Defenderからどのようなログが送られてくるか？
    ＝＞不審なPushやPullは検知不可
        デプロイされたイメージに脆弱性があれば、推奨事項としてログに格納される。
        コンテナに関する推奨事項事項は下記のリンクから確認。
        種類：脆弱性評価を条件に検出すればよさげ。

        https://learn.microsoft.com/en-us/azure/defender-for-cloud/recommendations-reference-container

    推奨事項はどのようにLog Analyticsのテーブルに格納される？
    ＝＞下記のサイトから確認。
        https://github.com/Azure/Microsoft-Defender-for-Cloud/blob/main/Powershell%20scripts/Workflow%20automation%20and%20export%20data%20types%20schemas/Recommendation.schema.json


    **コンテナの脆弱性診断管理にはMDMVの有効化が必要。**
    Registry accessをDefender for Containersプランで有効化する必要がある。
    https://learn.microsoft.com/en-us/azure/defender-for-cloud/agentless-vulnerability-assessment-azure

    **Image Vulnerability Detection**
    LLM02
    ```
    SecurityRecommendation
    | where RecommendationDisplayName has "vulnerability"
        or RecommendationDisplayName has "vulnerabilities"
        or Description has "vulnerability"
        or Description has "vulnerabilities"
    ```

- 1h:app serviceの検出ルール
Defender for App ServiceまたはAPIMの診断設定から異常検知(サービスやAPIへの不審リクエストや、コマンドインジェクションなど)を行いたい。
## Defender(APIs/App Service)のアラート
(Web shell検出、コマンドインジェクション試行、異常なAPI呼び出しパターンなど)は、Defender for Cloudのセキュリティアラートとして生成されます。

## APIMの診断設定
閉域アクセス以外からのリクエスト、特定URLへの集中アクセス等を補完する 。

##　Defenderの推奨事項

【LLM02】API Attack Detection
```
SecurityAlert
| where ProductName == "Microsoft Defender for Cloud"
| where ResourceId has "Microsoft.ApiManagement"
| where AlertSeverity in ("High", "Medium")
```

【LLM02】Traffic Anomaly Detection
```
ApiManagementGatewayLogs
| where TimeGenerated > ago(1d)
| summarize RequestCount = count() by CallerIpAddress, bin(TimeGenerated, 15m)
| make-series Trend = sum(RequestCount) on TimeGenerated from ago(1d) to now() step 15m by CallerIpAddress
| extend (Anomalies, Score, Baseline) = series_decompose_anomalies(Trend)
| mv-expand Anomalies, TimeGenerated, Trend
| where Anomalies != 0
```
- 1h:APIM 診断設定ログ活用

下記のサイトにクエリ例が載っている
https://learn.microsoft.com/en-us/azure/azure-monitor/reference/queries/apimanagementgatewaylogs
- 30mトークン消費量
```
test_CL
| where TimeGenerated > ago(1d)
| summarize TokenSum = sum(toreal(Token_CL)) by bin(TimeGenerated, 15m)
| make-series Trend = sum(TokenSum) on TimeGenerated from ago(1d) to now() step 15m
| extend (Anomalies, Score, Baseline) = series_decompose_anomalies(Trend)
| mv-expand Anomalies, TimeGenerated, Trend
| where Anomalies == 1
```
web/APIへの攻撃(不審リクエストや、コマンドインジェクションなど)のリスクを検知する分析ルールのKQLを作成して。
複数の分析ルールのKQLを作成して。
Log AnalyticsにはDefenderのセキュリティアラートと推奨事項、APIMの診断設定のログを格納するようにしている。

目的：さまざまなAIリスク(プロンプトインジェクションや情報漏洩)の検出を行い、問題がないかを確認したい。

どのサービス(APIM、Defender)のどこ(診断設定、セキュリティアラート、推奨事項)からどんな情報がLog Analytics Workspaceのどのテーブルに入るかを調査。

1.攻撃を検知できるのはどのログかを挙げる。
2.そのログからどのようなKQLで検知できるかを考える。
