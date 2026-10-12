# DB操作仕様書

## 概要

SQL原本を対象として、参照・挿入・更新・削除とパラメーター・対象条件・確定取消を記載する。

| 操作ID | 処理 | 対象テーブル | 原本 |
| --- | --- | --- | --- |
| SQL-55B58633E466 | 挿入 | DB2.Ｕカウンターシフト | n2framework/WEB-INF/src/common/base/InsertCounterShiftBase.java |
| SQL-F393DA844BF7 | 参照 | DB2.ＵＷＥＢログイン情報表 | n2framework/WEB-INF/src/common/base/SearchLoginInfoBase.java |
| SQL-418D30BDB59A | 参照 | DB2.ＵＷＥＢログイン情報表 | n2framework/WEB-INF/src/common/base/SearchLoginInfoBase.java |
| SQL-691F64E50533 | 参照 | DB2.Ｕ職員名簿表 | n2framework/WEB-INF/src/common/base/SearchLoginInfoBase.java |
| SQL-8B483872EF3B | 参照 | DB2.Ｕ職員所属課係一覧表 | n2framework/WEB-INF/src/common/base/SearchLoginInfoBase.java |
| SQL-01B370EBE516 | 参照 | DB2.ＵＪＶ役職コード表 | n2framework/WEB-INF/src/common/base/SearchLoginInfoBase.java |
| SQL-33C804326C53 | 参照 | DB2.ＵＪ業種 | n2framework/WEB-INF/src/common/base/SelectCodeGyosyuBase.java |
| SQL-91261B9FE7E9 | 参照 | DB2.ＵＤＢ管理ＤＢ | n2framework/WEB-INF/src/common/base/SelectDBKanriDBBase.java |
| SQL-527AB7402065 | 参照 | DB2.Ｕ代行可能職員名簿表 | n2framework/WEB-INF/src/common/base/SelectDaikoSyokuinBase.java |
| SQL-ADBA2FF6D73F | 参照 | N2_DWH.Ｊ事業所コード表２ | n2framework/WEB-INF/src/common/base/SelectJigyosyoCodeHyo2Base.java |
| SQL-D79B5FD619BA | 参照 | DB2.Ｕ祭日 | n2framework/WEB-INF/src/common/base/SelectSaijitsuBase.java |
| SQL-8BDBD39B9963 | 参照 | DB2.ＵＪ店舗管理台帳 | n2framework/WEB-INF/src/common/base/SelectTenpoKanriDaichoBase.java |
| SQL-56387246D482 | 参照 | DB2.ＵＤＢ管理ＤＢ | n2framework/WEB-INF/src/jhkcommon/OjiServlet.java |
| SQL-B07128F6323E | 挿入 | NAVI.ＵＳパス管理ステータス | n2framework/WEB-INF/src/webon/base/InsertPathMngStatBase.java |
| SQL-E77CBB76DE57 | 参照 | DB2.ＵＪ科目 | n2framework/WEB-INF/src/webon/base/SelectDB2KamokuBase.java |
| SQL-FE9A02F1592C | 参照 | DB2.ＵＪ科目 | n2framework/WEB-INF/src/webon/base/SelectDB2KamokuBase.java |
| SQL-D1BA242EB73F | 参照 | NAVI.ＵＭ機能マスタ | n2framework/WEB-INF/src/webon/base/SelectFunctionMasterBase.java |
| SQL-BF61EBA506D0 | 参照 | NAVI.ＵＪ機能マスタ | n2framework/WEB-INF/src/webon/base/SelectFunctionMasterBase.java |
| SQL-0DCAE7BAC6A9 | 参照 | NAVI.ＵＭオンラインＯＰマスタ | n2framework/WEB-INF/src/webon/base/SelectOnlineOperationMastBase.java |
| SQL-694864CAA608 | 参照 | NAVI.ＵＪ稼動店舗管理マスタ | n2framework/WEB-INF/src/webon/base/SelectOperationBranchMstBase.java |
| SQL-9782CA7464D4 | 参照 | NAVI.ＵＪ稼動店舗管理マスタ | n2framework/WEB-INF/src/webon/base/SelectOperationBranchMstBase.java |
| SQL-35487658430A | 参照 | NAVI.ＵＪ稼動店舗管理マスタ | n2framework/WEB-INF/src/webon/base/SelectOperationBranchMstBase.java |
| SQL-E2FA10A154DE | 参照 | NAVI.ＵＭパス管理マスタ | n2framework/WEB-INF/src/webon/base/SelectPathMngMstBase.java |
| SQL-519634C3F762 | 参照 | NAVI.ＵＳパス管理ステータス | n2framework/WEB-INF/src/webon/base/SelectPathMngStatBase.java |
| SQL-D94B94F30EBB | 参照 | NAVI.ＵＳパス管理ステータス | n2framework/WEB-INF/src/webon/base/SelectPathMngStatBase.java |
| SQL-F97C0AE27E69 | 更新 | NAVI.ＵＳパス管理ステータス | n2framework/WEB-INF/src/webon/base/UpdatePathMngStatBase.java |
| SQL-8DA5C44CC841 | 更新 | NAVI.ＵＳパス管理ステータス | n2framework/WEB-INF/src/webon/base/UpdatePathMngStatBase.java |
| SQL-26B9F21A0A7B | 参照 | N2_SIGHT.Ｂ顧客基本表 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-BE29DD398BAD | 参照 | 年金1_LK | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-98675681E706 | 参照 | 店名テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-935A991E07F4 | 参照 | 性別テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-A0A469ECF2C0 | 参照 | 裁定請求テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-F2C97CD89E50 | 参照 | 受給有無テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-CD804AC01D11 | 参照 | 年金種類テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-1CC29D9EDFFF | 参照 | 年金1_LK | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-28470D010AFF | 参照 | 店名テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-0F5F7D3D4469 | 参照 | 性別テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-0E90141F3DE0 | 参照 | 裁定請求テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-6597FFB0C483 | 参照 | 受給有無テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-87035C2BB1E0 | 参照 | 年金種類テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-F9D3BB2927F4 | 削除 | 年金1_LK | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-749C63561641 | 参照 | 年金1_LK | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-0E9B648B03D3 | 参照 | 年金＿削除明細 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-4F7E42ED747E | 削除 | 年金＿削除明細 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-22BD3A50DAE5 | 参照 | 店名テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-F5C825F11352 | 参照 | 年金種類テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-19BE5BBBA554 | 参照 | 年金1_LK | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-EC6FD30BE7CE | 参照 | 年金1_LK | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-B8CFB512D81A | 参照 | 店名テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-B3BD08EC9265 | 参照 | 性別テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-47BAF2E0D129 | 参照 | 裁定請求テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-C66BA4DBA955 | 参照 | 受給有無テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-E2E89DE2FC84 | 参照 | 年金種類テーブル | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-1A463E2BC06C | 挿入 | 年金1_LK | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-CD4068C5AE3B | 更新 | 年金1_LK | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-D7ADE1A915C2 | 挿入 | 年金＿削除明細 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java |
| SQL-2CF7CA976867 | 参照 | 店名テーブル | nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java |
| SQL-D9F3500B923D | 参照 | DB2.Ｕ職員名簿表 | nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java |
| SQL-E0FD738666D8 | 参照 | 店名テーブル | nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java |
| SQL-A8F5412DEF20 | 挿入・更新（MERGE） | DB2.ＵＷＥＢログイン情報表 | nenkin/WEB-INF/resources/db/data.sql |
| SQL-5C89ADEB93BB | 挿入・更新（MERGE） | DB2.Ｕ職員名簿表 | nenkin/WEB-INF/resources/db/data.sql |
| SQL-04E9DB7527CB | 挿入・更新（MERGE） | DB2.ＵＪＶ役職コード表 | nenkin/WEB-INF/resources/db/data.sql |
| SQL-304A64D29ABA | 挿入・更新（MERGE） | N2_DWH.Ｊ事業所コード表２ | nenkin/WEB-INF/resources/db/data.sql |
| SQL-CB7B3D708782 | 挿入・更新（MERGE） | DB2.ＵＤＢ管理ＤＢ | nenkin/WEB-INF/resources/db/data.sql |
| SQL-6B0A53508CEA | 挿入・更新（MERGE） | N2_SIGHT.Ｂ顧客基本表 | nenkin/WEB-INF/resources/db/data.sql |
| SQL-AB72701F29DC | 挿入・更新（MERGE） | 性別テーブル | nenkin/WEB-INF/resources/db/data.sql |
| SQL-974CC766238C | 挿入・更新（MERGE） | 裁定請求テーブル | nenkin/WEB-INF/resources/db/data.sql |
| SQL-FDB588A8849B | 挿入・更新（MERGE） | 受給有無テーブル | nenkin/WEB-INF/resources/db/data.sql |
| SQL-456572D1B62D | 挿入・更新（MERGE） | 店名テーブル | nenkin/WEB-INF/resources/db/data.sql |
| SQL-85DBC611F1E0 | 挿入・更新（MERGE） | 年金種類テーブル | nenkin/WEB-INF/resources/db/data.sql |
| SQL-0DE7BDCDCDFA | 挿入・更新（MERGE） | 年金1_LK | nenkin/WEB-INF/resources/db/data.sql |
| SQL-3E11A4E77CE8 | 挿入・更新（MERGE） | 年金＿削除明細 | nenkin/WEB-INF/resources/db/data.sql |


