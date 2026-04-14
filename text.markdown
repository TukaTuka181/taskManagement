# オンプレ/クラウド配置条件


# 機能調査
- ダッシュボード作成機能調査
データソースから取得した情報をクエリで加工し、可視化する。


- 外部データ連携機能調査
    - Monitor
    - Log Analytics Workspace
    - Sentinel

Monitorは使用できる

log analyticsはmonitor経由で監視できる
https://learn.microsoft.com/ja-jp/azure/azure-monitor/logs/data-platform-logs?utm_source=chatgpt.com

sentinelは検出結果をlog analyticsに保存
https://docs.azure.cn/en-us/sentinel/security-alert-schema?utm_source=chatgpt.com


# 非機能調査
- Grafanaの権限制御(ID,passはあったと思う)
サーバー管理者
組織ロール（Viewer / Editor / Admin）　基本ロール
    Viewer → 見るだけ
    Editor → 作る・編集する
    Admin  → 何でもできる
    基本ロール　権限がありません。必要に応じてRBACを使用して権限を追加してください。
ダッシュボード・フォルダ権限

Grafana Enterprise
    データソースの権限
    役割ベースアクセス制御（RBAC）
        基本ロールに加えカスタムロールを作成可能
        だが基本ロールは含めなければいけない。
        ユーザーB：
        - 基本ロール：Viewer（基本は閲覧のみ）
        - カスタムロール：
            - dashboards:write（特定範囲だけ）


https://grafana.com/docs/grafana/latest/administration/roles-and-permissions/

- 負荷テスト



- AKSとGrafanaの両方の料金体系を調査
AKS
以下の三つの料金体系
Free
Standard SLA
Premium SLA＋LTS

https://azure.microsoft.com/ja-jp/pricing/calculator/?service=kubernetes-service

Grafana
