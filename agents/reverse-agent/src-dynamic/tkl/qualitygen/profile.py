"""Source-reviewed TKL rules. This is a project profile, not a language adapter."""
COMMON_RULES = [
 ('COM-B01','変更検知と終了確認','入力変更を監視している画面では変更状態を保持する。子画面または別画面への移動では、保存する・保存せず移動する・取消を分ける。保存関数が失敗した場合は移動を中止する。注文の新規入力では共通の終了確認を使わず、未確定明細に対する個別の確認を優先する。','MyWindowBase.vb'),
 ('COM-B02','必須項目の適用範囲','文字とパスワードは前後空白を除いて空でないこと、日付は指定があること、選択欄は選択位置があることを検証する。直接の表示状態が非表示の対象は必須検査を通過する実装である。親領域の実効表示や操作不可状態まで除外すると決めつけない。操作モードごとの対象集合は個別仕様を優先する。','MyApp.vb'),
 ('COM-B03','明細の一時保存と確定','追加・修正の明細保存は画面の一覧に反映する。選択行がない修正・削除は受け付けず、削除は確認の了承後に行う。明細が0件なら確定・修正・削除の操作を無効にする。明細追加等の処理を登録した時点で、DBの登録が実行されたとは扱わない。','MyWindowChildCommandGrid.vb'),
 ('COM-B04','値引額・単価・金額','値引額は定価×（値引率÷100）を小数点以下0桁で最も近い偶数に丸める。ちょうど0.5円は0円、1.5円は2円、2.5円は2円になる。現行の途中計算は二進浮動小数によるため、十進固定小数への変更時は境界例を再比較する。請求単価は定価－値引額であり、この共通関数に0円への切上げはない。請求金額は請求単価×数量で、明細合計は各金額の総和である。','MyApp.vb'),
 ('COM-B05','条件別価格の優先順位','書籍・顧客区分・配送区分に一致する条件別書籍価格を優先する。一致行がない場合は書籍基本価格を参照する。条件別価格が存在する場合だけ、取得した値引率・値引額を設定する。新規に作成した価格取得用情報の初期値は0であるため、基本価格へ切り替えた場合の値引率・値引額は0になる。取得行が複数なら先頭1行を採用するが、検索に並び順の指定はなく、複数一致の優先順位は未確定である。','MasterBookModel.vb'),
 ('COM-B06','DB更新の一括性','トランザクション付きの共通更新処理は接続を開き、取引を開始し、渡された更新文を配列順に実行して最後に確定する。途中失敗は全体の取消を試み、エラーを表示して失敗を返す。接続を開く処理は内部の例外捕捉より前にあるため、接続開始エラーまで必ず失敗値になるとは保証しない。取引を使わない別の更新関数は同じ保証を持たない。','MyNpg.vb'),
 ('COM-B07','検索条件の省略と一致方式','値が未設定または空の場合、一致検索の条件は追加しない。通常の一致条件、部分一致、範囲条件は別の共通処理で作る。部分一致では指定に応じて左右のワイルドカードと表記変換を適用する。範囲の上端・下端、未指定側の扱いは実際に利用する関数の条件に従い、画面名だけから同じ検索方式と推定しない。','MyNpg.vb'),
 ('COM-B08','文字数と文字コード','項目の上限は文字数とバイト数を分ける。バイト制限の共通入力部品はShift_JISによる長さを確認し、貼り付け時は残容量に入る文字列に制限する。一方、文字数のみの部品にこのバイト制限を適用してはならない。数字入力部品の貼り付け拒否、金額入力部品の整数丸めは別条件として記録する。','MyStyle.vb'),
 ('COM-B09','日付のDB受渡し','日付からDBへ渡す値は年月日を8桁の数値にした値である。未設定日はDBの空値として渡す。表示用の区切り付き文字列やソース言語の日時値を、そのまま物理列の型とみなさない。DBからの変換では空値や所定桁数に達しない値を未設定として扱う。','MyApp.vb'),
 ('COM-B10','認証・帳票・通知','認証失敗と操作権限不足は区別する。共通メッセージの定義と表示箇所は別に管理し、動的な値を文面の固定部分に含めない。帳票データの作成、プレビュー、印刷、ファイル保存を別の完了状態とする。現行のファイル出力には内部でエラーを表示した後も完了通知へ進む経路があり、成功保証として引用しない。','MyMessage.vb')]

