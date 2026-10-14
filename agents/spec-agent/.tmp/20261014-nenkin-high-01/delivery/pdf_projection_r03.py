"""Pure, insertion-only offline print projection. Never compose specification prose."""
import base64,hashlib,io,math,re
from collections import Counter
from html import escape
from html.parser import HTMLParser
from PIL import Image

PRINT_CSS='''
@page{size:A3 landscape;margin:12mm}
html,body{margin:0!important}body{font-family:"Meiryo","Yu Gothic",sans-serif;font-size:10pt;line-height:1.5;hyphens:none}
h1,h2,h3,h4{break-after:avoid}p{orphans:3;widows:3}
thead{display:table-header-group}tr{break-inside:avoid}
table[data-renderer-markdown]{width:100%;table-layout:auto}
table[data-renderer-markdown] col{width:auto!important}
table[data-renderer-markdown] th,table[data-renderer-markdown] td{overflow-wrap:normal;word-break:normal;vertical-align:top}
table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) th:first-child,
table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) td:first-child{white-space:nowrap;min-width:6em}
table[data-renderer-markdown] code{white-space:nowrap}
pre{white-space:pre-wrap;overflow-wrap:normal;word-break:normal;font-size:9pt;hyphens:none}
img{max-width:100%;height:auto}img[data-renderer-diagram]{max-height:240mm;object-fit:contain;break-inside:avoid}
.pdf-native-tile{break-before:page;break-inside:avoid;margin:0;padding:0}
.pdf-native-tile img{max-width:none;width:auto;height:auto}
.pdf-native-tile figcaption{font-size:9pt;margin:0 0 2mm}
'''
CONTENT_WIDTH_PX=math.floor((420-24)/25.4*96)
CONTENT_HEIGHT_PX=math.floor((297-24)/25.4*96)
MAX_PIXELS=40_000_000
def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(ok,message):
    if not ok:raise ValueError('HOLD: '+message)

class OuterHtml(HTMLParser):
    """Find structural insertion points without changing or reserializing HTML."""
    def __init__(self,text):
        super().__init__(convert_charrefs=False);self.text=text;self.offsets=[0]
        for line in text.splitlines(keepends=True):self.offsets.append(self.offsets[-1]+len(line))
        self.heads=0;self.bodies=0;self.head_close=None;self.body_close=None;self.stack=[];self.imageHashes=[]
    def offset(self):
        line,column=self.getpos();return self.offsets[line-1]+column
    def handle_starttag(self,tag,attrs):
        values={};tag=tag.casefold()
        for key,value in attrs:
            key=key.casefold();require(key not in values,'duplicate HTML attribute');values[key]=value or ''
        require(tag not in {'script','iframe','frame','frameset','object','embed','base','link'},'active/external HTML element '+tag)
        require(not any(k.startswith('on') for k in values),'HTML event attribute')
        if tag=='meta':require(values.get('http-equiv','').strip().casefold()!='refresh','HTML meta refresh')
        for key in ('src','srcset','poster','action','formaction','data','background','xlink:href'):
            if key not in values:continue
            require(tag=='img' and key=='src' and values[key].startswith('data:image/png;base64,'),'non-PNG or network URL attribute '+key)
        if tag=='img':
            require('src' in values,'image source missing')
            raw=base64.b64decode(values['src'].split(',',1)[1],validate=True);self.imageHashes.append(sha(raw))
        if tag=='head':self.heads+=1;require(self.heads==1 and self.bodies==0,'outer head cardinality/order')
        if tag=='body':self.bodies+=1;require(self.bodies==1 and self.head_close is not None,'outer body cardinality/order')
        if tag in {'html','head','body'}:self.stack.append(tag)
    def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs)
    def handle_endtag(self,tag):
        if tag in {'html','head','body'}:
            require(self.stack and self.stack[-1]==tag,'outer structural closing tag mismatch')
            self.stack.pop()
        if tag=='head':self.head_close=self.offset()
        if tag=='body':self.body_close=self.offset()
    def handle_pi(self,data):raise ValueError('HOLD: processing instruction HTML')
    def unknown_decl(self,data):raise ValueError('HOLD: unknown HTML declaration')
    def handle_decl(self,data):require(data.strip().casefold()=='doctype html','non-HTML doctype')

