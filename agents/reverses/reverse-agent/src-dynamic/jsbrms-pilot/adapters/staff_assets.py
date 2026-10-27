"""Reviewed project-specific assets and QA; used only during P2."""
from __future__ import annotations
from pathlib import Path
import shutil
import subprocess
from bs4 import BeautifulSoup

def static_screen(root: Path, input_dir: str, cfg: dict) -> str:
    base=root/input_dir/cfg['base']
    markup=BeautifulSoup((base/'Pages/Staff.cshtml').read_text(encoding='utf-8-sig'),'html.parser')
    layout=BeautifulSoup((base/'Pages/Shared/_Layout.cshtml').read_text(encoding='utf-8-sig'),'html.parser')
    section=markup.find('section');header=layout.find('header');footer=layout.find('footer')
    if not section or not header or not footer:raise ValueError('Pilot markup sections missing')
    for part in (section,header,footer):
        for node in part.find_all(['script','link','style','iframe','object']):node.decompose()
        for node in part.find_all(True):
            if node.name=='input':node['value']=''
            for attr in list(node.attrs):
                if attr.startswith(('asp-','on')) or attr in {'src','href','action','formaction'}:del node[attr]
        for button in part.select('.navbar-toggler'):button.decompose()
    css=(base/'wwwroot/css/site.css').read_text(encoding='utf-8-sig')
    # The repository does not include Bootstrap's dist CSS. Minimal container/flex
    # rules below are a documented approximation, not a captured running screen.
    fallback='''*{box-sizing:border-box}body{margin:0;font-family:"Noto Sans CJK JP","Meiryo",sans-serif}.container-fluid{width:100%;padding:0 20px}.navbar .container-fluid{display:flex;align-items:center;gap:36px}.navbar-collapse{display:flex;align-items:center}.navbar-nav{display:flex;list-style:none;padding:0;margin:0}.nav-link,.navbar-brand{text-decoration:none}.form-control{display:block;width:100%}.navbar-toggler{display:none}.validation-summary:empty{display:none}'''
    return '<!doctype html><html lang="ja"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\';style-src \'unsafe-inline\';img-src data:"><style>'+fallback+'\n'+css+'</style><body>'+str(header)+'<div class="container-fluid app-shell"><main class="app-main">'+str(section)+'</main></div>'+str(footer)+'</body></html>'


def prepare_assets(root: Path, input_dir: str, cfg: dict, *, asset_root: Path | None = None) -> dict:
    assets=asset_root or root/'output/md/基本設計書/assets';assets.mkdir(parents=True,exist_ok=True)
    report=root/'report/pilot';report.mkdir(parents=True,exist_ok=True)
    html=static_screen(root,input_dir,cfg)
    (report/'screen-reconstruction.html').write_text(html,encoding='utf-8')
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        path=shutil.which('chromium') or shutil.which('chromium-browser')
        args={'headless':True,'args':['--no-sandbox']}
        if path:args['executable_path']=path
        browser=pw.chromium.launch(**args)
        page=browser.new_page(viewport={'width':1280,'height':410},device_scale_factor=1.5,java_script_enabled=False)
        page.route('**/*',lambda route:route.abort())
        page.set_content(html,wait_until='load')
        page.screenshot(path=str(assets/'pilot-100008-screen.png'),full_page=True)
        browser.close()
    dot=cfg['directory']/'flow.dot'
    subprocess.run(['dot','-Tpng','-Gdpi=115',str(dot),'-o',str(assets/'pilot-100008-flow.png')],check=True,capture_output=True,timeout=30)
    return {'screen':'static-source-reconstruction','executed_application':False,'images':2,'source_identity':'match','checksums':cfg['checksums']}


def add_pilot_questions(review):
    questions=[('Q-PILOT-STYLE','画面再構成','外部CSS未収録箇所の表示寸法を実画面で照合する。','現行画面とCSSを使用し、不足するBootstrapのコンテナ配置を近似する。'),
               ('Q-PILOT-BIND','数値変換エラー','直接送信による数値変換不可時の正確な文言を対象実行環境で確認する。','入力検証不成立とし、文言はフレームワークによる。'),
               ('Q-PILOT-DATA','本番データ取得先','本番ではどの職員データ取得サービスへ切り替えるか。','現行はメモリー上のサンプル職員データを使用する。')]
    for qid,target,question,assumption in questions:
        old=review.questions.get(qid,{})
        review.questions[qid]={'id':qid,'target':'職員番号入力 / '+target,'question':question,'assumption':assumption,
            'evidence':'src-dynamic/jsbrms-pilot/pilot.json','kind':'specification','active':True,
            'impact':'Pilotの表示・エラー文言・データ取得構成に影響する。','status':old.get('status','open'),'answer':old.get('answer','')}
    review.incomplete.append({'target':'職員番号入力Pilot','detail':'現行ソースの静的意味レビュー。実アプリ・本番DBの動作比較と全環境の画面完全一致は未検証。'})