## 操作詳細

#### DB操作 SQL-55B58633E466

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-55B58633E466 |
| 対象テーブル | DB2.Ｕカウンターシフト |
| 操作 | 挿入 |
| 処理説明 | 原本のinsertで「DB2.Ｕカウンターシフト」を挿入する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | アクセス日付 ← 〈gSDFDate.format(date)〉／アクセス時刻 ← 〈gSDFTime.format(date)〉／機能ＩＤ ← 〈map.get(機能ＩＤ)：空値・NULLの条件付き設定〉／画面ＩＤ ← 〈map.get(画面ＩＤ)：空値・NULLの条件付き設定〉／コマンドＩＤ ← 〈map.get(コマンドＩＤ)：空値・NULLの条件付き設定〉／アクションＩＤ ← 〈map.get(アクションＩＤ)：空値・NULLの条件付き設定〉／ＪＳＰ名 ← 〈map.get(ＪＳＰ名)：空値・NULLの条件付き設定〉／ユーザーＩＤ ← '〈map.get("ユーザーＩＤ")〉' |
| 対象条件 | 新しい行を挿入する。重複や採番の扱いは呼出元および列制約に従う。 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/common/base/InsertCounterShiftBase.java:34 / insert@34 |

SQLの組立規則：insert into DB2.Ｕカウンターシフト (アクセス日付,アクセス時刻,機能ＩＤ,画面ＩＤ,コマンドＩＤ,アクションＩＤ,ＪＳＰ名,ユーザーＩＤ)  values (〈gSDFDate.format(date)〉,〈gSDFTime.format(date)〉,〈map.get(機能ＩＤ)：空値・NULLの条件付き設定〉,〈map.get(画面ＩＤ)：空値・NULLの条件付き設定〉,〈map.get(コマンドＩＤ)：空値・NULLの条件付き設定〉,〈map.get(アクションＩＤ)：空値・NULLの条件付き設定〉,〈map.get(ＪＳＰ名)：空値・NULLの条件付き設定〉,'〈map.get("ユーザーＩＤ")〉')

#### DB操作 SQL-F393DA844BF7

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-F393DA844BF7 |
| 対象テーブル | DB2.ＵＷＥＢログイン情報表 |
| 操作 | 参照 |
| 処理説明 | 原本のselectＷＥＢログイン情報表で「DB2.ＵＷＥＢログイン情報表」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：アプリケーション名 = '〈applName〉' and ユーザーＩＤ = '〈userId〉' and パスワード = '〈password〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/common/base/SearchLoginInfoBase.java:40 / selectＷＥＢログイン情報表@40 |

SQLの組立規則：select * from DB2.ＵＷＥＢログイン情報表 where アプリケーション名 = '〈applName〉' and ユーザーＩＤ = '〈userId〉' and パスワード = '〈password〉'

#### DB操作 SQL-418D30BDB59A

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-418D30BDB59A |
| 対象テーブル | DB2.ＵＷＥＢログイン情報表 |
| 操作 | 参照 |
| 処理説明 | 原本のselectＷＥＢログイン情報表で「DB2.ＵＷＥＢログイン情報表」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：アプリケーション名 = '〈applName〉' and ユーザーＩＤ = '〈userId〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/common/base/SearchLoginInfoBase.java:75 / selectＷＥＢログイン情報表@75 |

SQLの組立規則：select * from DB2.ＵＷＥＢログイン情報表 where アプリケーション名 = '〈applName〉' and ユーザーＩＤ = '〈userId〉'

#### DB操作 SQL-691F64E50533

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-691F64E50533 |
| 対象テーブル | DB2.Ｕ職員名簿表 |
| 操作 | 参照 |
| 処理説明 | 原本のselect職員名簿表で「DB2.Ｕ職員名簿表」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：職員番号 = 〈shokuinNo〉 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/common/base/SearchLoginInfoBase.java:107 / select職員名簿表@107 |

SQLの組立規則：select * from DB2.Ｕ職員名簿表 where 職員番号 = 〈shokuinNo〉

#### DB操作 SQL-8B483872EF3B

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-8B483872EF3B |
| 対象テーブル | DB2.Ｕ職員所属課係一覧表 |
| 操作 | 参照 |
| 処理説明 | 原本のselect職員所属課係一覧表で「DB2.Ｕ職員所属課係一覧表」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：職員番号 = 〈shokuinNo〉 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/common/base/SearchLoginInfoBase.java:137 / select職員所属課係一覧表@137 |

SQLの組立規則：select * from DB2.Ｕ職員所属課係一覧表 where 職員番号 = 〈shokuinNo〉

#### DB操作 SQL-01B370EBE516

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-01B370EBE516 |
| 対象テーブル | DB2.ＵＪＶ役職コード表 |
| 操作 | 参照 |
| 処理説明 | 原本のselect役職コード表で「DB2.ＵＪＶ役職コード表」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：役職コード = 〈yakusyokucode〉 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/common/base/SearchLoginInfoBase.java:167 / select役職コード表@167 |

SQLの組立規則：SELECT 役職 FROM DB2.ＵＪＶ役職コード表 WHERE 役職コード = 〈yakusyokucode〉

#### DB操作 SQL-33C804326C53

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-33C804326C53 |
| 対象テーブル | DB2.ＵＪ業種 |
| 操作 | 参照 |
| 処理説明 | 原本のselectで「DB2.ＵＪ業種」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | WHERE句による限定はこのSQL式にない。呼出条件・動的付加条件は原本を参照する。 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/common/base/SelectCodeGyosyuBase.java:40 / select@35 |

SQLの組立規則：SELECT コード,項目１ FROM DB2.ＵＪ業種 ORDER BY コード

#### DB操作 SQL-91261B9FE7E9

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-91261B9FE7E9 |
| 対象テーブル | DB2.ＵＤＢ管理ＤＢ |
| 操作 | 参照 |
| 処理説明 | 原本のselectで「DB2.ＵＤＢ管理ＤＢ」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：ＤＢ名 = '〈dbName〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/common/base/SelectDBKanriDBBase.java:39 / select@39 |

SQLの組立規則：select 処理中ＦＬＧ from DB2.ＵＤＢ管理ＤＢ where ＤＢ名 = '〈dbName〉'

#### DB操作 SQL-527AB7402065

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-527AB7402065 |
| 対象テーブル | DB2.Ｕ代行可能職員名簿表 |
| 操作 | 参照 |
| 処理説明 | 原本のselectCredit代行で「DB2.Ｕ代行可能職員名簿表」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：職員番号 = 〈shokuinNo〉 and credit権限 = 1 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/common/base/SelectDaikoSyokuinBase.java:40 / selectCredit代行@40 |

SQLの組立規則：select * from DB2.Ｕ代行可能職員名簿表 where 職員番号 = 〈shokuinNo〉 and credit権限 = 1

#### DB操作 SQL-ADBA2FF6D73F

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-ADBA2FF6D73F |
| 対象テーブル | N2_DWH.Ｊ事業所コード表２ |
| 操作 | 参照 |
| 処理説明 | 原本のselectで「N2_DWH.Ｊ事業所コード表２」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：店舗コード = 〈code〉 and 枝番 = 〈edaban〉 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/common/base/SelectJigyosyoCodeHyo2Base.java:39 / select@39 |

SQLの組立規則：select 事業所名 from N2_DWH.Ｊ事業所コード表２ where 店舗コード = 〈code〉 and 枝番 = 〈edaban〉

#### DB操作 SQL-D79B5FD619BA

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-D79B5FD619BA |
| 対象テーブル | DB2.Ｕ祭日 |
| 操作 | 参照 |
| 処理説明 | 原本のselectで「DB2.Ｕ祭日」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | WHERE句による限定はこのSQL式にない。呼出条件・動的付加条件は原本を参照する。 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/common/base/SelectSaijitsuBase.java:33 / select@33 |

SQLの組立規則：select 日付 from DB2.Ｕ祭日 order by 日付 

#### DB操作 SQL-8BDBD39B9963

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-8BDBD39B9963 |
| 対象テーブル | DB2.ＵＪ店舗管理台帳 |
| 操作 | 参照 |
| 処理説明 | 原本のselectTenpoIchiranで「DB2.ＵＪ店舗管理台帳」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：副店番 = 0 AND 状態 = 0 AND 店番 &gt; 10 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/common/base/SelectTenpoKanriDaichoBase.java:39 / selectTenpoIchiran@39 |

