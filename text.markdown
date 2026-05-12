# Entra IDのグループ設定をRLS設定などに反映することはできるか？
## Azure DB
結論：可能（Unity Catalog が前提）
### 行フィルター（Row Filter） ＋ 列マスク（Column Mask）
SQL 関数をテーブルに適用し、クエリ実行時に WHERE 句を自動注入する方式。
```sql
-- 行フィルター関数の定義
CREATE FUNCTION my_catalog.my_schema.region_filter(region STRING)
RETURN IF(
  is_account_group_member('sales_japan'), region = 'JP',
  is_account_group_member('sales_admin'), TRUE,
  FALSE
);

-- テーブルへの適用
ALTER TABLE my_catalog.my_schema.sales
SET ROW FILTER my_catalog.my_schema.region_filter ON (region);
```
### ABAC（Attribute-Based Access Control）
タグとポリシーで一括適用。テーブルごとに設定不要で、新テーブルも自動適用される。

## Azure Managed Grafana
ログインしたら、以下の情報は変数としてwhere句に埋め込めるが、グループ情報はない。
${__user} の利用可能フィールド
変数	内容
${__user.id}	Grafana 内部のユーザー ID
${__user.login}	ログイン名（メールアドレス等）
${__user.email}	メールアドレス

将来、Entra IDをデータソースの接続に再利用できるかも
https://techcommunity.microsoft.com/blog/azureobservabilityblog/introducing-azure-managed-grafana-12/4500673


## Power BI
結論：可能。Entra ID グループを Power BI のロールに割り当てることで、グループ単位の行フィルタが実現できる。

### 動的 RLS の設定手順

#### ステップ①：ユーザーマッピングテーブルを用意

| UserEmail | Region | Department |
|-----------|--------|------------|
| alice@contoso.com | JP | Sales |
| bob@contoso.com | US | Finance |

#### ステップ②：DAX でロールを定義（Power BI Desktop）

-- ロール「DynamicRLS」の DAX フィルタ式
[UserEmail] = USERPRINCIPALNAME()

#### ステップ③：Power BI Service でロールに Entra ID グループを割り当て
セマンティックモデル → セキュリティ → ロール「DynamicRLS」
  └─ Entra ID グループ（例：sales_japan@contoso.com）を追加
→ グループメンバーは自動的にフィルタ対象になる。
→ グループ追加・削除は Entra ID 側で管理するだけで OK。

### RLS の仕組み（Report Server）
Power BI Desktop でロールと DAX フィルタを定義し、  
Report Server に発行後にロールへグループを割り当てる点は Service と共通。

-- 動的 RLS の DAX 例
[UserEmail] = USERPRINCIPALNAME()

Entra ID グループとの連携
Report Server 環境では、Entra ID グループを AD Connect でオンプレ AD に同期することで、
Windows グループとして RLS のロール割り当てに使用できる。

Entra ID グループ
  → AD Connect でオンプレ AD グループに同期
  → Report Server のロールに AD グループを割り当て
  → ユーザーアクセス時に DAX フィルタが自動適用

## Tableau
### 結論：✅ 可能。`ISMEMBEROF()` 関数で Entra ID グループによる行フィルタが実装できる。

### RLS の実装方式（3パターン）
| 方式 | 概要 | 推奨度 |
|------|------|-------|
| **データポリシー（Virtual Connection）** | 仮想接続単位で RLS を集中管理 | ⭐ 推奨（v2021.4〜・Data Management 要） |
| **ユーザーフィルター** | ワークブック単位で設定 | △ 小規模向け |
| **DB 側 RLS** | DB（Databricks / PostgreSQL 等）で制御 | ⭐ 最強 |

### Entra ID グループとの連携の流れ
1. Entra ID グループを SCIM で Tableau Server に同期
2. Tableau Server のグループとして登録される
3. データポリシー内で ISMEMBEROF() を使ったポリシー条件を定義
---
### データポリシー例（DAX 相当の Tableau 計算式）
-- 「Managers グループは全行表示、それ以外は自分のレコードのみ」
ISMEMBEROF('Managers') OR USERNAME() = [employee_name]

-- 「sales_japan グループは JP 地域のみ表示」
ISMEMBEROF('sales_japan') AND [region] = 'JP'