def inspect_html(text):
    require(text.startswith('<!doctype html><html '),'expected pinned renderer outer document')
    parser=OuterHtml(text);parser.feed(text);parser.close()
    require(parser.heads==parser.bodies==1 and not parser.stack and parser.body_close is not None,'complete renderer outer document required')
    return parser

def origins(length,limit,overlap):
    require(type(length) is int and length>0 and 0<=overlap<limit,'bounded tile origin parameters')
    return list(range(0,max(1,length-overlap),limit-overlap))

def native_tiles(pictures,inline_hashes=()):
    """Mechanical PNG pixel windows, including white/transparent regions. No dropped tiles."""
    figures=[];records=[]
    for picture in pictures:
        raw=picture['bytes'];require(sha(raw)==picture['sha256'],'native image SHA mismatch')
        source=Image.open(io.BytesIO(raw));require(source.format=='PNG','native asset is not PNG')
        require(source.width*source.height<=MAX_PIXELS,'native PNG exceeds bounded pixel budget');source.load();source=source.convert('RGBA')
        require((source.width,source.height)==(picture['width'],picture['height']),'native image dimensions drift')
        if picture['sha256'] in inline_hashes and source.width<=CONTENT_WIDTH_PX and source.height<=CONTENT_HEIGHT_PX:continue
        boxes=[(x,y,min(x+900,source.width),min(y+600,source.height)) for y in origins(source.height,600,60) for x in origins(source.width,900,60)]
        for number,box in enumerate(boxes,1):
            crop=source.crop(box);require(crop.tobytes()==source.crop(box).tobytes(),'exact tile pixel mismatch')
            buffer=io.BytesIO();crop.save(buffer,format='PNG');encoded=buffer.getvalue()
            record={'sourceId':picture['id'],'sourceSha256':picture['sha256'],'sourceDimensions':[source.width,source.height],'cropBox':list(box),'overlapPx':60,'tileOrdinal':number,'sourceTileCount':len(boxes),'tileSha256':sha(encoded),'rgbaSha256':sha(crop.tobytes()),'bytes':encoded}
            records.append(record)
            label=escape(picture['id'])+' '+str(number)+'/'+str(len(boxes))
            figures.append('<figure class="pdf-native-tile"><figcaption>'+label+'</figcaption><img src="data:image/png;base64,'+base64.b64encode(encoded).decode('ascii')+'" width="'+str(crop.width)+'" height="'+str(crop.height)+'"></figure>')
        require(boxes[0][:2]==(0,0) and max(b[2] for b in boxes)==source.width and max(b[3] for b in boxes)==source.height,'native tile coverage extent')
    return ''.join(figures),records

def project_html(raw,pictures):
    text=raw.decode('utf-8');parser=inspect_html(text)
    ids=[p['id'] for p in pictures];require(len(ids)==len(set(ids)),'duplicate native image ID')
    # Every inline PNG stays byte-exact in canonical HTML. The render manifest also
    # supplies independent native layout PNGs, which may not be inline in the HTML.
    known={p['sha256'] for p in pictures};require(set(parser.imageHashes).issubset(known),'unbound inline native PNG')
    required=Counter(p['sha256'] for p in pictures if p.get('kind')=='diagram')
    actual=Counter(parser.imageHashes)
    require(all(actual[value]>=count for value,count in required.items()),'canonical inline diagram multiplicity mismatch')
    annex,tiles=native_tiles(pictures,parser.imageHashes)
    style='<style data-spec-agent-pdf="1">'+PRINT_CSS+'</style>'
    insertions=[(parser.head_close,style),(parser.body_close,annex)]
    projected=text
    for at,value in sorted(insertions,reverse=True):projected=projected[:at]+value+projected[at:]
    reverse=projected
    for at,value in sorted(insertions):
        # Earlier insertion shifts subsequent positions; removing in source order
        # restores the original offset for the next removal.
        require(reverse[at:at+len(value)]==value,'projection reverse literal mismatch')
        reverse=reverse[:at]+reverse[at+len(value):]
    require(reverse.encode('utf-8')==raw,'projection modified canonical HTML bytes')
    return projected,{'canonicalHtmlSha256':sha(raw),'printProjectionSha256':sha(projected.encode()),'cssSha256':sha(PRINT_CSS.encode()),'onlyInsertions':True,'inverseRestoresCanonicalHtmlBytes':True,'tableRowsDropped':0,'canonicalTextOrCellsReauthored':False,'paper':'A3 landscape','marginMm':12,'contentWidthCssPx':CONTENT_WIDTH_PX,'contentHeightCssPx':CONTENT_HEIGHT_PX,'nativeTiles':[{k:v for k,v in r.items() if k!='bytes'} for r in tiles],'nativeAssetIdsRetained':[p['id'] for p in pictures],'canonicalInlineNativeImageCount':len(parser.imageHashes),'allNativeAssetsEitherInlineOrAnnexed':True},tiles

