-- 動作確認サンプル。実プロジェクトの物理DB定義ではありません。
CREATE TABLE customers (
    id INTEGER NOT NULL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE orders (
    id INTEGER NOT NULL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    total DECIMAL(12, 2) NOT NULL CHECK (total > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'new',
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers(id)
);
CREATE INDEX ix_orders_customer ON orders(customer_id);