SQLの組立規則：SELECT 店番, TRIM('　' from 漢字店名) AS 漢字店名 FROM DB2.ＵＪ店舗管理台帳 WHERE 副店番 = 0 AND 状態 = 0 AND 店番 &gt; 10 ORDER BY 店番

#### DB操作 SQL-56387246D482

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-56387246D482 |
| 対象テーブル | DB2.ＵＤＢ管理ＤＢ |
| 操作 | 参照 |
| 処理説明 | 原本のcheckで「DB2.ＵＤＢ管理ＤＢ」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：ＤＢ名 = 'Ｕ調査カード' |
| 確定・取消 | 当該メソッド内で自動コミット設定を行う。例外時の処理順は詳細仕様の分岐に従う。 |
| 原本 | n2framework/WEB-INF/src/jhkcommon/OjiServlet.java:244 / check@244 |

SQLの組立規則：select 処理中ＦＬＧ from DB2.ＵＤＢ管理ＤＢ where ＤＢ名 = 'Ｕ調査カード'

#### DB操作 SQL-B07128F6323E

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-B07128F6323E |
| 対象テーブル | NAVI.ＵＳパス管理ステータス |
| 操作 | 挿入 |
| 処理説明 | 原本のinsertPathNoで「NAVI.ＵＳパス管理ステータス」を挿入する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 接続先 ← 〈ConvertUtil.dbMoldStr(ip, 15)〉／パス使用数 ← 〈ConvertUtil.dbMoldInt(DBVAL_INITPATHNUM, 3)〉／制限パス使用数 ← 〈ConvertUtil.dbMoldInt(DBVAL_INITPATHNUMLIM, 3)〉／作成日 ← 〈ConvertUtil.dbGetDate()〉／作成時刻 ← 〈ConvertUtil.dbGetTime()〉／更新日 ← 〈ConvertUtil.dbGetDate()〉／更新時刻 ← 〈ConvertUtil.dbGetTime()〉 |
| 対象条件 | 新しい行を挿入する。重複や採番の扱いは呼出元および列制約に従う。 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/InsertPathMngStatBase.java:42 / insertPathNo@42 |

SQLの組立規則：INSERT INTO NAVI.ＵＳパス管理ステータス (接続先 ,パス使用数 ,制限パス使用数 ,作成日 ,作成時刻 ,更新日 ,更新時刻 ) VALUES(〈ConvertUtil.dbMoldStr(ip, 15)〉,〈ConvertUtil.dbMoldInt(DBVAL_INITPATHNUM, 3)〉,〈ConvertUtil.dbMoldInt(DBVAL_INITPATHNUMLIM, 3)〉,〈ConvertUtil.dbGetDate()〉,〈ConvertUtil.dbGetTime()〉,〈ConvertUtil.dbGetDate()〉,〈ConvertUtil.dbGetTime()〉)

#### DB操作 SQL-E77CBB76DE57

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-E77CBB76DE57 |
| 対象テーブル | DB2.ＵＪ科目 |
| 操作 | 参照 |
| 処理説明 | 原本のselectKamokuNameByCodeで「DB2.ＵＪ科目」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：コード=〈ConvertUtil.dbMoldStr(code,2)〉 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectDB2KamokuBase.java:37 / selectKamokuNameByCode@37 |

SQLの組立規則：SELECT * FROM DB2.ＵＪ科目 WHERE コード=〈ConvertUtil.dbMoldStr(code,2)〉

#### DB操作 SQL-FE9A02F1592C

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-FE9A02F1592C |
| 対象テーブル | DB2.ＵＪ科目 |
| 操作 | 参照 |
| 処理説明 | 原本のselectCodeByKamokuNameで「DB2.ＵＪ科目」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：項目１='〈name〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectDB2KamokuBase.java:65 / selectCodeByKamokuName@65 |

SQLの組立規則：SELECT * FROM DB2.ＵＪ科目 WHERE 項目１='〈name〉'

#### DB操作 SQL-D1BA242EB73F

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-D1BA242EB73F |
| 対象テーブル | NAVI.ＵＭ機能マスタ |
| 操作 | 参照 |
| 処理説明 | 原本のselectValueByFunctionIdAndKeyで「NAVI.ＵＭ機能マスタ」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：機能名='〈functionId〉'and キー名='〈key〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectFunctionMasterBase.java:39 / selectValueByFunctionIdAndKey@39 |

SQLの組立規則：select 値 from NAVI.ＵＭ機能マスタ where 機能名='〈functionId〉'and キー名='〈key〉'

#### DB操作 SQL-BF61EBA506D0

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-BF61EBA506D0 |
| 対象テーブル | NAVI.ＵＪ機能マスタ |
| 操作 | 参照 |
| 処理説明 | 原本のselectByFunctionIdで「NAVI.ＵＪ機能マスタ」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：機能名='〈functionId〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectFunctionMasterBase.java:60 / selectByFunctionId@60 |

SQLの組立規則：select * from NAVI.ＵＪ機能マスタ where 機能名='〈functionId〉'

#### DB操作 SQL-0DCAE7BAC6A9

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-0DCAE7BAC6A9 |
| 対象テーブル | NAVI.ＵＭオンラインＯＰマスタ |
| 操作 | 参照 |
| 処理説明 | 原本のselectByOperationIdで「NAVI.ＵＭオンラインＯＰマスタ」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：オペレーションＩＤ='〈operationId〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectOnlineOperationMastBase.java:41 / selectByOperationId@41 |

SQLの組立規則：SELECT * FROM NAVI.ＵＭオンラインＯＰマスタ WHERE オペレーションＩＤ='〈operationId〉'

#### DB操作 SQL-694864CAA608

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-694864CAA608 |
| 対象テーブル | NAVI.ＵＪ稼動店舗管理マスタ |
| 操作 | 参照 |
| 処理説明 | 原本のselectOperationBranchNoで「NAVI.ＵＪ稼動店舗管理マスタ」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | WHERE句による限定はこのSQL式にない。呼出条件・動的付加条件は原本を参照する。 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectOperationBranchMstBase.java:41 / selectOperationBranchNo@41 |

SQLの組立規則：SELECT * FROM NAVI.ＵＪ稼動店舗管理マスタ ORDER BY 店番

#### DB操作 SQL-9782CA7464D4

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-9782CA7464D4 |
| 対象テーブル | NAVI.ＵＪ稼動店舗管理マスタ |
| 操作 | 参照 |
| 処理説明 | 原本のselectByBrnoで「NAVI.ＵＪ稼動店舗管理マスタ」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：店番=〈brno〉 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectOperationBranchMstBase.java:69 / selectByBrno@69 |

SQLの組立規則：SELECT  店番,取引店舗コード,接続先,取引可能フラグ FROM NAVI.ＵＪ稼動店舗管理マスタ WHERE 店番=〈brno〉

#### DB操作 SQL-35487658430A

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-35487658430A |
| 対象テーブル | NAVI.ＵＪ稼動店舗管理マスタ |
| 操作 | 参照 |
| 処理説明 | 原本のselectNotActiveByBrnoで「NAVI.ＵＪ稼動店舗管理マスタ」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：店番=〈brno〉 AND 取引可能フラグ='1' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectOperationBranchMstBase.java:100 / selectNotActiveByBrno@100 |

SQLの組立規則：SELECT  店番,取引店舗コード,接続先,取引可能フラグ FROM NAVI.ＵＪ稼動店舗管理マスタ WHERE 店番=〈brno〉 AND 取引可能フラグ='1'

#### DB操作 SQL-E2FA10A154DE

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-E2FA10A154DE |
| 対象テーブル | NAVI.ＵＭパス管理マスタ |
| 操作 | 参照 |
| 処理説明 | 原本のselectPathMaxで「NAVI.ＵＭパス管理マスタ」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：接続先='〈ip〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectPathMngMstBase.java:35 / selectPathMax@35 |

SQLの組立規則：SELECT * FROM NAVI.ＵＭパス管理マスタ WHERE 接続先='〈ip〉'

#### DB操作 SQL-519634C3F762

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-519634C3F762 |
| 対象テーブル | NAVI.ＵＳパス管理ステータス |
| 操作 | 参照 |
| 処理説明 | 原本のselectPathNoForUpで「NAVI.ＵＳパス管理ステータス」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：接続先='〈ip〉' FOR UPDATE WAIT 10 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectPathMngStatBase.java:39 / selectPathNoForUp@39 |

SQLの組立規則：SELECT パス使用数,制限パス使用数 FROM NAVI.ＵＳパス管理ステータス WHERE 接続先='〈ip〉' FOR UPDATE WAIT 10

