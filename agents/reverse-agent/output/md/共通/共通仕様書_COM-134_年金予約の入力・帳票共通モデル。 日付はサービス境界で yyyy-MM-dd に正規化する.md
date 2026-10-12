# 年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化する

## 表紙

| 項目 | 内容 |
| --- | --- |
| 文書名 | 基本設計書 |
| システム名 |  |
| 機能ID | COM-134 |
| 画面名 | 年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化する |
| 会社名 |  |
| 作成日 |  |


## 概要

### 概要説明

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するの入力・表示・要求処理を行う。

| 情報 | 内容 |
| --- | --- |
| 対象種別 | common |
| 開始契機 | 呼出元からの要求 |
| 処理対象 | 入力値・画面状態 |


## 項目一覧

| No | グループ | 項目名 | 種類 | 入出力 | DB連携項目 | 候補取得元 | 必須 | 形式・桁 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

項目定義数：0項目。表示順と反復行の定義数を区別する。


## イベント仕様

### PensionReservation

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「PensionReservation」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連する処理へ制御を渡す。詳細な実行経路は原本対応を参照する。

### PensionReservation

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「PensionReservation」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 「対象項目がない」に該当するか確認する。該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む。

1.1. 条件成立時：処理結果を呼出元へ返す。この経路の後続手順は実行しない。

2. 関連情報を取得・設定する（処理27：詳細仕様参照）。

3. 関連情報を取得・設定する（処理28：詳細仕様参照）。

4. 関連情報を取得・設定する（処理29：詳細仕様参照）。

5. 関連情報を取得・設定する（処理30：詳細仕様参照）。

6. 関連情報を取得・設定する（処理31：詳細仕様参照）。

7. 関連情報を取得・設定する（処理32：詳細仕様参照）。

8. 関連情報を取得・設定する（処理33：詳細仕様参照）。

9. 関連情報を取得・設定する（処理34：詳細仕様参照）。

10. 関連情報を取得・設定する（処理35：詳細仕様参照）。

11. 関連情報を取得・設定する（処理36：詳細仕様参照）。

12. 関連情報を取得・設定する（処理37：詳細仕様参照）。

13. 関連情報を取得・設定する（処理38：詳細仕様参照）。

14. 関連情報を取得・設定する（処理39：詳細仕様参照）。

15. 関連情報を取得・設定する（処理40：詳細仕様参照）。

16. 関連情報を取得・設定する（処理41：詳細仕様参照）。

17. 関連情報を取得・設定する（処理42：詳細仕様参照）。

18. 関連情報を取得・設定する（処理43：詳細仕様参照）。

19. 関連情報を取得・設定する（処理44：詳細仕様参照）。

20. 関連情報を取得・設定する（処理45：詳細仕様参照）。

21. 関連情報を取得・設定する（処理46：詳細仕様参照）。

22. 関連情報を取得・設定する（処理47：詳細仕様参照）。

23. 関連情報を取得・設定する（処理48：詳細仕様参照）。

24. 関連情報を取得・設定する（処理49：詳細仕様参照）。

25. 関連情報を取得・設定する（処理50：詳細仕様参照）。

26. 関連情報を取得・設定する（処理51：詳細仕様参照）。

27. 関連情報を取得・設定する（処理52：詳細仕様参照）。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| 対象項目がない | 処理結果を呼出元へ返す |

### copy

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「copy」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### getBranchNo

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getBranchNo」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setBranchNo

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setBranchNo」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getBranchName

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getBranchName」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setBranchName

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setBranchName」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getCustomerNo

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getCustomerNo」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setCustomerNo

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setCustomerNo」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getStaffCode

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getStaffCode」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setStaffCode

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setStaffCode」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getCustomerName

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getCustomerName」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setCustomerName

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setCustomerName」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getKanaName

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getKanaName」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setKanaName

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setKanaName」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getGender

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getGender」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setGender

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setGender」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getAddress

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getAddress」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setAddress

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setAddress」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getPhoneNumber

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getPhoneNumber」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setPhoneNumber

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setPhoneNumber」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getBirthDate

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getBirthDate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setBirthDate

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setBirthDate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getClaimStatus

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getClaimStatus」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setClaimStatus

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setClaimStatus」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getClaimScheduledDate

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getClaimScheduledDate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setClaimScheduledDate

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setClaimScheduledDate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getPlannedAge

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getPlannedAge」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setPlannedAge

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setPlannedAge」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getReservationRequestDate

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getReservationRequestDate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setReservationRequestDate

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setReservationRequestDate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getDataUpdateDate

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getDataUpdateDate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setDataUpdateDate

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setDataUpdateDate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getNotes

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getNotes」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setNotes

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setNotes」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getSpouseName

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getSpouseName」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setSpouseName

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setSpouseName」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getHasBenefit

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getHasBenefit」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setHasBenefit

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setHasBenefit」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getSpouseBirthDate

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getSpouseBirthDate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setSpouseBirthDate

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setSpouseBirthDate」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### getPensionType

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「getPensionType」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setPensionType

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setPensionType」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### isNationalPension

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「isNationalPension」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setNationalPension

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setNationalPension」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### isEmployeePension

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「isEmployeePension」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setEmployeePension

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setEmployeePension」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### isMutualAidPension

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「isMutualAidPension」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setMutualAidPension

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setMutualAidPension」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### isEmployeePensionFund

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「isEmployeePensionFund」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setEmployeePensionFund

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setEmployeePensionFund」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### isNationalPensionFund

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「isNationalPensionFund」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setNationalPensionFund

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setNationalPensionFund」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### isSixMonthCheck

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「isSixMonthCheck」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |

