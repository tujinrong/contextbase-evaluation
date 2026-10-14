# 最新検索稿 basic05/detail04 のsource-only照合

対象は basic05 SHA `1f307707bebcb621f7c0e7f895cec8e2a5c386c98c96aa5821c7e9619f0f6778`（949行）、detail04 SHA `658617eb1367817031128eef12fbd51d50b758e04dff14f01997f14eacb1c785`（896行）。固定checklist SHA `40e184c35018ec8efe31915a91c48ab35a4ebb70670e61bc8d35c7d0a4aa4242` に照合した。原仕様、spec-eval、採点、training-assisted、新しいbasic06/detail05は読んでいない。コード・プロンプト・原fact・原ソース・checklist・稿は変更していない。

**新たな重要な業務意味の漏れ・誤りは見つからなかった。** 全53動作は各稿で含まれる34、必須欠落1、対象外18。40項目グループと23図（基本12・詳細11）を照合した。検索12条件/11列、6イベント、4結果、原入力/加工値/DB容量の単位、候補下書きとApplied、optionsの版・排他省略、ページ補正とResume差、状態反映後の表示失敗、commit・非Saved・303・読込版を保持している。

旧R1の重要指摘は指定SHAで解消している。

- 同日検索: basic134–135行、detail133–134/637行は開始≦終了・両端を含む。source `Core/SqlServerStudentService.cs:120–122` と一致。
- Unknownの回復案内: basic723行は再保存前の検索確認を促す。detail852–858行と862–892行の図はサービスFieldError→ModelState→画面再表示、削除後Load失敗、未接続WebPresentation.Save helperの文言を分けて説明する。

既存の軽微な不足は残る。

- DC-07: 共通HTTP保護の具体値不足。basic全稿はno-store/nosniff/no-referrer/CSP設定自体を記載せず、detail556行は名前のみ。両稿でCookieのSecureAlways/HttpOnly/SameSiteStrict/30分slide、HTTPS redirect、CSPのself/frame-ancestors none等が欠落。source `Infrastructure/WebHostSetup.cs:14–15,22–25` の実引用をrootとsource_pilotへ共有した。active06/05の凍結contextは変更せず、後続AI局所改訂または補足の候補とする。
- DC-08: basic図670/782行のUnknown条件にAND/OR括弧がない。ただし681/797行と715行が正確な式を定義し、書込未開始はSystemErrorと限定している。新たな重要誤りとはせず、図だけでも括弧を付ける補足候補とする。
- DC-09: basic827/839/845行の任意所属は列/FKのNULL属性として正しいが、856行のCHECK説明は01/02のクラス必須を具体化していない。detail798行は区分依存条件を正確に限定する。元DDL `database/001_schema.sql:198` を添える候補とする。

個人条件はPOSTとサーバーメモリ、往復URLは識別値、所有者/session/任意Tab照合という原ソース境界は保持されている。no-store等の設定不足は上記へ記録した。Warningログ設定だけから実環境でのPII無出力を保証せず、DB暗号化・永続化も推定しない。

封印snapshotのraw sourcesを41件列挙・SHA記録し、うち固定checklistにある25 raw/indexed組の以前のSHA一致を確認した。残る16は補助モデル・filter・layout・設定・build・保守実装と、deployment/verification/package metadataである。前者の接続・属性、後者の役割境界を静的に確認した。全41件に対する独立した以前の全体seal/manifestは読んでいないため、その照合を完了したとは主張しない。

アプリ・DB・deployment script・ログイン・多重要求は未実行。画像のnative確認も未実施。既知のgeometry/selected=falseの再測定へ時間を使わず、この監査からcanonical採用や視覚合格を出していない。basic06/detail05には別SHA監査が必要である。

`document-comparison-03.json` SHA `3e1b6ee5f8d0a61fec5d5aa055d48bda3e48cf37ea9afc2e993eaa8a23d8716d`。全269引用範囲で稿・sourceの実文字列、入力SHA、範囲SHA一致を確認した。記録スクリプトは引用と整合確認だけで、仕様書本文を生成していない。