PILOT_DETAILS = {
 'Window_Loaded': '注文日、請求区分、配送区分、送付先、送り状都道府県、書籍、売上区分、値引率、値引額、数量を必須検査の対象として登録する。新規時は明細保存用の変更監視と明細の追加・修正・削除を準備し、注文日を当日、数量を通常1・マイナス指定時－1、価格関連を0にする。新規時の請求区分は直接変更できない。修正時は確定ボタンを保存と表示し、明細一覧と操作モードの領域を非表示にする。表示変更をデータ削除と扱わない。',
 'Window_Closing': '新規入力で確定前の明細が1件以上ある場合だけ、明細を保存して戻るか確認する。「はい」はDB確定を試み、失敗したら終了を取り消す。「いいえ」はDB確定を行わず終了する。「取消」は入力内容を残して画面に戻る。既に確定済み、明細0件、修正モードの場合はこの新規専用分岐に入らない。共通終了確認との適用範囲を分ける。',
 'btnExec_Click': '確定確認に了承した場合だけ更新を開始する。新規では画面にある明細の現在順で、明細ごとに注文番号を取得し、特別出版注文、送り状送付先の順に追加する。一括更新指定のある明細については続いて関連送り状を更新する。修正では対象注文番号の注文と送り状を順に更新する。複数の更新は最後に一度だけトランザクション付き共通処理へ渡す。成功後だけ未保存状態を解除し、確定済みと呼出元への成功を設定して閉じる。失敗した場合は成功状態に変更せず、画面を閉じない。採番した値の消費やDB関数の巻戻し可否は別途確認する。',
 'cmbSendId_SelectionChanged': '初期表示など変更監視が停止している間は追加処理を行わない。選択した送付先顧客を取得し、名称、所属、部署、電話、住所を表示する。送り状の宛名には顧客名と所属名を空白でつないだ文字列を設定し、都道府県・郵便番号前後・住所・電話へ初期値をコピーする。送り状欄は表示用の顧客情報とは別の編集値として保持する。',
 'btnSend_Click': '顧客選択を開く。選択結果が確定した場合だけ送付先IDを変更し、その選択変更に連動する顧客情報の再表示と送り状初期化につなげる。選択取消の場合は従前のIDを維持する。顧客を選ぶこと自体では注文のDB確定は行わない。',
 'btnSendAdd_Click': '顧客を追加する画面を開く。追加結果が返った場合は新しい顧客を候補リストへ追加し、その顧客を送付先として選択する。顧客マスタの保存と注文の確定は別取引であり、注文画面を後で取り消したときに追加顧客も消えるという保証はない。',
 'btnSendEdit_Click': '現在の送付先顧客を修正画面へ渡す。修正が完了した場合は顧客情報を取り直し、送り状の初期値に反映する。入力済みの送り状の値が更新される可能性があるため、顧客修正後の住所・電話・宛名を確認する。顧客画面で取消した場合は注文画面の受渡しを確定しない。',
 'cmbSagawaTdfk_SelectionChanged': '変更監視中に送り状都道府県が変わった場合、選択状態を見て郵便番号検索の使用可否を切り替える。候補を選べている場合は検索を有効にし、未選択なら無効にする。この時点では郵便番号や住所のDB更新は行わない。',
 'btnSagawaPostalno_Click': '指定した都道府県を郵便番号検索へ渡す。検索結果を確定したときだけ郵便番号を前3桁と後4桁に分け、送り状郵便番号と住所を置き換える。取消時は入力済みの宛先を維持する。送付先顧客そのものの住所を更新する操作とは異なる。',
 'cmbBook_SelectionChanged': '書籍の選択有無で価格取得の可否を切り替える。書籍が解除された場合は注文の書籍・売上区分・金額類を初期化し、新規入力では数量も通常・マイナスの初期値へ戻す。書籍が指定された場合は条件別価格を優先して取得し、該当なしなら基本価格へ切り替える。送付先変更や配送区分変更が必ず自動価格再取得を起こすとは扱わず、呼出しのあるイベントだけで計算する。',
 'btnBook_Click': '書籍検索で確定した書籍を選択する。現時点の候補一覧にそのコードがない場合は候補一覧を取得し直し、対象を選べるようにする。検索取消では書籍を変更しない。書籍を選び直した場合は、その書籍と現在の顧客・配送区分に対する価格取得処理へ連動する。',
 'btnPrice_Click': '書籍コード、顧客区分、配送区分をキーに価格を取得する。条件別価格に一致しないときは書籍基本価格を使う。売上区分、定価、値引率、値引額を画面へ設定し、定価から値引額を引いて単価を求め、数量を乗じて金額を再計算する。取得した本体価格・送料をそのまま請求単価に加算する仕様ではない。複数一致や定価NULLは正常値を創作せず、未解決のデータ条件として残す。',
 'txtReducePercent_LostFocus': '入力変更監視中に値引率が確定したら、入力値を保持情報へ反映する。定価と率から値引額を偶数丸めで求め、その値引額で請求単価、続いて数量による請求金額を更新する。価格取得で読み込んだ固定の値引額を維持するイベントとは区別する。DBにはこの時点では保存しない。',
 'txtDiscount_LostFocus': '変更監視中に直接入力した値引額を保持情報へ反映し、定価－値引額で単価、単価×数量で金額を計算する。値引率を値引額から逆算して上書きする処理はこの経路にはない。共通の単価計算は負の値を0に補正しないため、別の業務検証を確認せずに0円下限を追加しない。',
 'txtSendCopies_LostFocus': '新規の通常入力は1～999冊、新規のマイナス入力は－999～－1冊を許可する。修正モードは－999～999冊を許可し、0冊も範囲内である。空欄は検査前に0として扱う。上限・下限を外れた場合は上限以下または下限以上の入力を求め、表示数量を通常1またはマイナス－1へ戻して、このイベントでの金額再計算を中止する。範囲内のときだけ単価×数量を計算する。戻した表示値が保持情報へ反映される時期はUIのデータ受渡し設定に依存するため、実画面で別に検証する。',
 'btnCalc_Click': '現在の請求単価と数量から請求金額を再計算する。この計算ボタンの実装は、書籍の価格再取得や値引率からの値引額再計算を呼び出していない。価格マスタが変更された場合に、この操作だけで最新価格になるとは説明しない。',
 'btnClear_Click': '注文日を当日に戻し、送付先の情報を初期化し、書籍・価格・値引き・金額の明細入力値を初期化する。数量はマイナス指定に応じて1または－1とする。既に画面内の明細一覧へ保存した注文を一括削除する操作ではなく、DB確定済みの注文もこの操作では削除しない。',
 'chkMinus_Click': '通常へ戻す場合は数量を1、入力欄の上限を3桁とし、マイナス指定時は数量を－1、符号を含め4桁の入力へ切り替える。切替後は請求金額を再計算する。既存の数量に単に符号を付け替えるのではなく、初期値へ置き換える点に注意する。',
 'txtPostalno_LostFocus': '入力内容を保持情報へ反映し、前後空白を除いた郵便番号が前3桁・後4桁そろった場合だけ住所を検索する。取得住所が空でない場合に送り状住所を補完する。桁数不足または該当なしの場合は既存の住所を空にしない。郵便番号の先頭ゼロは数値変換で失わず保持する。'
}

