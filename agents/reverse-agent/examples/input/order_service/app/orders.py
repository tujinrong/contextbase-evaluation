"""静的解析用サンプル。ジェネレーターはこのコードを実行しない。"""


def create_order(connection, customer_id: int, total: int) -> int:
    """正の受注金額を検証し、受注を新規登録して採番されたIDを返す。"""
    if total <= 0:
        raise ValueError("受注金額は正の整数で指定してください")
    cursor = connection.execute(
        "INSERT INTO orders (customer_id, total, status) VALUES (?, ?, ?)",
        (customer_id, total, "new"),
    )
    connection.commit()
    return int(cursor.lastrowid)


def find_order(connection, order_id: int):
    """受注IDで照会する。存在しなければLookupErrorを送出する。"""
    row = connection.execute(
        "SELECT id, customer_id, total, status FROM orders WHERE id = ?",
        (order_id,),
    ).fetchone()
    if row is None:
        raise LookupError("対象の受注がありません")
    return row