#### DB操作 SQL-D94B94F30EBB

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-D94B94F30EBB |
| 対象テーブル | NAVI.ＵＳパス管理ステータス |
| 操作 | 参照 |
| 処理説明 | 原本のcheckPathNoで「NAVI.ＵＳパス管理ステータス」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：接続先='〈ip〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/SelectPathMngStatBase.java:69 / checkPathNo@69 |

SQLの組立規則：SELECT パス使用数,制限パス使用数 FROM NAVI.ＵＳパス管理ステータス WHERE 接続先='〈ip〉'

#### DB操作 SQL-F97C0AE27E69

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-F97C0AE27E69 |
| 対象テーブル | NAVI.ＵＳパス管理ステータス |
| 操作 | 更新 |
| 処理説明 | 原本のupdatePathNoで「NAVI.ＵＳパス管理ステータス」を更新する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | パス使用数 ← 〈pathNum〉／更新日 ← 〈ConvertUtil.dbGetDate()〉／更新時刻 ← 〈ConvertUtil.dbGetTime()〉 |
| 対象条件 | 抽出・更新対象条件：接続先='〈ip〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/UpdatePathMngStatBase.java:41 / updatePathNo@41 |

SQLの組立規則：UPDATE NAVI.ＵＳパス管理ステータス SET パス使用数=〈pathNum〉,更新日=〈ConvertUtil.dbGetDate()〉,更新時刻=〈ConvertUtil.dbGetTime()〉 WHERE 接続先='〈ip〉'

#### DB操作 SQL-8DA5C44CC841

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-8DA5C44CC841 |
| 対象テーブル | NAVI.ＵＳパス管理ステータス |
| 操作 | 更新 |
| 処理説明 | 原本のupdatePathNoで「NAVI.ＵＳパス管理ステータス」を更新する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | パス使用数 ← 〈pathNum〉／制限パス使用数 ← 〈pathNumLim〉／更新日 ← 〈ConvertUtil.dbGetDate()〉／更新時刻 ← 〈ConvertUtil.dbGetTime()〉 |
| 対象条件 | 抽出・更新対象条件：接続先='〈ip〉' |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | n2framework/WEB-INF/src/webon/base/UpdatePathMngStatBase.java:70 / updatePathNo@70 |

SQLの組立規則：UPDATE NAVI.ＵＳパス管理ステータス SET パス使用数=〈pathNum〉,制限パス使用数=〈pathNumLim〉,更新日=〈ConvertUtil.dbGetDate()〉,更新時刻=〈ConvertUtil.dbGetTime()〉 WHERE 接続先='〈ip〉'

#### DB操作 SQL-26B9F21A0A7B

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-26B9F21A0A7B |
| 対象テーブル | N2_SIGHT.Ｂ顧客基本表 |
| 操作 | 参照 |
| 処理説明 | 原本のfindByCustomerで「N2_SIGHT.Ｂ顧客基本表」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：C.店舗コード = ? AND C.顧客番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:88 / findByCustomer@87 |

SQLの組立規則：SELECT C.店舗コード AS BRANCH_NO, C.顧客番号 AS CUSTOMER_NO, C.担当者コード AS STAFF_CODE, C.漢字氏名 AS CUSTOMER_NAME, C.カナ氏名 AS KANA_NAME, C.性別コード AS GENDER_CODE, C.漢字住所 AS ADDRESS, C.電話番号 AS PHONE_NUMBER, C.生年月日 AS BIRTH_DATE FROM N2_SIGHT.Ｂ顧客基本表 C WHERE C.店舗コード = ? AND C.顧客番号 = ?

#### DB操作 SQL-BE29DD398BAD

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-BE29DD398BAD |
| 対象テーブル | 年金1_LK |
| 操作 | 参照 |
| 処理説明 | 原本のfindByKanaAndPhoneで「年金1_LK」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.ふりがな = ? AND R.電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:150 / findByKanaAndPhone@144 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.ふりがな = ? AND R.電話番号 = ?

#### DB操作 SQL-98675681E706

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-98675681E706 |
| 対象テーブル | 店名テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のfindByKanaAndPhoneで「店名テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.ふりがな = ? AND R.電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:150 / findByKanaAndPhone@144 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.ふりがな = ? AND R.電話番号 = ?

#### DB操作 SQL-935A991E07F4

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-935A991E07F4 |
| 対象テーブル | 性別テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のfindByKanaAndPhoneで「性別テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.ふりがな = ? AND R.電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:150 / findByKanaAndPhone@144 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.ふりがな = ? AND R.電話番号 = ?

#### DB操作 SQL-A0A469ECF2C0

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-A0A469ECF2C0 |
| 対象テーブル | 裁定請求テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のfindByKanaAndPhoneで「裁定請求テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.ふりがな = ? AND R.電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:150 / findByKanaAndPhone@144 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.ふりがな = ? AND R.電話番号 = ?

#### DB操作 SQL-F2C97CD89E50

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-F2C97CD89E50 |
| 対象テーブル | 受給有無テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のfindByKanaAndPhoneで「受給有無テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.ふりがな = ? AND R.電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:150 / findByKanaAndPhone@144 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.ふりがな = ? AND R.電話番号 = ?

#### DB操作 SQL-CD804AC01D11

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-CD804AC01D11 |
| 対象テーブル | 年金種類テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のfindByKanaAndPhoneで「年金種類テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.ふりがな = ? AND R.電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:150 / findByKanaAndPhone@144 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.ふりがな = ? AND R.電話番号 = ?

#### DB操作 SQL-1CC29D9EDFFF

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-1CC29D9EDFFF |
| 対象テーブル | 年金1_LK |
| 操作 | 参照 |
| 処理説明 | 原本のlistByBranchで「年金1_LK」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.店番 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:224 / listByBranch@223 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.店番 = ? ORDER BY R.請求予定日 DESC, R.担当者コード, R.顧客番号

#### DB操作 SQL-28470D010AFF

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-28470D010AFF |
| 対象テーブル | 店名テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のlistByBranchで「店名テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.店番 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:224 / listByBranch@223 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.店番 = ? ORDER BY R.請求予定日 DESC, R.担当者コード, R.顧客番号

#### DB操作 SQL-0F5F7D3D4469

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-0F5F7D3D4469 |
| 対象テーブル | 性別テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のlistByBranchで「性別テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.店番 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:224 / listByBranch@223 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.店番 = ? ORDER BY R.請求予定日 DESC, R.担当者コード, R.顧客番号

#### DB操作 SQL-0E90141F3DE0

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-0E90141F3DE0 |
| 対象テーブル | 裁定請求テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のlistByBranchで「裁定請求テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.店番 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:224 / listByBranch@223 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.店番 = ? ORDER BY R.請求予定日 DESC, R.担当者コード, R.顧客番号

#### DB操作 SQL-6597FFB0C483

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-6597FFB0C483 |
| 対象テーブル | 受給有無テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のlistByBranchで「受給有無テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.店番 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:224 / listByBranch@223 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.店番 = ? ORDER BY R.請求予定日 DESC, R.担当者コード, R.顧客番号

#### DB操作 SQL-87035C2BB1E0

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-87035C2BB1E0 |
| 対象テーブル | 年金種類テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のlistByBranchで「年金種類テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.店番 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:224 / listByBranch@223 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.店番 = ? ORDER BY R.請求予定日 DESC, R.担当者コード, R.顧客番号

#### DB操作 SQL-F9D3BB2927F4

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-F9D3BB2927F4 |
| 対象テーブル | 年金1_LK |
| 操作 | 削除 |
| 処理説明 | 原本のdeleteで「年金1_LK」を削除する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：ふりがな = ? AND 電話番号 = ? |
| 確定・取消 | 当該メソッド内で自動コミット設定・コミット・ロールバックを行う。例外時の処理順は詳細仕様の分岐に従う。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:334 / delete@315 |

SQLの組立規則：DELETE FROM 年金1_LK WHERE ふりがな = ? AND 電話番号 = ?

#### DB操作 SQL-749C63561641

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-749C63561641 |
| 対象テーブル | 年金1_LK |
| 操作 | 参照 |
| 処理説明 | 原本のfindLatestAuditTypeで「年金1_LK」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：ふりがな = ? AND 電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:427 / findLatestAuditType@416 |

SQLの組立規則：SELECT 変更FLG FROM 年金1_LK WHERE ふりがな = ? AND 電話番号 = ?

#### DB操作 SQL-0E9B648B03D3

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-0E9B648B03D3 |
| 対象テーブル | 年金＿削除明細 |
| 操作 | 参照 |
| 処理説明 | 原本のfindLatestAuditTypeで「年金＿削除明細」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：ふりがな = ? AND 電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:440 / findLatestAuditType@416 |