---
### エンタイトルメントテーブル方式
データテーブルに直接ユーザー情報がない場合、マッピング用テーブルを別途用意。
| user_email | region | department |
|-----------|--------|-----------|
| alice@contoso.com | JP | Sales |
| bob@contoso.com | US | Finance |
→ JOIN またはデータポリシー内で参照して動的に行フィルタ。
---
### 対応まとめ
| ユースケース | 対応可否 |
|------------|---------|
| Entra ID グループ単位の閲覧制限 | ✅ プロジェクト/ワークブック権限 |
| Entra ID グループ単位の行フィルタ（RLS） | ✅ ISMEMBEROF() で対応 |
| 動的 RLS（ログインユーザー毎） | ✅ USERNAME() で対応 |
| ネストされたグループ | ✅ 対応（SCIM 同期時にフラット化可能） |
| 一元管理（複数ワークブック横断） | ✅ Virtual Connection でデータポリシー化 |

## Apache Superset
結論：✅ 可能。Entra ID グループ → Superset ロールマッピング → RLS ルールという流れで対応。

### 仕組み
Entra ID グループ
  → OAuth トークンに groups クレームとして含める
  → Superset の AUTH_ROLES_MAPPING で Superset ロールに変換
  → RLS ルールを Superset ロールに紐付け
  → SQL クエリに WHERE 句を自動注入

### AUTH_ROLES_MAPPING の設定例

``` python
# superset_config.py

AUTH_ROLES_MAPPING = {
    # Entra ID グループの Object ID → Superset ロール名
    "8bab1c86-8fba-33e5-2089-1d1c80ec267d": ["Admin"],
    "12345678-aaaa-bbbb-cccc-1234567890ab": ["sales_japan_role"],
    "abcdefab-1234-5678-90ab-cdefabcdef12": ["sales_admin_role"],
}

AUTH_ROLES_SYNC_AT_LOGIN = True  # ログイン毎にグループ同期
```

### RLS ルールの定義（Superset UI）
Settings → Row Level Security → ＋ Rule
Name: Japan Sales Filter
Filter Type: Regular
Tables: sales
Roles: sales_japan_role
Group Key: region_filter
Clause: region = 'JP'

### Jinja テンプレートで動的フィルタ
``` python
-- ユーザー情報を WHERE 句に動的展開
user_email = '{{ current_username() }}'

-- ロール情報を使用
{% if 'sales_admin_role' in current_user_roles() %}
  1 = 1
{% else %}
  region = '{{ current_user_info()["region"] }}'
{% endif %}
```


# 費用
## Azure DB
アーキ
```
【取り込みあり】
PostgreSQL → Lakeflow Connect（ETL） → Delta Lake（Unity Catalog） → SQL Warehouse → Dashboard

【参照のみ（Federation）】
PostgreSQL ←→ Lakehouse Federation（フェデレーテッドクエリ） → SQL Warehouse → Dashboard
```
本番 BI 用途・多ユーザー向け → 取り込みあり（Delta Lake の高速クエリで DBU を節約）
検証・小規模・リアルタイムデータが必須 → Federation（手軽に始められる）

Azure Databricks の費用は DBU（Databricks Unit）料金 ＋ Azure インフラ料金（VM・ストレージ等） の合算。
2026年4月1日より Standard ティアの新規作成が廃止。2026年10月1日までに既存 Standard は自動的に Premium へ移行

###共通コスト:SQL Warehouse（ダッシュボード表示）
どちらの方式でも、ダッシュボード表示には SQL Warehouse の費用がかかります。
SQL Warehouse タイプ	DBU 単価（目安）	特徴
Serverless SQL	~$0.70 / DBU	VM 費用込み、起動が速い
Pro SQL（Classic）	~$0.55 / DBU + VM 代	高機能、中規模向け
Classic SQL	~$0.22 / DBU + VM 代	低コスト、シンプル

### 取り込みあり（Lakeflow Connect ＋ Delta Lake）
コスト項目	内容	単価目安
Lakeflow Connect（ETL）	PostgreSQL → Delta Lake へのパイプライン実行	~$0.35 / DBU（Premium）
Serverless パイプライン	データ取り込み処理のコンピュート	Serverless DBU 消費
ストレージ（Delta Lake）	Azure Data Lake Storage Gen2	~$0.02〜0.023 / GB / 月
SQL Warehouse	ダッシュボードのクエリ実行	上記参照
無料枠	ワークスペースあたり 100 DBU/日 が無料	✅ 小規模ならほぼ無料
特徴：

