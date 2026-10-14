/*
 * 年金業務用 SQL Server DDL (jdbc/RAROA_DB)
 * Access のリンク元と同じ表名・列名を使用する。
 * DB2.Ｕ職員名簿表と N2_SIGHT.Ｂ顧客基本表は既存 N2 Oracle 表のため作成しない。
 */
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

IF OBJECT_ID(N'dbo.性別テーブル', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[性別テーブル] (
        [性別ｺｰﾄﾞ] TINYINT NOT NULL,
        [性別] NVARCHAR(10) NOT NULL,
        CONSTRAINT [PK_性別テーブル] PRIMARY KEY ([性別ｺｰﾄﾞ])
    );
END;
GO

IF OBJECT_ID(N'dbo.裁定請求テーブル', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[裁定請求テーブル] (
        [裁請ｺｰﾄﾞ] TINYINT NOT NULL,
        [裁定請求] NVARCHAR(10) NOT NULL,
        CONSTRAINT [PK_裁定請求テーブル] PRIMARY KEY ([裁請ｺｰﾄﾞ])
    );
END;
GO

IF OBJECT_ID(N'dbo.受給有無テーブル', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[受給有無テーブル] (
        [受給ｺｰﾄﾞ] TINYINT NOT NULL,
        [受給有無] NVARCHAR(10) NOT NULL,
        CONSTRAINT [PK_受給有無テーブル] PRIMARY KEY ([受給ｺｰﾄﾞ])
    );
END;
GO

IF OBJECT_ID(N'dbo.店名テーブル', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[店名テーブル] (
        [店舗ｺｰﾄﾞ] INT NOT NULL,
        [店名] NVARCHAR(80) NOT NULL,
        CONSTRAINT [PK_店名テーブル] PRIMARY KEY ([店舗ｺｰﾄﾞ])
    );
END;
GO

IF OBJECT_ID(N'dbo.年金種類テーブル', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[年金種類テーブル] (
        [種類ｺｰﾄﾞ] INT NOT NULL,
        [年金種類] NVARCHAR(120) NOT NULL,
        CONSTRAINT [PK_年金種類テーブル] PRIMARY KEY ([種類ｺｰﾄﾞ])
    );
END;
GO

IF OBJECT_ID(N'dbo.年金1_LK', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[年金1_LK] (
        [店番] INT NULL,
        [顧客番号] BIGINT NULL,
        [担当者コード] INT NULL,
        [顧客氏名] NVARCHAR(100) NULL,
        [ふりがな] NVARCHAR(100) NULL,
        [性別] TINYINT NULL,
        [住所] NVARCHAR(300) NULL,
        [電話番号] DECIMAL(15,0) NULL,
        [生年月日] DATE NULL,
        [種類：国民年金] BIT NULL,
        [種類：厚生年金] BIT NULL,
        [種類：共済年金] BIT NULL,
        [種類：厚生年金基金] BIT NULL,
        [種類：国民年金基金] BIT NULL,
        [年金種類] INT NULL,
        [裁定請求] TINYINT NULL,
        [請求予定日] DATE NULL,
        [予定年齢] INT NULL,
        [配偶者名] NVARCHAR(100) NULL,
        [配偶者生年月日] DATE NULL,
        [受給有無] TINYINT NULL,
        [予約徴求日] DATE NULL,
        [備考] NVARCHAR(400) NULL,
        [データ更新日] DATE NULL,
        [更新時間] TIME(0) NULL,
        [更新者] INT NULL,
        [６ヶ月先確認] BIT NULL,
        [変更FLG] TINYINT NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.年金＿削除明細', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.[年金＿削除明細] (
        [店番] INT NULL,
        [顧客番号] BIGINT NULL,
        [担当者コード] INT NULL,
        [顧客氏名] NVARCHAR(100) NULL,
        [ふりがな] NVARCHAR(100) NULL,
        [性別] TINYINT NULL,
        [住所] NVARCHAR(300) NULL,
        [電話番号] DECIMAL(15,0) NULL,
        [生年月日] DATE NULL,
        [種類：国民年金] BIT NULL,
        [種類：厚生年金] BIT NULL,
        [種類：共済年金] BIT NULL,
        [種類：厚生年金基金] BIT NULL,
        [種類：国民年金基金] BIT NULL,
        [年金種類] INT NULL,
        [裁定請求] TINYINT NULL,
        [請求予定日] DATE NULL,
        [予定年齢] INT NULL,
        [配偶者名] NVARCHAR(100) NULL,
        [配偶者生年月日] DATE NULL,
        [受給有無] TINYINT NULL,
        [予約徴求日] DATE NULL,
        [備考] NVARCHAR(400) NULL,
        [データ更新日] DATE NULL,
        [更新時間] TIME(0) NULL,
        [更新者] INT NULL,
        [６ヶ月先確認] BIT NULL,
        [変更FLG] TINYINT NULL
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
     WHERE object_id = OBJECT_ID(N'dbo.年金1_LK')
       AND name = N'IX_年金1_LK_検索キー'
)
BEGIN
    CREATE INDEX [IX_年金1_LK_検索キー]
        ON dbo.[年金1_LK] ([ふりがな], [電話番号]);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
     WHERE object_id = OBJECT_ID(N'dbo.年金1_LK')
       AND name = N'IX_年金1_LK_顧客'
)
BEGIN
    CREATE INDEX [IX_年金1_LK_顧客]
        ON dbo.[年金1_LK] ([店番], [顧客番号]);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
     WHERE object_id = OBJECT_ID(N'dbo.年金1_LK')
       AND name = N'IX_年金1_LK_更新区分'
)
BEGIN
    CREATE INDEX [IX_年金1_LK_更新区分]
        ON dbo.[年金1_LK] ([変更FLG], [データ更新日], [更新者]);
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
     WHERE object_id = OBJECT_ID(N'dbo.年金＿削除明細')
       AND name = N'IX_年金削除明細_更新日'
)
BEGIN
    CREATE INDEX [IX_年金削除明細_更新日]
        ON dbo.[年金＿削除明細] ([データ更新日], [更新者]);
END;
GO