SQLの組立規則：SELECT 1 FROM 年金＿削除明細 WHERE ふりがな = ? AND 電話番号 = ? ORDER BY データ更新日 DESC, 更新時間 DESC

#### DB操作 SQL-4F7E42ED747E

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-4F7E42ED747E |
| 対象テーブル | 年金＿削除明細 |
| 操作 | 削除 |
| 処理説明 | 原本のpurgeDeletedAuditsThroughで「年金＿削除明細」を削除する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：データ更新日 &lt;= ? |
| 確定・取消 | 当該メソッド内で自動コミット設定・コミットを行う。例外時の処理順は詳細仕様の分岐に従う。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:468 / purgeDeletedAuditsThrough@458 |

SQLの組立規則：DELETE FROM 年金＿削除明細 WHERE データ更新日 &lt;= ?

#### DB操作 SQL-22BD3A50DAE5

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-22BD3A50DAE5 |
| 対象テーブル | 店名テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のresolveBranchNameで「店名テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：店舗ｺｰﾄﾞ = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:543 / resolveBranchName@535 |

SQLの組立規則：SELECT 店名 FROM 店名テーブル WHERE 店舗ｺｰﾄﾞ = ?

#### DB操作 SQL-F5C825F11352

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-F5C825F11352 |
| 対象テーブル | 年金種類テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のresolvePensionTypeCodeで「年金種類テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：種類ｺｰﾄﾞ = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:609 / resolvePensionTypeCode@596 |

SQLの組立規則：SELECT 年金種類 FROM 年金種類テーブル WHERE 種類ｺｰﾄﾞ = ?

#### DB操作 SQL-19BE5BBBA554

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-19BE5BBBA554 |
| 対象テーブル | 年金1_LK |
| 操作 | 参照 |
| 処理説明 | 原本のexistsで「年金1_LK」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：ふりがな = ? AND 電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:628 / exists@623 |

SQLの組立規則：SELECT 1 FROM 年金1_LK WHERE ふりがな = ? AND 電話番号 = ?

#### DB操作 SQL-EC6FD30BE7CE

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-EC6FD30BE7CE |
| 対象テーブル | 年金1_LK |
| 操作 | 参照 |
| 処理説明 | 原本のfindByKeyで「年金1_LK」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.ふりがな = ? AND R.電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:645 / findByKey@640 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.ふりがな = ? AND R.電話番号 = ?

#### DB操作 SQL-B8CFB512D81A

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-B8CFB512D81A |
| 対象テーブル | 店名テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のfindByKeyで「店名テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.ふりがな = ? AND R.電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:645 / findByKey@640 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.ふりがな = ? AND R.電話番号 = ?

#### DB操作 SQL-B3BD08EC9265

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-B3BD08EC9265 |
| 対象テーブル | 性別テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のfindByKeyで「性別テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.ふりがな = ? AND R.電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:645 / findByKey@640 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.ふりがな = ? AND R.電話番号 = ?

#### DB操作 SQL-47BAF2E0D129

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-47BAF2E0D129 |
| 対象テーブル | 裁定請求テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のfindByKeyで「裁定請求テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.ふりがな = ? AND R.電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:645 / findByKey@640 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.ふりがな = ? AND R.電話番号 = ?

#### DB操作 SQL-C66BA4DBA955

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-C66BA4DBA955 |
| 対象テーブル | 受給有無テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のfindByKeyで「受給有無テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.ふりがな = ? AND R.電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:645 / findByKey@640 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.ふりがな = ? AND R.電話番号 = ?

#### DB操作 SQL-E2E89DE2FC84

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-E2E89DE2FC84 |
| 対象テーブル | 年金種類テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のfindByKeyで「年金種類テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：R.ふりがな = ? AND R.電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:645 / findByKey@640 |

SQLの組立規則：SELECT R.店番 AS BRANCH_NO, B.店名 AS BRANCH_NAME, R.顧客番号 AS CUSTOMER_NO, R.担当者コード AS STAFF_CODE, R.顧客氏名 AS CUSTOMER_NAME, R.ふりがな AS KANA_NAME, G.性別 AS GENDER, R.住所 AS ADDRESS, R.電話番号 AS PHONE_NUMBER, R.生年月日 AS BIRTH_DATE, C.裁定請求 AS CLAIM_STATUS, R.請求予定日 AS CLAIM_SCHEDULED_DATE, R.予定年齢 AS PLANNED_AGE, R.予約徴求日 AS RESERVATION_REQUEST_DATE, R.データ更新日 AS DATA_UPDATE_DATE, R.備考 AS NOTES, R.配偶者名 AS SPOUSE_NAME, H.受給有無 AS HAS_BENEFIT, R.配偶者生年月日 AS SPOUSE_BIRTH_DATE, P.年金種類 AS PENSION_TYPE, R."種類：国民年金" AS NATIONAL_PENSION, R."種類：厚生年金" AS EMPLOYEE_PENSION, R."種類：共済年金" AS MUTUAL_AID_PENSION, R."種類：厚生年金基金" AS EMPLOYEE_PENSION_FUND, R."種類：国民年金基金" AS NATIONAL_PENSION_FUND, R."６ヶ月先確認" AS SIX_MONTH_CHECK FROM 年金1_LK R LEFT JOIN 店名テーブル B ON R.店番 = B.店舗ｺｰﾄﾞ LEFT JOIN 性別テーブル G ON R.性別 = G.性別ｺｰﾄﾞ LEFT JOIN 裁定請求テーブル C ON R.裁定請求 = C.裁請ｺｰﾄﾞ LEFT JOIN 受給有無テーブル H ON R.受給有無 = H.受給ｺｰﾄﾞ LEFT JOIN 年金種類テーブル P ON R.年金種類 = P.種類ｺｰﾄﾞ WHERE R.ふりがな = ? AND R.電話番号 = ?

#### DB操作 SQL-1A463E2BC06C

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-1A463E2BC06C |
| 対象テーブル | 年金1_LK |
| 操作 | 挿入 |
| 処理説明 | 原本のinsertで「年金1_LK」を挿入する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 店番 ← バインド引数1（PreparedStatementまたは呼出側の設定順序）／顧客番号 ← バインド引数2（PreparedStatementまたは呼出側の設定順序）／担当者コード ← バインド引数3（PreparedStatementまたは呼出側の設定順序）／顧客氏名 ← バインド引数4（PreparedStatementまたは呼出側の設定順序）／ふりがな ← バインド引数5（PreparedStatementまたは呼出側の設定順序）／性別 ← バインド引数6（PreparedStatementまたは呼出側の設定順序）／住所 ← バインド引数7（PreparedStatementまたは呼出側の設定順序）／電話番号 ← バインド引数8（PreparedStatementまたは呼出側の設定順序）／生年月日 ← バインド引数9（PreparedStatementまたは呼出側の設定順序）／種類：国民年金 ← バインド引数10（PreparedStatementまたは呼出側の設定順序）／種類：厚生年金 ← バインド引数11（PreparedStatementまたは呼出側の設定順序）／種類：共済年金 ← バインド引数12（PreparedStatementまたは呼出側の設定順序）／種類：厚生年金基金 ← バインド引数13（PreparedStatementまたは呼出側の設定順序）／種類：国民年金基金 ← バインド引数14（PreparedStatementまたは呼出側の設定順序）／年金種類 ← バインド引数15（PreparedStatementまたは呼出側の設定順序）／裁定請求 ← バインド引数16（PreparedStatementまたは呼出側の設定順序）／請求予定日 ← バインド引数17（PreparedStatementまたは呼出側の設定順序）／予定年齢 ← バインド引数18（PreparedStatementまたは呼出側の設定順序）／配偶者名 ← バインド引数19（PreparedStatementまたは呼出側の設定順序）／配偶者生年月日 ← バインド引数20（PreparedStatementまたは呼出側の設定順序）／受給有無 ← バインド引数21（PreparedStatementまたは呼出側の設定順序）／予約徴求日 ← バインド引数22（PreparedStatementまたは呼出側の設定順序）／備考 ← バインド引数23（PreparedStatementまたは呼出側の設定順序）／データ更新日 ← バインド引数24（PreparedStatementまたは呼出側の設定順序）／更新時間 ← バインド引数25（PreparedStatementまたは呼出側の設定順序）／更新者 ← バインド引数26（PreparedStatementまたは呼出側の設定順序）／６ヶ月先確認 ← バインド引数27（PreparedStatementまたは呼出側の設定順序）／変更FLG ← バインド引数28（PreparedStatementまたは呼出側の設定順序） |
| 対象条件 | 新しい行を挿入する。重複や採番の扱いは呼出元および列制約に従う。 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:661 / insert@657 |