初期の取り込みコストは発生するが、ダッシュボードのクエリは Delta Lake（高速・最適化済み） に対して実行されるためレスポンスが速く、クエリ費用は低くなりやすい
PostgreSQL への負荷がない
データの鮮度はパイプライン頻度に依存（リアルタイムではない）

### 参照のみ（Lakehouse Federation）
コスト項目	内容	単価目安
フェデレーション接続	Unity Catalog 設定のみ、接続自体は無料	$0
SQL Warehouse	クエリ実行時に PostgreSQL からデータを取得し処理	上記参照
PostgreSQL 側の負荷	Databricks → PostgreSQL へクエリが直接実行される	PostgreSQL 側のコストに依存
特徴：

ETL コスト・ストレージコストが不要
ただし、ダッシュボード表示のたびに PostgreSQL へクエリが飛ぶため：
レスポンスが遅くなりやすい
Databricks 側の DBU 消費も増える（フルスキャンが多い）
PostgreSQL サーバーへの負荷が増加
 
## Azure Managed Grafana
Standard ティアの料金（USD・East US 参考）
課金項目	単価
インスタンス稼働費（通常）	$0.043 / 時間（約 $31 / 月）
インスタンス稼働費（ゾーン冗長）	$0.051 / 時間（約 $37 / 月）
アクティブユーザー費	$6 / ユーザー / 月
アクティブユーザー = 対象月にログインしたユーザー数。
閲覧のみの月はカウントされないケースがある（公式で要確認）。

https://azure.microsoft.com/ja-jp/pricing/calculator/


## Power BI
ライセンス体系の変更（2025年11月〜 SQL Server 2025 より）
変更点	以前（〜SQL Server 2022）	現在（SQL Server 2025〜）
対象エディション	Enterprise のみ	Standard でも OK
SA（ソフトウェアアシュアランス）	必須	不要
✅ SQL Server 2025 Standard を購入すれば Power BI Report Server が使える。
これにより、以前より大幅にコストダウンが可能。

SQL Server 2025 Standard Edition 永続的 1 サーバー ライセンスおよび 10 CAL
https://www.microsoft.com/ja-jp/d/sql-server-2025-standard-edition/dg7gmgf0vnjs


**Azure VNet 内で閉域、データを Azure 上に置いてよい	Power BI Service ＋ Private Link**
上記でもよいならレポートサーバは必要なし

料金体系の全体像
Power BI の料金は 「作成者（Publisher）」と「閲覧者（Viewer）」で必要ライセンスが異なる。

作成者（レポート作成・発行）：Pro または PPU ライセンスが必須
閲覧者（ダッシュボード閲覧）：コンテンツの保存場所によって変わる

### ① ユーザーライセンス（Per-User）
ライセンス	月額（USD）	主な用途
Free	$0	My Workspace のみ・共有不可
Pro	$14 / ユーザー	レポート作成・共有・閲覧（基本機能）
Premium Per User（PPU）	$24 / ユーザー	高度な AI・大容量・高頻度更新
⚠️ 2025年4月の価格改定で Pro: $10→$14、PPU: $20→$24 に値上がり。

ダッシュボード閲覧者に Pro ライセンスが必要になるケース：
コンテンツが「共有ワークスペース（Premium 容量外）」に置かれている場合、
閲覧者も Pro ライセンスが必要。

### ② 容量ライセンス（Fabric Capacity / F-SKU）
容量ライセンスを使うと、閲覧者のライセンスコストをゼロにできる。

SKU	CU 数	月額目安（USD）	特徴
F2	2 CU	~$263 / 月	小規模・検証向け
F4	4 CU	~$526 / 月	小〜中規模
F8	8 CU	~$1,051 / 月	中規模
F32	32 CU	~$4,205 / 月	大規模
F64	64 CU	~$8,410 / 月	閲覧者ライセンス不要の境界線
✅ F64 以上の容量に置かれたコンテンツは、閲覧者は無料ライセンスで OK。
⚠️ F2〜F32 では、閲覧者も Pro ライセンスが必要。
💡 1年予約で約 40% 割引あり。




