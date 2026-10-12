CREATE SCHEMA IF NOT EXISTS DB2;
CREATE SCHEMA IF NOT EXISTS N2_DWH;
CREATE SCHEMA IF NOT EXISTS N2_SIGHT;
CREATE SCHEMA IF NOT EXISTS NAVI;

CREATE TABLE IF NOT EXISTS DB2.ＵＷＥＢログイン情報表 (
    アプリケーション名 VARCHAR(20) NOT NULL,
    ユーザーＩＤ VARCHAR(40) NOT NULL,
    パスワード VARCHAR(100) NOT NULL,
    融資系ユーザー名 VARCHAR(80),
    融資系所属店番 VARCHAR(4),
    債権書類権限 VARCHAR(4),
    決算書権限 VARCHAR(4),
    ＣＲＤ権限 VARCHAR(4),
    格付権限 VARCHAR(4),
    自己査定権限 VARCHAR(4),
    PRIMARY KEY (アプリケーション名, ユーザーＩＤ)
);

CREATE TABLE IF NOT EXISTS DB2.Ｕ職員名簿表 (
    職員番号 DECIMAL(18, 0) NOT NULL PRIMARY KEY,
    所属店番 DECIMAL(18, 0),
    漢字氏名 VARCHAR(40),
    カナ氏名 VARCHAR(40),
    身分コード DECIMAL(18, 0),
    性別 DECIMAL(18, 0),
    生年月日 DECIMAL(18, 0),
    役職コード DECIMAL(18, 0),
    作成日 DECIMAL(18, 0)
);

CREATE TABLE IF NOT EXISTS DB2.Ｕ職員所属課係一覧表 (
    職員番号 DECIMAL(8, 0) NOT NULL,
    所属課係コード VARCHAR(20) NOT NULL,
    PRIMARY KEY (職員番号, 所属課係コード)
);

CREATE TABLE IF NOT EXISTS DB2.ＵＪＶ役職コード表 (
    役職コード DECIMAL(4, 0) NOT NULL PRIMARY KEY,
    役職 VARCHAR(40)
);

CREATE TABLE IF NOT EXISTS N2_DWH.Ｊ事業所コード表２ (
    店舗コード DECIMAL(2, 0) NOT NULL,
    枝番 DECIMAL(2, 0) NOT NULL,
    事業所名 VARCHAR(80),
    PRIMARY KEY (店舗コード, 枝番)
);

CREATE TABLE IF NOT EXISTS DB2.ＵＤＢ管理ＤＢ (
    ＤＢ名 VARCHAR(80) NOT NULL PRIMARY KEY,
    処理中ＦＬＧ VARCHAR(1) NOT NULL
);

CREATE TABLE IF NOT EXISTS DB2.Ｕカウンターシフト (
    アクセス日付 VARCHAR(8) NOT NULL,
    アクセス時刻 VARCHAR(9) NOT NULL,
    機能ＩＤ VARCHAR(100),
    画面ＩＤ VARCHAR(100),
    コマンドＩＤ VARCHAR(100),
    アクションＩＤ VARCHAR(200),
    ＪＳＰ名 VARCHAR(260),
    ユーザーＩＤ VARCHAR(20) NOT NULL
);

-- Local H2 uses the same N2 customer-master name and required source columns.
CREATE TABLE IF NOT EXISTS N2_SIGHT.Ｂ顧客基本表 (
    店舗コード DECIMAL(18, 0) NOT NULL,
    顧客番号 DECIMAL(18, 0) NOT NULL,
    カナ氏名 VARCHAR(48),
    漢字氏名 VARCHAR(96),
    担当者コード DECIMAL(18, 0),
    電話番号 DECIMAL(18, 0),
    漢字住所 VARCHAR(160),
    性別コード VARCHAR(1),
    生年月日 DECIMAL(18, 0),
    PRIMARY KEY (店舗コード, 顧客番号)
);

-- Access pension tables. Production uses the same names in jdbc/RAROA_DB.
CREATE TABLE IF NOT EXISTS 性別テーブル (
    性別ｺｰﾄﾞ TINYINT NOT NULL PRIMARY KEY,
    性別 VARCHAR(10) NOT NULL
);