GEOMETRY_JS=r'''() => {
 const viewport=document.documentElement.clientWidth;const issues=[];
 for(const el of document.querySelectorAll('table,pre,input,select,textarea')) {
  const r=el.getBoundingClientRect();if(r.width>viewport+1||r.right>viewport+1||r.left<-1)issues.push({kind:'outside-print-width',tag:el.tagName,width:r.width,right:r.right});
 }
 const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let node;
 while(node=walker.nextNode()) {
  if(node.parentElement.closest('style,script,.pdf-native-tile'))continue;
  const matcher=/[A-Za-z0-9_]+(?:[.\-][A-Za-z0-9_]+)*/g;let match;
  while(match=matcher.exec(node.data)) {
   const ys=[];for(let i=match.index;i<match.index+match[0].length;i++) {
    const range=document.createRange();range.setStart(node,i);range.setEnd(node,i+1);const r=range.getBoundingClientRect();
    if(!Number.isFinite(r.left)||!Number.isFinite(r.top)||r.width<=0||r.height<=0||r.right>viewport+1||r.left<-1)issues.push({kind:'token-clipped-or-invisible',token:match[0]});ys.push(Math.round(r.top));
   }
   if(new Set(ys).size>1)issues.push({kind:'token-internal-wrap',token:match[0]});
  }
 }
 return {viewport,issues,measuredBy:'trusted DOM geometry only; source JS disabled'};
}'''

def text_coverage(extracted,model):
    # Whitespace-only equivalence accounts for PDF line/page layout. All Unicode
    # characters, punctuation, source IDs, leading zeros and era tokens remain.
    normalize=lambda value:''.join(value.split())
    expected=[model['title'],*[d['heading'] for d in model['sourceMetadata'].get('sections',model['sourceMetadata'].get('sheets',[]))],*model['visibleCoverage']]
    expected=[v for v in expected if normalize(v)]
    normalized=normalize(extracted);counts=Counter(normalize(v) for v in expected)
    missing=[v for v in expected if normalize(v) not in normalized]
    multiplicity=[{'normalizedLiteral':v,'expectedMinimum':count,'observedNonoverlappingOccurrences':normalized.count(v)} for v,count in counts.items() if normalized.count(v)<count]
    return {'expectedCount':len(expected),'missing':missing,'missingCount':len(missing),'multiplicityFailures':multiplicity,'normalization':'WHITESPACE_ONLY','visualQualified':False}

def canonical_text_order(extracted,strings):
    normalized=''.join(extracted.split());cursor=0;missing=[]
    for ordinal,value in enumerate(strings):
        value=''.join(value.split())
        if not value:continue
        found=normalized.find(value,cursor)
        if found<0:missing.append({'canonicalDomOrdinal':ordinal,'literal':value})
        else:cursor=found+len(value)
    return {'orderedStringsChecked':len(strings),'orderFailures':missing,'visualQualified':False,'limitation':'Normalized text sequence is a conservative extraction check; it does not prove visual cell alignment.'}