## Tableau
### ライセンス体系
Tableau は **ユーザーごとのロールベース** ライセンス。容量ライセンスはない。
| ロール | 主な用途 | Standard 月額 | Enterprise 月額 |
|-------|---------|--------------|----------------|
| **Creator** | ダッシュボード作成・データ接続 | $75 | $115 |
| **Explorer** | 既存データの分析・編集 | $42 | $70 |
| **Viewer** | 閲覧のみ | $15 | $35 |
> ⚠️ 年間契約のみ（月額契約は不可）。USD 単価。
---
### Tableau Server 固有の制約
| 項目 | 内容 |
|------|------|
| **最小ライセンス要件** | Creator 1名 必須 |
| **最小ユーザー数（Server）** | Viewer / Explorer は **100ユーザー以上から購入可** |
| **ライセンス購入形態** | BYOL（自社購入 → Azure VM に適用） |
---
### Azure VM インフラ費用（追加でかかる）
| リソース | 推奨スペック | 月額目安（USD） |
|---------|------------|---------------|
| Tableau Server VM | E8s_v5（8コア / 64GB）※最小 | ~$400/月 |
| Tableau Server VM（推奨本番） | E16s_v5（16コア / 128GB） | ~$800/月 |
| Azure Database for PostgreSQL（外部リポジトリ） | General Purpose 4vCore | ~$250/月 |
| マネージドディスク（Premium SSD） | 512 GB | ~$80/月 |
| 内部 Load Balancer | Standard | ~$20/月 |
| **合計（最小構成）** | — | **~$750/月** |
| **合計（本番冗長構成 ×3 ノード）** | — | **~$2,500/月** |
---
### コスト試算例
#### ケース A：閲覧者中心（Viewer 100名・Creator 2名）
Creator 2名 × $75 × 12 = $1,800/年
Viewer 100名 × $15 × 12 = $18,000/年
ライセンス計：$19,800/年（約 $1,650/月）

＋ Azure VM 等インフラ：約 $750/月
─────────────────────────────────
総額：約 $2,400/月（約 $28,800/年）

