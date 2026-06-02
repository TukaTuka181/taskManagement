import psycopg2
from pyspark.sql.types import (
    StructType, StructField,
    LongType, StringType, DecimalType, TimestampType
)
from decimal import Decimal
from datetime import datetime

# --- 接続情報 ---
pg_host = "mypg.privatelink.postgres.database.azure.com"
pg_port = 5432
pg_db   = "appdb"
pg_user = dbutils.secrets.get("kv-pg", "pg-user")
pg_pass = dbutils.secrets.get("kv-pg", "pg-pass")
jdbc_url = f"jdbc:postgresql://{pg_host}:{pg_port}/{pg_db}"

# ============================================================
# Step 1: PostgreSQL にテーブルを作成（psycopg2）
# ============================================================
ddl = """
CREATE TABLE IF NOT EXISTS public.orders (
    order_id     BIGINT       PRIMARY KEY,
    customer_id  VARCHAR(20)  NOT NULL,
    amount       NUMERIC(10,2) NOT NULL,
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orders_customer_id
    ON public.orders (customer_id);

CREATE INDEX IF NOT EXISTS idx_orders_created_at
    ON public.orders (created_at);
"""

with psycopg2.connect(
    host=pg_host, port=pg_port, dbname=pg_db,
    user=pg_user, password=pg_pass, sslmode="require",
) as conn:
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()

print("テーブル作成完了")

# ============================================================
# Step 2: モックデータを定義（Spark DataFrame）
# ============================================================
mock_rows = [
    (1001, "C-001", Decimal("1980.00"),  datetime(2026, 5, 28, 10, 15, 0)),
    (1002, "C-002", Decimal("3500.50"),  datetime(2026, 5, 28, 10, 22, 0)),
    (1003, "C-003", Decimal("720.00"),   datetime(2026, 5, 28, 11,  5, 0)),
    (1004, "C-001", Decimal("12000.00"), datetime(2026, 5, 28, 12, 40, 0)),
]

schema = StructType([
    StructField("order_id",    LongType(),         nullable=False),
    StructField("customer_id", StringType(),       nullable=False),
    StructField("amount",      DecimalType(10, 2), nullable=False),
    StructField("created_at",  TimestampType(),    nullable=False),
])

df = spark.createDataFrame(mock_rows, schema=schema)
df.show(truncate=False)

# ============================================================
# Step 3: PostgreSQL に追記（Spark JDBC）
# ============================================================
df.write \
  .format("jdbc") \
  .option("url", jdbc_url) \
  .option("dbtable", "public.orders") \
  .option("user", pg_user) \
  .option("password", pg_pass) \
  .option("sslmode", "require") \
  .mode("append") \
  .save()

print("データ投入完了")

# ============================================================
# Step 4: 確認（任意）
# ============================================================
verify_df = spark.read \
    .format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", "public.orders") \
    .option("user", pg_user) \
    .option("password", pg_pass) \
    .option("sslmode", "require") \
    .load()

verify_df.show(truncate=False)