PILOT_CONTRACT = {
 'version':'1.0','feature_id':'TKL-011','scope':'business_core_with_mocked_io',
 'quantity':{'add_positive':[1,999],'add_negative':[-999,-1],'edit':[-999,999],'default_positive':1,'default_negative':-1,'empty':0,'invalid_recalculate':False},
 'money':{'discount':'price*(rate/100)','intermediate':'binary64','round_digits':0,'midpoint':'to_even','unit_price':'price-discount','clamp_zero':False,'amount':'unit_price*quantity'},
 'price_lookup':{'priority':['conditional','base'],'key':['book_cd','cs_kbn','haiso_kbn'],'base_discount':0,'base_rate':0,'missing_row':'new_model_defaults','multiple_rows':'first_unordered','null_price':'conversion_failure_not_zero'},
 'workflow':{'new_order_sequence':['C:tt301_order_pub_send','C:tt302_order_pub_send_list','optional:U:tt302_order_pub_send_list'],'edit_order_sequence':['U:tt301_order_pub_send','U:tt302_order_pub_send_list','optional:U:tt302_order_pub_send_list'],'update_scope':'one_common_transaction_per_confirmation','bulk_filter':['same_customer','same_send_id','exists_t401'],'exclude_current_order':False,'curregeis':0,'success_flags':['changed_false','updated_true','dialog_true'],'failure_flags':'unchanged','save':'memory_only','confirm':'database'},
 'not_verified':['WPF_binding_and_focus','physical_DB_constraints','live_transaction_rollback','sequence_rollback','external_reports','complete_feature_rebuild']
}
DB_CONTRACT = {
 'version':'1.0','feature_id':'TKL-011',
 'order_table':'tt301_order_pub_send','send_table':'tt302_order_pub_send_list','eligibility_table':'t401_invoice_arrangements',
 'order_columns':[['order_no','prORDER_NO','OrderNo'],['customer_id','prCUSTOMER_ID','CustomerId'],['haiso_kbn','prHAISO_KBN','DeliveryKbn'],['cs_kbn','prCS_KBN','CustomerKbn'],['order_date','prORDER_DATE','OrderDate'],['send_id','prSEND_ID','SendId'],['book_cd','prBOOK_CD','BookCd'],['seikyu_kbn','prSEIKYU_KBN','SeikyuKbn'],['send_copies','prSEND_COPIES','SendCopies'],['seikyu_price','prSEIKYU_PRICE','SeikyuPrice'],['seikyu_tanka','prSEIKYU_TANKA','SeikyuTanka'],['book_price','prFIXED_PRICE','FixedPrice'],['discounts','prDISCOUNTS','Discounts'],['curregeis','prCURREGEIS','constant_zero'],['uriage_kbn','prURIAGE_KBN','UriageKbn'],['reducepercent','prREDUCEPERCENT','ReducePercent'],['updt','','database_now'],['upnm','prUPNM','current_user']],
 'send_columns':[['order_no','prORDER_NO','OrderNo'],['send_id','prSEND_ID','SendId'],['send_name','prSEND_NAME','SagawaNm'],['send_ken_cd','prSEND_KEN_CD','SagawaTdfkCd'],['send_postalno1','prSEND_POSTALNO1','SagawaPostalno1'],['send_postalno3','prSEND_POSTALNO3','SagawaPostalno3'],['send_address','prSEND_ADDRESS','SagawaAddress'],['send_tel','prSEND_TEL','SagawaTel'],['updt','','database_now'],['upnm','prUPNM','current_user']],
 'physical_definition_status':'not_verified','key_note':'order_no is an observed WHERE key, not proof of a primary key'
}
