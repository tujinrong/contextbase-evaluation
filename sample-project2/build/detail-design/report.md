<!-- spec-meta: {"schema":"spec-md/1.0","documentId":"SP2-DETAIL-RUN","version":"1.3","path":"sample-project2/build/detail-design/report.md","sheets":[{"heading":"成果物と入力","kind":"GRID","sheet":"01_成果物と入力"},{"heading":"検査・レビュー・保全","kind":"GRID","sheet":"02_検査・レビュー・保全"},{"heading":"採用判断と残件","kind":"GRID","sheet":"03_採用判断と残件"}]} -->
# sample-project2 詳細設計の再生成・確認記録

版1.3／2026-10-30。AG-DETAIL-DESIGN 1.3、専用規則/工程1.2、stage=detail-design、generationMode=canonical-update、runId=sp2-ui-regenerate-20261029。

## 成果物と入力

両方式の今回基本設計をレビュー・凍結した後、Access・CSharp_ASPNETの6機能詳細と必要な共通実装・規約・QA・索引を改訂した。要件本文、DBの業務/物理定義、DEMO認証、seed、業務上限、全体保存と出力範囲は継承した。入力/出力のID・版・SHA、改訂と保持、基本からの対応は各方式の固定manifestへ記録した。

Accessは10改訂・1追加。新しいUI部品・状態・検査契約で5Form/15Section/2Page、付属Label32、列見出し13、必要Dialogを具体化した。物理Sectionと論理Page、Headerの識別/Tab、Footerの操作、native列の非client分、選択後の全文確認、92項目の物理対応と54条件、取消と未反映のイベント順を定めた。

Webは12改訂。共通Shell・自然DOM/キー・行編集、SearchRawとCriteria、取消・保存・dirty確認、状態所有と検索専用履歴snapshot、通常PRG/直接URL/BFCache/失効を具体化した。既存Storeの限定拡張で編集Draftを隔離し、履歴復帰で検索条件を失わない。UI状態失効のMSG-041を追加し、既存40メッセージと認証失効/保存結果不明を維持した。

実装準備の技術調査でWebだけ詳細契約へ戻り、DQA-UI05を限定改訂した。保護操作はJSON fetch＋成功200 navigation envelopeから未消費ticketへ一度だけGET移動し、失敗はJSONと現在DOM/GET URLを保持する。fetchの303自動追随によるticket二重消費、通常formの422表示後のPOST再送、単一form値の容量不足を避ける。Loginのnative POST→303は継承する。変更6文書・同一6候補を独立再レビューし、43現仕様/入力66の再preflightとUI契約3.1へ根拠を更新した。製品書込み/実測より前の仕様改訂で、実装の実値から期待値を緩和していない。

Accessのbuild独立検査と限定Excel試験から、DQA-UI08/09として詳細7文書を局所補正した。F03全文欄は初期330twip/非表示、選択時1980/Detail9450へ展開する。F04はTab900/Header2400の余白を設計し、Detail7920キャンバスを保持する。ネイティブ最小値をそのまま期待値へ転記しない。Excel Footerの小数サイズコードによる文字混入は整数11ptで回避し、本文10.5ptを維持する。76入力と現11候補を独立再確認し、基本8HTML・既存11pt/入力幅・業務/DB/認証を保全した。旧候補の属性/API合格は新候補へ引き継がない。

## 検査・レビュー・保全

| 方式 | 今回の設計検査 | 固定記録 |
| --- | --- | --- |
| Access | DQA-UI08/09後の45文書、164H2、43LIST/586行、423リンク、6基本/詳細ペア92項目・17イベント順・8HTML断片一致、54条件。11候補を独立再確認し、基本20＋DB6の保護SHAは不変 | [結果](../../srcs/Access/build/spec-generation/detail-design/report.md)、[manifest](../../srcs/Access/build/spec-generation/detail-design/manifest.json)、[独立レビュー](../../srcs/Access/build/spec-generation/detail-design/review.json) |
| CSharp_ASPNET | 43文書、494リンク、43LIST、論理/物理各5表48列、83項目・17イベントと6画面＋帳票HTML一致、54図・24静的描画ケース。履歴/BFCacheなど5指摘を独立再確認して解消 | [結果](../../srcs/CSharp_ASPNET/build/spec-generation/detail-design/report.md)、[manifest](../../srcs/CSharp_ASPNET/build/spec-generation/detail-design/manifest.json)、[独立レビュー](../../srcs/CSharp_ASPNET/build/spec-generation/detail-design/review.json) |

構造と同断片描画、自己/独立意味レビュー、目視を分けた。rootは両方式の物理/状態契約と今回の経歴画面代表描画を確認した。Access/Webとも基本と同じMD埋込みHTMLを維持し、単独HTML/PNGを正本にしていない。各manifestの今回出力SHAを集約時にも照合する。アプリソース、ACCDB、DB、製品用UI期待値/観測はこの詳細工程で生成していない。

## 採用判断と残件

Accessは不正TextBox rawでも取消へ到達し、Comboの候補コードと表示/未確定文字を混ぜない。未反映保存・失敗保持・原点/焦点・通常遷移と9カテゴリを実機へ渡す。空Pageを持つHeader TabとDetail入力群、NotInList後のClick/Unload/復元、2165回避は設計済みで、実Accessでの成立はbuildで確認する。F05はZoom=100、幅480～504ptと行高の計測、720ptの縦予算と手動継続見出し/改ページを採用し、全件全文/読戻し/実Excel検証を必須とする。仕様値だけで実印刷成立を宣言しない。

Webはアプリ内復帰の全raw捕捉を保証し、有効な検索snapshotを新しい独立状態へコピーして戻る/再読込を復元する。編集Draftの全復旧を約束せず、未同期時/通信失敗/BFCache/期限/別タブ、Committed後の表示引継ぎ失敗とUnknownを分けて実HTTP/ブラウザー検査へ渡す。rawの不明候補は明示し、正規化や初期値で失わない。

実装・コンパイル・実DB/HTTP・実Form/最終publish・キー/IME/DPI・実Excel/印刷・仕様Excel/PDF変換・利用者受入・正式採点はこの設計工程で未実施。次は独立期待値を仕様から先に固定し、build-agentで実装/検査/隔離再構築へ進む。現在状態は[工程記録](../generation/pipeline.json)を参照。formalScore=null。
