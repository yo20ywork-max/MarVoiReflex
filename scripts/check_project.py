"""Offline checks for published content; does not start models or touch user data."""
from pathlib import Path
import collections,csv,json,os,re,sys,tempfile,unittest,zipfile
ROOT=Path(__file__).resolve().parent.parent
errors=[]
def check(condition,message):
    if not condition:errors.append(message)

cases=list(csv.DictReader((ROOT/'docs/testing/50-cases.csv').open(encoding='utf-8-sig')))
check(len(cases)==50,'Expected 50 planned cases')
check(collections.Counter(x['category'] for x in cases)=={'基本工具操作':10,'行銷素材整理':20,'多步驟任務':10,'安全與異常':10},'Case category totals differ')
check(len({x['id'] for x in cases})==50,'Duplicate case IDs')
check(all(x['status']=='待執行' and not x['actual'] for x in cases),'Unexecuted cases must not claim results')
req=list(csv.DictReader((ROOT/'docs/requirements.csv').open(encoding='utf-8-sig')))
check(len(req)==60 and len({x['id'] for x in req})==60,'Expected 60 distinct research requirements')
for row in req:check((ROOT/row['document']).is_file(),'Requirement missing document: '+row['id'])

links=0
for p in [ROOT/'README.md',*ROOT.rglob('docs/**/*.md')]:
    content=p.read_text(encoding='utf-8')
    check(not any(ord(c)<32 and c not in '\r\n\t' for c in content),'Unexpected control character: '+str(p.relative_to(ROOT)))
    for raw in re.findall(r'\]\(([^)]+)\)',content):
        raw=raw.strip('<>').split('#')[0]
        if not raw or '://' in raw or raw.startswith('mailto:'):continue
        links+=1
        check((p.parent/raw).is_file() or (p.parent/raw).is_dir(),f'Broken local link in {p.relative_to(ROOT)}: {raw}')

pyfiles=list((ROOT/'src').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))
for p in pyfiles:
    try:compile(p.read_text(encoding='utf-8'),str(p),'exec')
    except Exception as e:errors.append(f'Python syntax: {p.name}: {e}')
sys.path.insert(0,str(ROOT/'src'))
import app_paths
old=os.environ.pop('MARVOI_ASSETS_ROOT',None)
old_data=os.environ.pop('CROSSGEN_DATA_DIR',None)
try:
    check(app_paths.web_root()==ROOT/'web/voice','Source must serve its own web files')
    check(app_paths.data_root()==ROOT/'.local-data','Source data must be isolated from delivered App data')
    os.environ['MARVOI_ASSETS_ROOT']=str(ROOT/'external-runtime-example')
    check(app_paths.bundle_root()==(ROOT/'external-runtime-example').resolve(),'Runtime override is not respected')
    check(app_paths.web_root()==ROOT/'web/voice','External runtime must not override source UI')
finally:
    if old is None:os.environ.pop('MARVOI_ASSETS_ROOT',None)
    else:os.environ['MARVOI_ASSETS_ROOT']=old
    if old_data is not None:os.environ['CROSSGEN_DATA_DIR']=old_data
html=(ROOT/'web/voice/index.html').read_text(encoding='utf-8')
for value in ['__SESSION_TOKEN__','__NATIVE_SHELL__','data-runtime="live"','src="/live.js"','Noto Sans TC']:
    check(value in html,'Missing live UI value: '+value)
for name in ['chatSend','taskSend','import','demo','callToggle','chatVoice','taskVoice']:
    check('id="'+name+'" disabled' in html,'Control not disabled until real backend attaches: '+name)
check("web=web_root()" in (ROOT/'src/main.py').read_text(encoding='utf-8'),'Main source does not use local web root')
check('C:\\Users\\User' not in html and 'D:\\GhostReflex' not in html,'Published UI contains machine paths')
manifest=json.loads((ROOT/'runtime/manifest.json').read_text(encoding='utf-8'))
check(manifest['CPU_only'] is True and manifest['llama_cpp']['gpu_layers']==0,'CPU manifest changed')
check(not (ROOT/'assets').exists(),'Third-party runtime assets must not be committed')
deck=ROOT/'docs/presentation/MarVoiReflex-Revision-20261031.pptx'
if deck.exists():
    with zipfile.ZipFile(deck) as z:
        slides=[n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)]
        check(len(slides)==24,'Expected 24 deck slides')
        check(z.testzip() is None,'PPTX CRC failed')
else:errors.append('Revised deck is missing')
summary={'pass':not errors,'planned_cases':len(cases),'research_requirements':len(req),'python_sources_checked':len(pyfiles),'local_links_checked':links,'models_started':False,'physical_8GB_verified':False,'errors':errors}
print(json.dumps(summary,ensure_ascii=False,indent=2))
raise SystemExit(0 if not errors else 1)