SQLの組立規則：INSERT INTO 年金1_LK (店番, 顧客番号, 担当者コード, 顧客氏名, ふりがな, 性別, 住所, 電話番号, 生年月日, "種類：国民年金", "種類：厚生年金", "種類：共済年金", "種類：厚生年金基金", "種類：国民年金基金", 年金種類, 裁定請求, 請求予定日, 予定年齢, 配偶者名, 配偶者生年月日, 受給有無, 予約徴求日, 備考, データ更新日, 更新時間, 更新者, "６ヶ月先確認", 変更FLG) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

#### DB操作 SQL-CD4068C5AE3B

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-CD4068C5AE3B |
| 対象テーブル | 年金1_LK |
| 操作 | 更新 |
| 処理説明 | 原本のupdateで「年金1_LK」を更新する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 店番 ← バインド引数1（PreparedStatementまたは呼出側の設定順序）／顧客番号 ← バインド引数2（PreparedStatementまたは呼出側の設定順序）／担当者コード ← バインド引数3（PreparedStatementまたは呼出側の設定順序）／顧客氏名 ← バインド引数4（PreparedStatementまたは呼出側の設定順序）／ふりがな ← バインド引数5（PreparedStatementまたは呼出側の設定順序）／性別 ← バインド引数6（PreparedStatementまたは呼出側の設定順序）／住所 ← バインド引数7（PreparedStatementまたは呼出側の設定順序）／電話番号 ← バインド引数8（PreparedStatementまたは呼出側の設定順序）／生年月日 ← バインド引数9（PreparedStatementまたは呼出側の設定順序）／種類：国民年金 ← バインド引数10（PreparedStatementまたは呼出側の設定順序）／種類：厚生年金 ← バインド引数11（PreparedStatementまたは呼出側の設定順序）／種類：共済年金 ← バインド引数12（PreparedStatementまたは呼出側の設定順序）／種類：厚生年金基金 ← バインド引数13（PreparedStatementまたは呼出側の設定順序）／種類：国民年金基金 ← バインド引数14（PreparedStatementまたは呼出側の設定順序）／年金種類 ← バインド引数15（PreparedStatementまたは呼出側の設定順序）／裁定請求 ← バインド引数16（PreparedStatementまたは呼出側の設定順序）／請求予定日 ← バインド引数17（PreparedStatementまたは呼出側の設定順序）／予定年齢 ← バインド引数18（PreparedStatementまたは呼出側の設定順序）／配偶者名 ← バインド引数19（PreparedStatementまたは呼出側の設定順序）／配偶者生年月日 ← バインド引数20（PreparedStatementまたは呼出側の設定順序）／受給有無 ← バインド引数21（PreparedStatementまたは呼出側の設定順序）／予約徴求日 ← バインド引数22（PreparedStatementまたは呼出側の設定順序）／備考 ← バインド引数23（PreparedStatementまたは呼出側の設定順序）／データ更新日 ← バインド引数24（PreparedStatementまたは呼出側の設定順序）／更新時間 ← バインド引数25（PreparedStatementまたは呼出側の設定順序）／更新者 ← バインド引数26（PreparedStatementまたは呼出側の設定順序）／６ヶ月先確認 ← バインド引数27（PreparedStatementまたは呼出側の設定順序）／変更FLG ← バインド引数28（PreparedStatementまたは呼出側の設定順序） |
| 対象条件 | 抽出・更新対象条件：ふりがな = ? AND 電話番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:676 / update@672 |

SQLの組立規則：UPDATE 年金1_LK SET 店番 = ?, 顧客番号 = ?, 担当者コード = ?, 顧客氏名 = ?, ふりがな = ?, 性別 = ?, 住所 = ?, 電話番号 = ?, 生年月日 = ?, "種類：国民年金" = ?, "種類：厚生年金" = ?, "種類：共済年金" = ?, "種類：厚生年金基金" = ?, "種類：国民年金基金" = ?, 年金種類 = ?, 裁定請求 = ?, 請求予定日 = ?, 予定年齢 = ?, 配偶者名 = ?, 配偶者生年月日 = ?, 受給有無 = ?, 予約徴求日 = ?, 備考 = ?, データ更新日 = ?, 更新時間 = ?, 更新者 = ?, "６ヶ月先確認" = ?, 変更FLG = ? WHERE ふりがな = ? AND 電話番号 = ?

#### DB操作 SQL-D7ADE1A915C2

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-D7ADE1A915C2 |
| 対象テーブル | 年金＿削除明細 |
| 操作 | 挿入 |
| 処理説明 | 原本のinsertDeletedで「年金＿削除明細」を挿入する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 店番 ← バインド引数1（PreparedStatementまたは呼出側の設定順序）／顧客番号 ← バインド引数2（PreparedStatementまたは呼出側の設定順序）／担当者コード ← バインド引数3（PreparedStatementまたは呼出側の設定順序）／顧客氏名 ← バインド引数4（PreparedStatementまたは呼出側の設定順序）／ふりがな ← バインド引数5（PreparedStatementまたは呼出側の設定順序）／性別 ← バインド引数6（PreparedStatementまたは呼出側の設定順序）／住所 ← バインド引数7（PreparedStatementまたは呼出側の設定順序）／電話番号 ← バインド引数8（PreparedStatementまたは呼出側の設定順序）／生年月日 ← バインド引数9（PreparedStatementまたは呼出側の設定順序）／種類：国民年金 ← バインド引数10（PreparedStatementまたは呼出側の設定順序）／種類：厚生年金 ← バインド引数11（PreparedStatementまたは呼出側の設定順序）／種類：共済年金 ← バインド引数12（PreparedStatementまたは呼出側の設定順序）／種類：厚生年金基金 ← バインド引数13（PreparedStatementまたは呼出側の設定順序）／種類：国民年金基金 ← バインド引数14（PreparedStatementまたは呼出側の設定順序）／年金種類 ← バインド引数15（PreparedStatementまたは呼出側の設定順序）／裁定請求 ← バインド引数16（PreparedStatementまたは呼出側の設定順序）／請求予定日 ← バインド引数17（PreparedStatementまたは呼出側の設定順序）／予定年齢 ← バインド引数18（PreparedStatementまたは呼出側の設定順序）／配偶者名 ← バインド引数19（PreparedStatementまたは呼出側の設定順序）／配偶者生年月日 ← バインド引数20（PreparedStatementまたは呼出側の設定順序）／受給有無 ← バインド引数21（PreparedStatementまたは呼出側の設定順序）／予約徴求日 ← バインド引数22（PreparedStatementまたは呼出側の設定順序）／備考 ← バインド引数23（PreparedStatementまたは呼出側の設定順序）／データ更新日 ← バインド引数24（PreparedStatementまたは呼出側の設定順序）／更新時間 ← バインド引数25（PreparedStatementまたは呼出側の設定順序）／更新者 ← バインド引数26（PreparedStatementまたは呼出側の設定順序）／６ヶ月先確認 ← バインド引数27（PreparedStatementまたは呼出側の設定順序）／変更FLG ← バインド引数28（PreparedStatementまたは呼出側の設定順序） |
| 対象条件 | 新しい行を挿入する。重複や採番の扱いは呼出元および列制約に従う。 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 同じ原本に明示トランザクションの呼出元があり、経路別の確定・取消範囲は関連処理で確認する。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/PensionRepository.java:694 / insertDeleted@690 |

SQLの組立規則：INSERT INTO 年金＿削除明細 (店番, 顧客番号, 担当者コード, 顧客氏名, ふりがな, 性別, 住所, 電話番号, 生年月日, "種類：国民年金", "種類：厚生年金", "種類：共済年金", "種類：厚生年金基金", "種類：国民年金基金", 年金種類, 裁定請求, 請求予定日, 予定年齢, 配偶者名, 配偶者生年月日, 受給有無, 予約徴求日, 備考, データ更新日, 更新時間, 更新者, "６ヶ月先確認", 変更FLG) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

#### DB操作 SQL-2CF7CA976867

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-2CF7CA976867 |
| 対象テーブル | 店名テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のgetBranchで「店名テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：店舗ｺｰﾄﾞ = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java:185 / getBranch@184 |

SQLの組立規則：SELECT 店舗ｺｰﾄﾞ AS BRANCH_NO, 店名 AS BRANCH_NAME FROM 店名テーブル WHERE 店舗ｺｰﾄﾞ = ?

#### DB操作 SQL-D9F3500B923D

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-D9F3500B923D |
| 対象テーブル | DB2.Ｕ職員名簿表 |
| 操作 | 参照 |
| 処理説明 | 原本のgetStaffで「DB2.Ｕ職員名簿表」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | 抽出・更新対象条件：S.職員番号 = ? |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java:207 / getStaff@206 |

SQLの組立規則：SELECT S.職員番号 AS STAFF_NO, S.漢字氏名 AS STAFF_NAME, S.カナ氏名 AS STAFF_KANA_NAME, S.所属店番 AS BRANCH_NO, S.役職コード AS ROLE_CODE FROM DB2.Ｕ職員名簿表 S WHERE S.職員番号 = ?

