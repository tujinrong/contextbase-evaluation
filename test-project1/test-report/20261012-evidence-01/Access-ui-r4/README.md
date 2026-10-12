# Access 撮影fixture R4

生成ID `20261012-evidence-01-ui-r4`。修正後の独立VBA・生成器から、新規SingleFile/IncludeTests/NoStartup ACCDBを作成した。Visible=falseのAccess COMでVBAをコンパイルし、production MaintainClass/clsStudentService.SaveStudentを用いて架空クラス1件・学生3件・CREATE監査4件を保存した。全件の実DAO読返しは [synthetic-data.json](synthetic-data.json)、生ログは [seed.raw.log](seed.raw.log)、入力版・ハッシュは [results.json](results.json)。

FileFormat=12、SELF、外部リンク0。COM Close/Quit時のfixture SHA-256は `CD2C8A0497B78EF35C9CD1D2770085C949831C6D142E65B7073152DDE9B7D72C`。原本は開かず、R4原本ハッシュ `090DB949398017D0583B24EA16D79EAC0C055577F82051B75A57146C0906C896` は前後一致した。

実UIで判明した検索「すべて」表示の残件は後続R5で修正するため、このR4 fixtureは修正前の表示証拠として保存する。撮影・手動操作後のfixture内部メタデータが変わる場合のハッシュはrootのUI閉鎖記録で区別する。共有SQL接続はしていない。