### 参考リンク
- [Self-Deploy Tableau Server on Microsoft Azure | Tableau Help](https://help.tableau.com/current/server/en-us/ts_azure_single_server.htm)
- [Configure SAML with Microsoft Entra ID | Tableau Help](https://help.tableau.com/current/server/en-us/saml_config_azure_server.htm)
- [Configure Tableau Server for SSO with Microsoft Entra ID | Microsoft Learn](https://learn.microsoft.com/en-us/entra/identity/saas-apps/tableauserver-tutorial)
- [Configure SCIM with Microsoft Entra ID | Tableau Help](https://help.tableau.com/current/online/en-us/scim_config_azure_ad.htm)
- [Create a Data Policy for Row-Level Security | Tableau Help](https://help.tableau.com/current/online/en-us/dm_vconn_create_rlspolicy.htm)
- [RLS Best Practices for Data Sources and Workbooks | Tableau Help](https://help.tableau.com/current/server/en-us/rls_bestpractices.htm)
- [Tableau Pricing | Tableau](https://www.tableau.com/pricing)
- [Tableau Server on Microsoft Azure deployment options | Tableau Help](https://help.tableau.com/current/server/en-us/ts_azure_deployment_options.htm)

## Apache Superset
ライセンス費用：$0（Apache 2.0 OSS）
公式コミュニティのみ

ただし注意：人件費・運用コスト
項目	影響
初期構築	中〜高（Docker / K8s 知識が必要）
カスタマイズ（SSO・RLS など）	コード設定が必要・難度中
アップデート対応	自社対応（マイナーバージョンで破壊的変更あり）
サポート	コミュニティのみ（商用サポートは Preset.io 別契約）
ドキュメント	やや散在・初級者には難しい
💡 ライセンスは無料だが、運用人材のスキルと工数が必要。中長期では人件費が支配的になりやすい。

# power BIのダッシュボードの認証をEntra IDで認証できるか？
方法 A：Entra ID Connect（AD 同期）＋ Windows 認証（推奨・閉域向け）

オンプレの Active Directory を Entra ID と同期し、  
Windows 認証（Kerberos/NTLM）経由でシームレス SSO を実現する構成。
ユーザー（Entra ID アカウント）
→ AD Connect でオンプレ AD と同期
→ Windows 認証（Kerberos）で Report Server にアクセス
→ SSO でダッシュボード閲覧

**ポイント：**
- ユーザーは Entra ID のアカウントで Windows ログイン済みなら自動認証
- 追加開発不要・最も安定した構成
- 完全閉域でも動作（Entra Connect の同期は定期的なインターネット接続が必要）
#### 方法 B：Microsoft Entra アプリケーションプロキシ（部分的な閉域向け）
Entra Application Proxy を経由して HTTPS アクセスし、  
Kerberos 制約付き委任（KCD）で Report Server に認証を委任する方式。
> ⚠️ Application Proxy 自体が Microsoft クラウドへの接続を必要とするため、  
> **完全閉域（インターネット切断）環境では利用不可**。  
> 閉域 VNet 内に限定したアクセスなら検討余地あり。
#### 方法 C：カスタムセキュリティ拡張（開発コストあり）
OIDC や SAML を処理するカスタム拡張を開発・登録する方式。  
実装難度が高く、メンテナンスコストもかかるため非推奨。
---
### 認証方式の比較まとめ
| 方式 | 閉域対応 | Entra ID 連携 | 実装コスト |
|------|---------|--------------|-----------|
| AD Connect ＋ Windows 認証 | ✅ | ✅（同期経由） | 低 |
| Entra Application Proxy | ⚠️ 部分的 | ✅ | 中 |
| カスタムセキュリティ拡張 | ✅ | ✅ | 高 |
> **閉域環境の推奨：AD Connect でオンプレ AD と Entra ID を同期 → Windows 認証**

https://learn.microsoft.com/en-us/power-bi/report-server/microsoft-entra-application-proxy

# Apache Supersetのロゴマーク非表示設定が可能か？
結論：✅ 可能。複数の方法あり。

方法①：APP_ICON を空文字に設定（推奨・最も簡単）
``` python
superset_config.py
APP_ICON = ""  # 空にするとロゴが非表示
APP_NAME = ""  # アプリ名も非表示にする場合
```

関連カスタマイズ可能項目
設定項目	内容
APP_NAME	ヘッダーのアプリ名
APP_ICON	ロゴ画像パス
LOGO_TARGET_PATH	ロゴクリック時の遷移先
LOGO_TOOLTIP	ロゴホバー時のツールチップ
LOGO_RIGHT_TEXT	ロゴ右側のテキスト
FAVICONS	ブラウザタブのアイコン

# 容量ライセンスが必要な理由
Fabric Capacity（F-SKU）が必要な理由
一言で言うと：「閲覧者ライセンスをゼロにするため」と「処理リソースを確保するため」
背景：Power BI の基本ルール
コンテンツが「共有ワークスペース（通常）」に置かれている場合
  → 作成者も閲覧者も、全員 Pro ライセンス（$14/人/月）が必要
つまり、閲覧者が100人いたら $14 × 100 = $1,400/月 が閲覧だけでかかる。

F-SKU を買うと何が変わるか
コンテンツを「Fabric 容量ワークスペース」に置く
  → 作成者は Pro ライセンスが必要（$14/人）
  → 閲覧者は無料ライセンスで OK（$0）
F-SKU は「テナント全体で使える処理能力のプール」を購入するイメージ。
閲覧者は個別ライセンスではなく、この容量プールを共有して使う。

必要になる典型的なシナリオ
シナリオ	F-SKU なし	F-SKU あり（F64〜）
閲覧者 10 人	$14 × 10 = $140/月	F64 = $8,410/月（割高）
閲覧者 100 人	$14 × 100 = $1,400/月	F64 = $8,410/月（まだ割高）
閲覧者 600 人	$14 × 600 = $8,400/月	F64 = $8,410/月（ほぼ同額）
閲覧者 1,000 人	$14 × 1,000 = $14,000/月	F64 = $8,410/月（安くなる）
閲覧者が約600人を超えると F64 のほうが安くなる。

F-SKU のもう一つの役割：処理能力の確保
ライセンスコスト削減だけでなく、以下の用途にも使う。

機能	必要な理由
大容量セマンティックモデル（100GB超）	共有容量では制限される
高頻度データ更新（48回/日以上）	Pro は 8回/日が上限
AI・機械学習機能	F-SKU または PPU が必要
Fabric 全機能（Data Factory、Lakehouse 等）	F-SKU が前提