### setSixMonthCheck

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「setSixMonthCheck」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 関連情報を取得・設定する（処理2：詳細仕様参照）。

### valueOrEmpty

#### 処理概要

年金予約の入力・帳票共通モデル。 日付はサービス境界で yyyy-MM-dd に正規化するで「valueOrEmpty」の要求を受け付ける。入力・確認・データ操作・応答の順と、条件が成立しない場合の処理を以下に示す。

#### 処理手順

1. 処理結果を呼出元へ返す。この経路の後続手順は実行しない。

#### 結果・例外時の扱い

| 到達条件 | 結果 |
| --- | --- |
| この終了経路へ到達した場合 | 処理結果を呼出元へ返す |


## 補足説明

### 適用条件

各仮定のQA番号を確認する。静的に確認できた操作・条件を適用する。

### 処理・条件の原本対応

文書内の条件番号・処理番号は次の原本表記に対応する。完全な業務用語への置換を行っていない箇所はQA・reportで確認する。

| イベント | 参照番号 | 原本条件・処理 |
| --- | --- | --- |
| PensionReservation | 処理1 | sixMonthCheck = source.sixMonthCheck |
| PensionReservation | 処理2 | nationalPensionFund = source.nationalPensionFund |
| PensionReservation | 処理3 | employeePensionFund = source.employeePensionFund |
| PensionReservation | 処理4 | mutualAidPension = source.mutualAidPension |
| PensionReservation | 処理5 | employeePension = source.employeePension |
| PensionReservation | 処理6 | nationalPension = source.nationalPension |
| PensionReservation | 処理7 | pensionType = source.pensionType |
| PensionReservation | 処理8 | spouseBirthDate = source.spouseBirthDate |
| PensionReservation | 処理9 | hasBenefit = source.hasBenefit |
| PensionReservation | 処理10 | spouseName = source.spouseName |
| PensionReservation | 処理11 | notes = source.notes |
| PensionReservation | 処理12 | dataUpdateDate = source.dataUpdateDate |
| PensionReservation | 処理13 | reservationRequestDate = source.reservationRequestDate |
| PensionReservation | 処理14 | plannedAge = source.plannedAge |
| PensionReservation | 処理15 | claimScheduledDate = source.claimScheduledDate |
| PensionReservation | 処理16 | claimStatus = source.claimStatus |
| PensionReservation | 処理17 | birthDate = source.birthDate |
| PensionReservation | 処理18 | phoneNumber = source.phoneNumber |
| PensionReservation | 処理19 | address = source.address |
| PensionReservation | 処理20 | gender = source.gender |
| PensionReservation | 処理21 | kanaName = source.kanaName |
| PensionReservation | 処理22 | customerName = source.customerName |
| PensionReservation | 処理23 | staffCode = source.staffCode |
| PensionReservation | 処理24 | customerNo = source.customerNo |
| PensionReservation | 処理25 | branchName = source.branchName |
| PensionReservation | 処理26 | branchNo = source.branchNo |
| PensionReservation | 処理27 | branchNo = source.branchNo |
| PensionReservation | 処理28 | branchName = source.branchName |
| PensionReservation | 処理29 | customerNo = source.customerNo |
| PensionReservation | 処理30 | staffCode = source.staffCode |
| PensionReservation | 処理31 | customerName = source.customerName |
| PensionReservation | 処理32 | kanaName = source.kanaName |
| PensionReservation | 処理33 | gender = source.gender |
| PensionReservation | 処理34 | address = source.address |
| PensionReservation | 処理35 | phoneNumber = source.phoneNumber |
| PensionReservation | 処理36 | birthDate = source.birthDate |
| PensionReservation | 処理37 | claimStatus = source.claimStatus |
| PensionReservation | 処理38 | claimScheduledDate = source.claimScheduledDate |
| PensionReservation | 処理39 | plannedAge = source.plannedAge |
| PensionReservation | 処理40 | reservationRequestDate = source.reservationRequestDate |
| PensionReservation | 処理41 | dataUpdateDate = source.dataUpdateDate |
| PensionReservation | 処理42 | notes = source.notes |
| PensionReservation | 処理43 | spouseName = source.spouseName |
| PensionReservation | 処理44 | hasBenefit = source.hasBenefit |
| PensionReservation | 処理45 | spouseBirthDate = source.spouseBirthDate |
| PensionReservation | 処理46 | pensionType = source.pensionType |
| PensionReservation | 処理47 | nationalPension = source.nationalPension |
| PensionReservation | 処理48 | employeePension = source.employeePension |
| PensionReservation | 処理49 | mutualAidPension = source.mutualAidPension |
| PensionReservation | 処理50 | employeePensionFund = source.employeePensionFund |
| PensionReservation | 処理51 | nationalPensionFund = source.nationalPensionFund |
| PensionReservation | 処理52 | sixMonthCheck = source.sixMonthCheck |
| setBranchNo | 処理1 | this.branchNo = branchNo |
| setBranchNo | 処理2 | this.branchNo = branchNo |
| setBranchName | 処理1 | this.branchName = valueOrEmpty(branchName) |
| setBranchName | 処理2 | this.branchName = valueOrEmpty(branchName) |
| setCustomerNo | 処理1 | this.customerNo = customerNo |
| setCustomerNo | 処理2 | this.customerNo = customerNo |
| setStaffCode | 処理1 | this.staffCode = staffCode |
| setStaffCode | 処理2 | this.staffCode = staffCode |
| setCustomerName | 処理1 | this.customerName = valueOrEmpty(customerName) |
| setCustomerName | 処理2 | this.customerName = valueOrEmpty(customerName) |
| setKanaName | 処理1 | this.kanaName = valueOrEmpty(kanaName) |
| setKanaName | 処理2 | this.kanaName = valueOrEmpty(kanaName) |
| setGender | 処理1 | this.gender = valueOrEmpty(gender) |
| setGender | 処理2 | this.gender = valueOrEmpty(gender) |
| setAddress | 処理1 | this.address = valueOrEmpty(address) |
| setAddress | 処理2 | this.address = valueOrEmpty(address) |
| setPhoneNumber | 処理1 | this.phoneNumber = valueOrEmpty(phoneNumber) |
| setPhoneNumber | 処理2 | this.phoneNumber = valueOrEmpty(phoneNumber) |
| setBirthDate | 処理1 | this.birthDate = valueOrEmpty(birthDate) |
| setBirthDate | 処理2 | this.birthDate = valueOrEmpty(birthDate) |
| setClaimStatus | 処理1 | this.claimStatus = valueOrEmpty(claimStatus) |
| setClaimStatus | 処理2 | this.claimStatus = valueOrEmpty(claimStatus) |
| setClaimScheduledDate | 処理1 | this.claimScheduledDate = valueOrEmpty(claimScheduledDate) |
| setClaimScheduledDate | 処理2 | this.claimScheduledDate = valueOrEmpty(claimScheduledDate) |
| setPlannedAge | 処理1 | this.plannedAge = plannedAge |
| setPlannedAge | 処理2 | this.plannedAge = plannedAge |
| setReservationRequestDate | 処理1 | this.reservationRequestDate = valueOrEmpty(reservationRequestDate) |
| setReservationRequestDate | 処理2 | this.reservationRequestDate = valueOrEmpty(reservationRequestDate) |
| setDataUpdateDate | 処理1 | this.dataUpdateDate = valueOrEmpty(dataUpdateDate) |
| setDataUpdateDate | 処理2 | this.dataUpdateDate = valueOrEmpty(dataUpdateDate) |
| setNotes | 処理1 | this.notes = valueOrEmpty(notes) |
| setNotes | 処理2 | this.notes = valueOrEmpty(notes) |
| setSpouseName | 処理1 | this.spouseName = valueOrEmpty(spouseName) |
| setSpouseName | 処理2 | this.spouseName = valueOrEmpty(spouseName) |
| setHasBenefit | 処理1 | this.hasBenefit = valueOrEmpty(hasBenefit) |
| setHasBenefit | 処理2 | this.hasBenefit = valueOrEmpty(hasBenefit) |
| setSpouseBirthDate | 処理1 | this.spouseBirthDate = valueOrEmpty(spouseBirthDate) |
| setSpouseBirthDate | 処理2 | this.spouseBirthDate = valueOrEmpty(spouseBirthDate) |
| setPensionType | 処理1 | this.pensionType = valueOrEmpty(pensionType) |
| setPensionType | 処理2 | this.pensionType = valueOrEmpty(pensionType) |
| setNationalPension | 処理1 | this.nationalPension = nationalPension |
| setNationalPension | 処理2 | this.nationalPension = nationalPension |
| setEmployeePension | 処理1 | this.employeePension = employeePension |
| setEmployeePension | 処理2 | this.employeePension = employeePension |
| setMutualAidPension | 処理1 | this.mutualAidPension = mutualAidPension |
| setMutualAidPension | 処理2 | this.mutualAidPension = mutualAidPension |
| setEmployeePensionFund | 処理1 | this.employeePensionFund = employeePensionFund |
| setEmployeePensionFund | 処理2 | this.employeePensionFund = employeePensionFund |
| setNationalPensionFund | 処理1 | this.nationalPensionFund = nationalPensionFund |
| setNationalPensionFund | 処理2 | this.nationalPensionFund = nationalPensionFund |
| setSixMonthCheck | 処理1 | this.sixMonthCheck = sixMonthCheck |
| setSixMonthCheck | 処理2 | this.sixMonthCheck = sixMonthCheck |