#### DB操作 SQL-E0FD738666D8

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-E0FD738666D8 |
| 対象テーブル | 店名テーブル |
| 操作 | 参照 |
| 処理説明 | 原本のloadBranchNamesで「店名テーブル」を参照する。条件と設定値は以下のSQL式・バインド順序に従う。 |
| 設定項目 | 当該SQL式の列指定・実行時引数を使用する。組立式と原本のパラメーター設定を参照。 |
| 対象条件 | WHERE句による限定はこのSQL式にない。呼出条件・動的付加条件は原本を参照する。 |
| 確定・取消 | 呼出側または接続の設定に従う。当該メソッド単独でのコミット・ロールバック指定はない。 |
| 原本 | nenkin/WEB-INF/src/nenkin/service/ReferenceDataService.java:291 / loadBranchNames@289 |

SQLの組立規則：SELECT 店舗ｺｰﾄﾞ AS BRANCH_NO, 店名 AS BRANCH_NAME FROM 店名テーブル

#### DB操作 SQL-A8F5412DEF20

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-A8F5412DEF20 |
| 対象テーブル | DB2.ＵＷＥＢログイン情報表 |
| 操作 | 挿入・更新（MERGE） |
| 処理説明 | SQLファイルの初期化処理で「DB2.ＵＷＥＢログイン情報表」を挿入・更新（MERGE）する。実データ値は納品仕様書へ転載しない。 |
| 設定項目 | アプリケーション名 ← 原本の初期データ値（値自体は非転載）／ユーザーＩＤ ← 原本の初期データ値（値自体は非転載）／パスワード ← 原本の初期データ値（値自体は非転載） |
| 対象条件 | 抽出・更新対象条件：KEY (アプリケーション名, ユーザーＩＤ) |
| 確定・取消 | 配備・初期化時に実行するSQL。アプリケーションの更新トランザクションとは別に扱う。 |
| 原本 | nenkin/WEB-INF/resources/db/data.sql:1 / SQLファイル |

SQLの組立規則：初期データ定義のため値は原本参照。

#### DB操作 SQL-5C89ADEB93BB

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-5C89ADEB93BB |
| 対象テーブル | DB2.Ｕ職員名簿表 |
| 操作 | 挿入・更新（MERGE） |
| 処理説明 | SQLファイルの初期化処理で「DB2.Ｕ職員名簿表」を挿入・更新（MERGE）する。実データ値は納品仕様書へ転載しない。 |
| 設定項目 | 職員番号 ← 原本の初期データ値（値自体は非転載）／所属店番 ← 原本の初期データ値（値自体は非転載）／漢字氏名 ← 原本の初期データ値（値自体は非転載）／カナ氏名 ← 原本の初期データ値（値自体は非転載）／身分コード ← 原本の初期データ値（値自体は非転載）／性別 ← 原本の初期データ値（値自体は非転載）／生年月日 ← 原本の初期データ値（値自体は非転載）／役職コード ← 原本の初期データ値（値自体は非転載）／作成日 ← 原本の初期データ値（値自体は非転載） |
| 対象条件 | 抽出・更新対象条件：KEY (職員番号) |
| 確定・取消 | 配備・初期化時に実行するSQL。アプリケーションの更新トランザクションとは別に扱う。 |
| 原本 | nenkin/WEB-INF/resources/db/data.sql:4 / SQLファイル |

SQLの組立規則：初期データ定義のため値は原本参照。

#### DB操作 SQL-04E9DB7527CB

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-04E9DB7527CB |
| 対象テーブル | DB2.ＵＪＶ役職コード表 |
| 操作 | 挿入・更新（MERGE） |
| 処理説明 | SQLファイルの初期化処理で「DB2.ＵＪＶ役職コード表」を挿入・更新（MERGE）する。実データ値は納品仕様書へ転載しない。 |
| 設定項目 | 役職コード ← 原本の初期データ値（値自体は非転載）／役職 ← 原本の初期データ値（値自体は非転載） |
| 対象条件 | 抽出・更新対象条件：KEY (役職コード) |
| 確定・取消 | 配備・初期化時に実行するSQL。アプリケーションの更新トランザクションとは別に扱う。 |
| 原本 | nenkin/WEB-INF/resources/db/data.sql:17 / SQLファイル |

SQLの組立規則：初期データ定義のため値は原本参照。

#### DB操作 SQL-304A64D29ABA

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-304A64D29ABA |
| 対象テーブル | N2_DWH.Ｊ事業所コード表２ |
| 操作 | 挿入・更新（MERGE） |
| 処理説明 | SQLファイルの初期化処理で「N2_DWH.Ｊ事業所コード表２」を挿入・更新（MERGE）する。実データ値は納品仕様書へ転載しない。 |
| 設定項目 | 店舗コード ← 原本の初期データ値（値自体は非転載）／枝番 ← 原本の初期データ値（値自体は非転載）／事業所名 ← 原本の初期データ値（値自体は非転載） |
| 対象条件 | 抽出・更新対象条件：KEY (店舗コード, 枝番) |
| 確定・取消 | 配備・初期化時に実行するSQL。アプリケーションの更新トランザクションとは別に扱う。 |
| 原本 | nenkin/WEB-INF/resources/db/data.sql:22 / SQLファイル |

SQLの組立規則：初期データ定義のため値は原本参照。

#### DB操作 SQL-CB7B3D708782

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-CB7B3D708782 |
| 対象テーブル | DB2.ＵＤＢ管理ＤＢ |
| 操作 | 挿入・更新（MERGE） |
| 処理説明 | SQLファイルの初期化処理で「DB2.ＵＤＢ管理ＤＢ」を挿入・更新（MERGE）する。実データ値は納品仕様書へ転載しない。 |
| 設定項目 | ＤＢ名 ← 原本の初期データ値（値自体は非転載）／処理中ＦＬＧ ← 原本の初期データ値（値自体は非転載） |
| 対象条件 | 抽出・更新対象条件：KEY (ＤＢ名) |
| 確定・取消 | 配備・初期化時に実行するSQL。アプリケーションの更新トランザクションとは別に扱う。 |
| 原本 | nenkin/WEB-INF/resources/db/data.sql:27 / SQLファイル |

SQLの組立規則：初期データ定義のため値は原本参照。

#### DB操作 SQL-6B0A53508CEA

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-6B0A53508CEA |
| 対象テーブル | N2_SIGHT.Ｂ顧客基本表 |
| 操作 | 挿入・更新（MERGE） |
| 処理説明 | SQLファイルの初期化処理で「N2_SIGHT.Ｂ顧客基本表」を挿入・更新（MERGE）する。実データ値は納品仕様書へ転載しない。 |
| 設定項目 | 店舗コード ← 原本の初期データ値（値自体は非転載）／顧客番号 ← 原本の初期データ値（値自体は非転載）／カナ氏名 ← 原本の初期データ値（値自体は非転載）／漢字氏名 ← 原本の初期データ値（値自体は非転載）／担当者コード ← 原本の初期データ値（値自体は非転載）／電話番号 ← 原本の初期データ値（値自体は非転載）／漢字住所 ← 原本の初期データ値（値自体は非転載）／性別コード ← 原本の初期データ値（値自体は非転載）／生年月日 ← 原本の初期データ値（値自体は非転載） |
| 対象条件 | 抽出・更新対象条件：KEY (店舗コード, 顧客番号) |
| 確定・取消 | 配備・初期化時に実行するSQL。アプリケーションの更新トランザクションとは別に扱う。 |
| 原本 | nenkin/WEB-INF/resources/db/data.sql:34 / SQLファイル |

SQLの組立規則：初期データ定義のため値は原本参照。

#### DB操作 SQL-AB72701F29DC

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-AB72701F29DC |
| 対象テーブル | 性別テーブル |
| 操作 | 挿入・更新（MERGE） |
| 処理説明 | SQLファイルの初期化処理で「性別テーブル」を挿入・更新（MERGE）する。実データ値は納品仕様書へ転載しない。 |
| 設定項目 | 性別ｺｰﾄﾞ ← 原本の初期データ値（値自体は非転載）／性別 ← 原本の初期データ値（値自体は非転載） |
| 対象条件 | 抽出・更新対象条件：KEY (性別ｺｰﾄﾞ) |
| 確定・取消 | 配備・初期化時に実行するSQL。アプリケーションの更新トランザクションとは別に扱う。 |
| 原本 | nenkin/WEB-INF/resources/db/data.sql:53 / SQLファイル |

SQLの組立規則：初期データ定義のため値は原本参照。

