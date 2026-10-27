"""Represent non-field components separately from the business-item count."""
from __future__ import annotations
import html


def enrich_layout(document: str, feature: dict, data: dict) -> str:
    nodes=data['records'].get(feature['source'],{}).get('nodes',[])
    blocks=[]
    for node in nodes:
        tag=node['tag'].split(':')[-1];a=node['attrs']
        if tag not in {'Viewer','ProgressBar','DocumentViewer','FlowDocumentReader'}:
            continue
        name=a.get('x:Name',a.get('Name',tag));escaped=html.escape(name,quote=True)
        if 'Viewer' in tag or tag=='FlowDocumentReader':
            blocks.append('<section class="component" data-component="'+escaped+'"><h2>帳票表示領域</h2><div style="padding:12px;background:#dce7ef">共通帳票ビューア '+escaped+' ／ 操作部は共通UI・帳票製品の設定に従う</div><div style="background:#e9eef2;padding:28px;min-height:400px"><div style="background:white;max-width:520px;min-height:350px;padding:28px;margin:auto;box-shadow:0 1px 5px #aab6c2"><h3>呼出元で作成した帳票</h3><p>ここに受け取った帳票ドキュメントを表示します。</p><p>このHTMLには帳票データを設定していません。印刷・拡大率・ページ移動等の実際のボタン配置は再現していません。</p></div></div><p>業務入力項目ではなく共通部品として数えます。原本の部品宣言：L'+str(node['line'])+'。</p></section>')
        else:
            blocks.append('<section class="component" data-component="'+escaped+'"><h2>処理状況の表示領域</h2><progress aria-label="処理状況（表示例）" style="width:100%"></progress><p>進捗・終了は実処理に依存します。この表示例は処理を実行せず、完了を意味しません。原本L'+str(node['line'])+'。</p></section>')
    return document.replace('</main>',''.join(blocks)+'</main>')
