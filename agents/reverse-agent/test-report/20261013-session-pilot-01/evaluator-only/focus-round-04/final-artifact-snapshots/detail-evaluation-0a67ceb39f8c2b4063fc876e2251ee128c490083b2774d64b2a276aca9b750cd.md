# 学生検索・登録 focus round 04 独立意味評価

EVALUATOR ONLY — 原期待値・採点証拠は生成入力へ渡さない。

対象はCSharp_ASPNET詳細画面2冊のみ。生成4.0、原仕様8.0、採点表7.4。training-assistedの同じsource43/reference11。
**全281行／316点を保持。観測一致283点、不足20点、矛盾6点、未裁定7点。**
正式完了得点・率・95%判定はnull。95%必要整数点301、保留を分母から外さない。
重大矛盾0件。行別の理由と現版証拠を参照。

| 対象 | 原行数 | 原満点 | 確認済 | 不足 | 矛盾 | 未裁定 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 学生検索 | 120 | 147 | 133 | 10 | 0 | 4 |
| 学生登録・編集 | 161 | 169 | 150 | 10 | 6 | 3 |

新規252一致・22不足・2矛盾・5保留。
検索と編集は独立担当が新本文を全行再読。設計意図と現行ソースを区別し、旧点・描画合格・単語存在で加点しない。
各行の理由と現版根拠を読み直し、原行の操作文脈との照合記録を保存。
編集の2 FLOWは正常な非空Context.Getの結果をReturnRevision=NULLへ合流させるため各3点のconflict。正しい手順/結果は重複減点しない。
編集1064の未escape縦棒による表示欠落は別診断。rawの正しい式と別の正しい補足を併読し、新しい配点行を追加しない。
保存不備：編集の暫定156点JSONと初期context reviewは完全byteを先に保存せず上書きした。既知SHA・ツール出力・残存初期MDを初期JSONの復元としない。
現在の最終JSON/reviewは別byte snapshotへ固定。次回以降の採点保存をexclusive-createへ変更し、旧snapshot＋別version＋transitionの保存を合成5検査で確認。過去の欠落byteは復元していない。

機械検査：281原ID/配点、4428根拠範囲、130固定pin、58現行原入力、130現行capsule/起動記録pin、起動runtime13のSHA一致。
起動scopeのpreservedRunnerPathを固定し、そのSHAと凍結コピーを照合。後続作業driverは入力pinおよびドリフト比較の対象外。
両MDは完了draft-resultのcontentSha256と公開/凍結本文が一致。生成scopeは実際のlegacy-v1 unsealedのまま。
後続のruntime改修・sealedスコープをこのラウンドへ遡及評価しない。

[合算JSON](detail-evaluation.json)、[証拠/ハッシュ検査](detail-validation.json)、[検索](search-evaluation.md)、[登録](editor-evaluation.md)。
実アプリ/実DB/ビルド/競合試験、原品質軸全面、他文書/1408点全体は未実施。