#### DB操作 SQL-974CC766238C

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-974CC766238C |
| 対象テーブル | 裁定請求テーブル |
| 操作 | 挿入・更新（MERGE） |
| 処理説明 | SQLファイルの初期化処理で「裁定請求テーブル」を挿入・更新（MERGE）する。実データ値は納品仕様書へ転載しない。 |
| 設定項目 | 裁請ｺｰﾄﾞ ← 原本の初期データ値（値自体は非転載）／裁定請求 ← 原本の初期データ値（値自体は非転載） |
| 対象条件 | 抽出・更新対象条件：KEY (裁請ｺｰﾄﾞ) |
| 確定・取消 | 配備・初期化時に実行するSQL。アプリケーションの更新トランザクションとは別に扱う。 |
| 原本 | nenkin/WEB-INF/resources/db/data.sql:56 / SQLファイル |

SQLの組立規則：初期データ定義のため値は原本参照。

#### DB操作 SQL-FDB588A8849B

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-FDB588A8849B |
| 対象テーブル | 受給有無テーブル |
| 操作 | 挿入・更新（MERGE） |
| 処理説明 | SQLファイルの初期化処理で「受給有無テーブル」を挿入・更新（MERGE）する。実データ値は納品仕様書へ転載しない。 |
| 設定項目 | 受給ｺｰﾄﾞ ← 原本の初期データ値（値自体は非転載）／受給有無 ← 原本の初期データ値（値自体は非転載） |
| 対象条件 | 抽出・更新対象条件：KEY (受給ｺｰﾄﾞ) |
| 確定・取消 | 配備・初期化時に実行するSQL。アプリケーションの更新トランザクションとは別に扱う。 |
| 原本 | nenkin/WEB-INF/resources/db/data.sql:58 / SQLファイル |

SQLの組立規則：初期データ定義のため値は原本参照。

#### DB操作 SQL-456572D1B62D

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-456572D1B62D |
| 対象テーブル | 店名テーブル |
| 操作 | 挿入・更新（MERGE） |
| 処理説明 | SQLファイルの初期化処理で「店名テーブル」を挿入・更新（MERGE）する。実データ値は納品仕様書へ転載しない。 |
| 設定項目 | 店舗ｺｰﾄﾞ ← 原本の初期データ値（値自体は非転載）／店名 ← 原本の初期データ値（値自体は非転載） |
| 対象条件 | 抽出・更新対象条件：KEY (店舗ｺｰﾄﾞ) |
| 確定・取消 | 配備・初期化時に実行するSQL。アプリケーションの更新トランザクションとは別に扱う。 |
| 原本 | nenkin/WEB-INF/resources/db/data.sql:60 / SQLファイル |

SQLの組立規則：初期データ定義のため値は原本参照。

#### DB操作 SQL-85DBC611F1E0

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-85DBC611F1E0 |
| 対象テーブル | 年金種類テーブル |
| 操作 | 挿入・更新（MERGE） |
| 処理説明 | SQLファイルの初期化処理で「年金種類テーブル」を挿入・更新（MERGE）する。実データ値は納品仕様書へ転載しない。 |
| 設定項目 | 種類ｺｰﾄﾞ ← 原本の初期データ値（値自体は非転載）／年金種類 ← 原本の初期データ値（値自体は非転載） |
| 対象条件 | 抽出・更新対象条件：KEY (種類ｺｰﾄﾞ) |
| 確定・取消 | 配備・初期化時に実行するSQL。アプリケーションの更新トランザクションとは別に扱う。 |
| 原本 | nenkin/WEB-INF/resources/db/data.sql:62 / SQLファイル |

SQLの組立規則：初期データ定義のため値は原本参照。

#### DB操作 SQL-0DE7BDCDCDFA

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-0DE7BDCDCDFA |
| 対象テーブル | 年金1_LK |
| 操作 | 挿入・更新（MERGE） |
| 処理説明 | SQLファイルの初期化処理で「年金1_LK」を挿入・更新（MERGE）する。実データ値は納品仕様書へ転載しない。 |
| 設定項目 | 店番 ← 原本の初期データ値（値自体は非転載）／顧客番号 ← 原本の初期データ値（値自体は非転載）／担当者コード ← 原本の初期データ値（値自体は非転載）／顧客氏名 ← 原本の初期データ値（値自体は非転載）／ふりがな ← 原本の初期データ値（値自体は非転載）／性別 ← 原本の初期データ値（値自体は非転載）／住所 ← 原本の初期データ値（値自体は非転載）／電話番号 ← 原本の初期データ値（値自体は非転載）／生年月日 ← 原本の初期データ値（値自体は非転載）／種類：国民年金 ← 原本の初期データ値（値自体は非転載）／種類：厚生年金 ← 原本の初期データ値（値自体は非転載）／種類：共済年金 ← 原本の初期データ値（値自体は非転載）／種類：厚生年金基金 ← 原本の初期データ値（値自体は非転載）／種類：国民年金基金 ← 原本の初期データ値（値自体は非転載）／年金種類 ← 原本の初期データ値（値自体は非転載）／裁定請求 ← 原本の初期データ値（値自体は非転載）／請求予定日 ← 原本の初期データ値（値自体は非転載）／予定年齢 ← 原本の初期データ値（値自体は非転載）／配偶者名 ← 原本の初期データ値（値自体は非転載）／配偶者生年月日 ← 原本の初期データ値（値自体は非転載）／受給有無 ← 原本の初期データ値（値自体は非転載）／予約徴求日 ← 原本の初期データ値（値自体は非転載）／備考 ← 原本の初期データ値（値自体は非転載）／データ更新日 ← 原本の初期データ値（値自体は非転載）／更新時間 ← 原本の初期データ値（値自体は非転載）／更新者 ← 原本の初期データ値（値自体は非転載）／６ヶ月先確認 ← 原本の初期データ値（値自体は非転載）／変更FLG ← 原本の初期データ値（値自体は非転載） |
| 対象条件 | 抽出・更新対象条件：KEY (ふりがな, 電話番号) |
| 確定・取消 | 配備・初期化時に実行するSQL。アプリケーションの更新トランザクションとは別に扱う。 |
| 原本 | nenkin/WEB-INF/resources/db/data.sql:94 / SQLファイル |

SQLの組立規則：初期データ定義のため値は原本参照。

#### DB操作 SQL-3E11A4E77CE8

| 情報 | 内容 |
| --- | --- |
| 操作ID | SQL-3E11A4E77CE8 |
| 対象テーブル | 年金＿削除明細 |
| 操作 | 挿入・更新（MERGE） |
| 処理説明 | SQLファイルの初期化処理で「年金＿削除明細」を挿入・更新（MERGE）する。実データ値は納品仕様書へ転載しない。 |
| 設定項目 | 店番 ← 原本の初期データ値（値自体は非転載）／顧客番号 ← 原本の初期データ値（値自体は非転載）／担当者コード ← 原本の初期データ値（値自体は非転載）／顧客氏名 ← 原本の初期データ値（値自体は非転載）／ふりがな ← 原本の初期データ値（値自体は非転載）／性別 ← 原本の初期データ値（値自体は非転載）／住所 ← 原本の初期データ値（値自体は非転載）／電話番号 ← 原本の初期データ値（値自体は非転載）／生年月日 ← 原本の初期データ値（値自体は非転載）／種類：国民年金 ← 原本の初期データ値（値自体は非転載）／種類：厚生年金 ← 原本の初期データ値（値自体は非転載）／種類：共済年金 ← 原本の初期データ値（値自体は非転載）／種類：厚生年金基金 ← 原本の初期データ値（値自体は非転載）／種類：国民年金基金 ← 原本の初期データ値（値自体は非転載）／年金種類 ← 原本の初期データ値（値自体は非転載）／裁定請求 ← 原本の初期データ値（値自体は非転載）／請求予定日 ← 原本の初期データ値（値自体は非転載）／予定年齢 ← 原本の初期データ値（値自体は非転載）／配偶者名 ← 原本の初期データ値（値自体は非転載）／配偶者生年月日 ← 原本の初期データ値（値自体は非転載）／受給有無 ← 原本の初期データ値（値自体は非転載）／予約徴求日 ← 原本の初期データ値（値自体は非転載）／備考 ← 原本の初期データ値（値自体は非転載）／データ更新日 ← 原本の初期データ値（値自体は非転載）／更新時間 ← 原本の初期データ値（値自体は非転載）／更新者 ← 原本の初期データ値（値自体は非転載）／６ヶ月先確認 ← 原本の初期データ値（値自体は非転載）／変更FLG ← 原本の初期データ値（値自体は非転載） |
| 対象条件 | 抽出・更新対象条件：KEY (ふりがな, 電話番号, データ更新日) |
| 確定・取消 | 配備・初期化時に実行するSQL。アプリケーションの更新トランザクションとは別に扱う。 |
| 原本 | nenkin/WEB-INF/resources/db/data.sql:121 / SQLファイル |

SQLの組立規則：初期データ定義のため値は原本参照。