CREATE TABLE IF NOT EXISTS 裁定請求テーブル (
    裁請ｺｰﾄﾞ TINYINT NOT NULL PRIMARY KEY,
    裁定請求 VARCHAR(10) NOT NULL
);

CREATE TABLE IF NOT EXISTS 受給有無テーブル (
    受給ｺｰﾄﾞ TINYINT NOT NULL PRIMARY KEY,
    受給有無 VARCHAR(10) NOT NULL
);

CREATE TABLE IF NOT EXISTS 店名テーブル (
    店舗ｺｰﾄﾞ INTEGER NOT NULL PRIMARY KEY,
    店名 VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS 年金種類テーブル (
    種類ｺｰﾄﾞ INTEGER NOT NULL PRIMARY KEY,
    年金種類 VARCHAR(120) NOT NULL
);

CREATE TABLE IF NOT EXISTS 年金1_LK (
    店番 INTEGER,
    顧客番号 BIGINT,
    担当者コード INTEGER,
    顧客氏名 VARCHAR(100),
    ふりがな VARCHAR(100),
    性別 TINYINT,
    住所 VARCHAR(300),
    電話番号 DECIMAL(15, 0),
    生年月日 DATE,
    "種類：国民年金" BOOLEAN,
    "種類：厚生年金" BOOLEAN,
    "種類：共済年金" BOOLEAN,
    "種類：厚生年金基金" BOOLEAN,
    "種類：国民年金基金" BOOLEAN,
    年金種類 INTEGER,
    裁定請求 TINYINT,
    請求予定日 DATE,
    予定年齢 INTEGER,
    配偶者名 VARCHAR(100),
    配偶者生年月日 DATE,
    受給有無 TINYINT,
    予約徴求日 DATE,
    備考 VARCHAR(400),
    データ更新日 DATE,
    更新時間 TIME,
    更新者 INTEGER,
    "６ヶ月先確認" BOOLEAN,
    変更FLG TINYINT
);

CREATE TABLE IF NOT EXISTS 年金＿削除明細 (
    店番 INTEGER,
    顧客番号 BIGINT,
    担当者コード INTEGER,
    顧客氏名 VARCHAR(100),
    ふりがな VARCHAR(100),
    性別 TINYINT,
    住所 VARCHAR(300),
    電話番号 DECIMAL(15, 0),
    生年月日 DATE,
    "種類：国民年金" BOOLEAN,
    "種類：厚生年金" BOOLEAN,
    "種類：共済年金" BOOLEAN,
    "種類：厚生年金基金" BOOLEAN,
    "種類：国民年金基金" BOOLEAN,
    年金種類 INTEGER,
    裁定請求 TINYINT,
    請求予定日 DATE,
    予定年齢 INTEGER,
    配偶者名 VARCHAR(100),
    配偶者生年月日 DATE,
    受給有無 TINYINT,
    予約徴求日 DATE,
    備考 VARCHAR(400),
    データ更新日 DATE,
    更新時間 TIME,
    更新者 INTEGER,
    "６ヶ月先確認" BOOLEAN,
    変更FLG TINYINT
);

CREATE INDEX IF NOT EXISTS IX_NENKIN1_KEY ON 年金1_LK (ふりがな, 電話番号);
CREATE INDEX IF NOT EXISTS IX_NENKIN1_CUSTOMER ON 年金1_LK (店番, 顧客番号);
CREATE INDEX IF NOT EXISTS IX_NENKIN1_UPDATE ON 年金1_LK (変更FLG, データ更新日, 更新者);
CREATE INDEX IF NOT EXISTS IX_NENKIN_DELETE_UPDATE ON 年金＿削除明細 (データ更新日, 更新者);

-- Remove the obsolete Java-only substitute tables from an existing local database.
DROP TABLE IF EXISTS NENKIN_AUDIT;
DROP TABLE IF EXISTS NENKIN_RESERVATION;
DROP TABLE IF EXISTS NENKIN_BRANCH;
DROP TABLE IF EXISTS NENKIN_STAFF;
