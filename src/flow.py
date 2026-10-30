from pathlib import Path
from datetime import date,timedelta
import hashlib,json,os,re,stat,time,secrets
import requests
from intent import Planner
from semantics import analyze, constraints as compile_constraints
from app_paths import data_root,bridge_url,fixed_move_command
ROOT=data_root()
ACTIVE=ROOT/'workspace'
MAT=ACTIVE/'materials'
IMAGE={'.png','.jpg','.jpeg','.webp'};TEXT={'.txt','.md'}
class ScopeError(PermissionError):pass
class MCPError(RuntimeError):pass
class IntentError(ValueError):pass
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def filename_date(name):
 m=re.search(r'(?<!\d)(20\d{6})(?!\d)',name)
 if not m:return None
 try:return date(int(m[1][:4]),int(m[1][4:6]),int(m[1][6:]))
 except ValueError:return None
def paths_in(text):
 # Prefer quoted literal paths, including spaces; never drop ../ traversal.
 found=[];masked=text
 def slash_date(value):
  if not re.fullmatch(r'(?:20\d{2}/)?\d{1,2}/\d{1,2}',value):return False
  try:
   parts=[int(n) for n in value.split('/')];date(*(parts if len(parts)==3 else [2000]+parts));return True
  except ValueError:return False
 for m in re.finditer(r'[「“`"]([^」”`"]+)[」”`"]',text):
  value=m[1]
  if slash_date(value):masked=masked.replace(m[0],' ');continue
  if '/' in value or '\\' in value:found.append(value);masked=masked.replace(m[0],' ')
 masked=re.sub(r'(?<![\d/\\])(?:20\d{2}/)?\d{1,2}/\d{1,2}(?![\d/\\])',lambda m:' ' if slash_date(m[0]) else m[0],masked)
 for m in re.finditer(r'(?:[A-Za-z]:[\\/]|[\w\u4e00-\u9fff.-]+[\\/])[^\s，。；;「」“”`"<>]*',masked):found.append(m[0])
 return [p.rstrip('，。；,;？?）)') for p in found if not re.match(r'^\.(?:png|jpg|jpeg|txt|md)[/|,]',p,re.I)]
def explicit_range(text,clock):
 token=r'(?:20\d{2}[年/-])?\d{1,2}[月/-]\d{1,2}日?'
 match=re.search(r'('+token+r')\s*(?:起)?\s*(?:至|到|~|～|–|—)\s*('+token+r')',text)
 if not match:return None
 def parse(s,year):
  parts=[int(x) for x in re.findall(r'\d+',s)]
  return date(*(parts if len(parts)==3 else [year]+parts))
 first=parse(match[1],clock.year);last=parse(match[2],first.year)
 if last<first and not re.match(r'20\d{2}',match[2]):last=date(last.year+1,last.month,last.day)
 if last<first:raise IntentError('日期起點晚於終點')
 return first,last
def mentioned_names(text,assets):
 lower=text.casefold();hits=[]
 for a in assets:
  start=0
  while (at:=lower.find(a['name'].casefold(),start))>=0:
   hits.append((at,at+len(a['name']),a));start=at+len(a['name'])
 return list({h[2]['name']:h[2] for h in hits if not any(k[0]<=h[0] and k[1]>=h[1] and k[1]-k[0]>h[1]-h[0] for k in hits)}.values())
def time_text(text):
 text=re.sub(r'[「“"]([^」”"]+)[」”"]',lambda m:m[1] if m[1] in ['本週','這週','本周','圖片','文案','文字','照片','所有','全部'] else '',text)
 return re.sub(r'[^\s，。；「」“”`]+\.(?:png|jpg|jpeg|txt|md)\b','',text,flags=re.I)

def request_constraints(user):
 # Compile only explicit task wording and lossless literals, never test-oracle answers.
 semantic=time_text(user)
 semantic=re.sub(r'(?:(?:先)?(?:不要|不用|禁止|不准|不必|不需要|無需)|先不|先別|請別)[^，。；\n]*','',semantic)
 constraints={}
 if re.search(r'讀取|逐字|讀一下|讀出|閱讀.*內容',semantic):constraints['actions']=['read']
 elif re.search(r'整理|分類|搬移|移動|搬到|移到|放到|放入|收進|歸檔|歸類|分開|預覽',semantic):constraints['actions']=['preview','organize','check']
 elif re.search(r'搜尋|找出|找一下|檔名.*(?:含|包含)|名稱.*(?:含|包含)',semantic):constraints['actions']=['search']
 elif re.search(r'列出|列給我|列一下|總數|清單|有哪些|有什麼|查看|看看|顯示|名稱.*數量',semantic):constraints['actions']=['list']
 quoted=re.findall(r'[「“"]([^」”"]+)[」”"]',user)
 named=any(re.search(r'\.(?:png|jpg|jpeg|webp|txt|md)(?:$|[」”"\s])',x,re.I) for x in quoted)
 literals=[x for x in quoted if '/' not in x and '\\' not in x and x not in ['本週','這週','本周','圖片','文案','所有','全部'] and not re.search(r'\.(?:png|jpg|jpeg|webp|txt|md)$',x,re.I)]
 if named:constraints['keyword_choices']=['']
 elif len(literals)==1:constraints['keyword_choices']=literals
 return constraints
class Flow:
 def __init__(self,out,clock=date(2026,10,30),seed=42,fault=None):
  self.out=out;out.parent.mkdir(parents=True,exist_ok=True);self.planner=Planner(out.with_suffix('.requests.jsonl'),seed,clock)
  self.clock=clock;self.history=[];self.events=[];self.pending=None;self.plans=[];self.intent_attempts=[];self.fault=fault;self.fault_fired=False;self.move_count=0;self.mutations=[];self.session_nonce=secrets.token_hex(12);self.allowed_commands=set();self.allowed_pids=set()
  state=json.loads((ROOT/'bridge-state.json').read_text(encoding='utf-8'));self.headers={'Authorization':'Bearer '+state['token']}
 def checked(self,value):
  if MAT.exists() and MAT.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:raise ScopeError('授權根資料夾不可是連結')
  p=Path(value);p=(p if p.is_absolute() else ACTIVE/p).resolve()
  if not p.is_relative_to(MAT.resolve()):raise ScopeError('只允許指定的 materials 資料夾')
  current=MAT
  for part in p.relative_to(MAT.resolve()).parts:
   current=current/part
   if current.exists() and current.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:raise ScopeError('不允許連結或重解析路徑')
  return p
 def rel(self,p):return p.relative_to(ACTIVE).as_posix()
 def source_folder(self,user,action):
  for value in paths_in(user):
   p=self.checked(value)
   if action!='list' and self.rel(p).startswith('materials/已整理'):continue
   if p.suffix.lower() in IMAGE|TEXT:p=p.parent
   return self.rel(p)
  return 'materials'
 def call(self,name,args,rollback=False):
  if name not in ['list_directory','read_file','get_file_info','start_search','get_more_search_results','stop_search','start_process','read_process_output']:raise ScopeError('未授權工具')
  if name=='start_process' and (args.get('command') not in self.allowed_commands or args.get('shell')!='cmd.exe'):raise ScopeError('只允許固定搬移器，不接受模型終端指令')
  if name=='read_process_output' and args.get('pid') not in self.allowed_pids:raise ScopeError('不是本次搬移器的程序')
  for key in ['path','source','destination']:
   if key in args:self.checked(args[key])
  record={'name':name,'arguments':args,'backend_called':False,'rollback':rollback,'time':time.time()}
  if name=='move_file' and not rollback:
   self.move_count+=1
   if self.fault=='second_move' and self.move_count==2 and not self.fault_fired:
    self.fault_fired=True;record.update(injected=True,error='Simulated second move failure');self.events.append(record);raise MCPError(record['error'])
  start=time.perf_counter()
  wire=requests.post(bridge_url()+'/call',headers=self.headers,json={'name':name,'arguments':args,'label':self.out.name},timeout=40).json()
  record.update(backend_called=True,wire_index=wire.get('index'),elapsed_s=time.perf_counter()-start,result=wire.get('result'),error=wire.get('error'));self.events.append(record)
  if wire.get('error'):raise MCPError(wire['error'])
  result=wire['result'];text='\n'.join(c.get('text','') for c in result.get('content',[]) if c.get('type')=='text')
  return {'text':text,'is_error':bool(result.get('isError')),'raw':result}
 def info(self,p):
  result=self.call('get_file_info',{'path':self.rel(p)})
  if result['is_error']:
   if re.search(r'ENOENT|does not exist|not found',result['text'],re.I):return {'exists':False}
   raise MCPError(result['text'])
  return {'exists':True,'is_file':bool(re.search(r'isFile:\s*true',result['text'])),'text':result['text']}
 def catalog(self,folder='materials'):
  p=self.checked(folder);result=self.call('list_directory',{'path':self.rel(p),'depth':1})
  if result['is_error']:raise MCPError(result['text'])
  if '[NOT_FOUND]' in result['text']:raise FileNotFoundError('指定資料夾不存在：'+folder)
  if '[DENIED]' in result['text']:raise ScopeError('資料夾不可存取')
  assets=[]
  for name in re.findall(r'^\[FILE\] (.+)$',result['text'],re.M):
   f=self.checked(self.rel(p/name));extension=f.suffix.lower()
   assets.append({'name':name,'path':self.rel(f),'type':'image' if extension in IMAGE else 'text' if extension in TEXT else 'other','date':filename_date(name),'sha256':digest(f)})
  return sorted(assets,key=lambda a:a['name'])
 def validate_intent(self,r,user):
  if not r:raise IntentError('模型沒有產生合法意圖')
  for value in paths_in(user):self.checked(value)
  spec=analyze(user,self.clock,paths_in(user))
  if spec['error']:raise IntentError(spec['error'])
  if r['action'] in ['chat','refuse']:raise IntentError('任務入口只能回傳檔案任務或詢問條件，不能切去聊天或猜測越界')
  if spec['actions'] and r['action'] not in spec['actions']:raise IntentError('動作不符合使用者的執行目的')
  if r['action']!='clarify':self.validate_filters(r,user)

 def validate_filters(self,r,user,check_keyword=True):
  spec=analyze(user,self.clock,paths_in(user))
  if spec['error']:raise IntentError(spec['error'])
  if check_keyword and r['keyword'] and r['keyword'] not in user:raise IntentError('活動名稱必須原樣取自使用者文字，不能改字')
  if r['kind']!=(spec['kind'] or 'all'):raise IntentError('檔案類型不符，應為'+(spec['kind'] or 'all'))
  if r['date_scope']!=spec['date_scope'] or r['start']!=spec['start'] or r['end']!=spec['end']:raise IntentError('日期條件不符：'+json.dumps({k:spec[k] for k in ['date_scope','start','end']},ensure_ascii=False))

 def query(self,r,user,assets,verify_only=False):
  self.validate_filters(r,user)
  spec=analyze(user,self.clock,paths_in(user));named=mentioned_names(user,assets)
  if named:selected=named
  else:
   selected=assets
   choices=spec['keyword_choices']
   if choices and choices!=[''] and r['keyword'] not in choices:raise IntentError('活動名稱沒有保留使用者原文')
   if r['keyword']:
    if not verify_only:
     result=self.call('start_search',{'path':self.source_folder(user,r['action']),'pattern':r['keyword'],'searchType':'files','literalSearch':True,'earlyTermination':False,'maxResults':100})
     if result['is_error']:raise MCPError(result['text'])
     match=re.search(r'\bsearch_[\w-]+',result['text'])
     if match:
      try:
       for _ in range(20):
        page=self.call('get_more_search_results',{'sessionId':match[0],'offset':0,'length':100})
        if 'COMPLETED' in page['text']:break
        time.sleep(.05)
       else:raise MCPError('搜尋未在上限內完成')
      finally:self.call('stop_search',{'sessionId':match[0]})
    contains=r['action']=='search' or bool(re.search(r'(?:檔名|名稱|名字).*?(?:含|包含|有|帶|相符)',spec['semantic']))
    if contains:selected=[a for a in selected if r['keyword'] in a['name']]
    else:
     def campaign(a):
      m=re.match(r'(.+?)[_ -]+20\d{6}',a['name']);return m[1] if m else a['name'].rsplit('.',1)[0]
     selected=[a for a in selected if campaign(a)==r['keyword']]
  if r['kind']!='all':selected=[a for a in selected if a['type']==('image' if r['kind']=='images' else 'text')]
  elif spec['type_explicit']:selected=[a for a in selected if a['type'] in spec['explicit_type_set']]
  if r['date_scope']!='any':
   lo,hi=(self.clock-timedelta(days=self.clock.weekday()),self.clock+timedelta(days=6-self.clock.weekday())) if r['date_scope']=='this_week' else (date.fromisoformat(r['start']),date.fromisoformat(r['end']))
   selected=[a for a in selected if a['date'] is not None and lo<=a['date']<=hi]
  return selected

 def propose(self,r,user,assets):
  selected=self.query(r,user,assets)
  if not selected:return {'status':'empty','text':'找不到符合條件的素材，共0個，沒有修改任何檔案。'}
  for m in re.finditer(r'(?:整理到|移到|移動到|搬到|放到|放入|收進|分類到)\s*([^，。；\n]+)',user):
   for value in paths_in(m[1]):
    target=self.rel(self.checked(value)).rstrip('/')
    prefix=re.split(r'[，。；\n]',user[:m.start()])[-1]
    bound=mentioned_names(prefix,selected) or selected
    destinations=['materials/已整理/'+('圖片' if a['type']=='image' else '文案')+'/'+a['name'] for a in bound]
    allowed=set(destinations)|{'materials/已整理'}
    if all(a['type']=='image' for a in bound) or (not mentioned_names(prefix,selected) and any(a['type']=='image' for a in selected)):allowed.add('materials/已整理/圖片')
    if all(a['type']=='text' for a in bound) or (not mentioned_names(prefix,selected) and any(a['type']=='text' for a in selected)):allowed.add('materials/已整理/文案')
    if target not in allowed:raise IntentError('本原型只整理到預設的已整理/圖片與已整理/文案，指定目的地或類型不符，請確認')
  items=[];collisions=[]
  for a in selected:
   if a['type'] not in ['image','text']:raise IntentError('這個版本只支援圖片與文字素材，請先確認其他類型如何分類')
   dest='materials/已整理/'+('圖片' if a['type']=='image' else '文案')+'/'+a['name']
   if self.info(self.checked(dest))['exists']:collisions.append(dest)
   items.append({'source':a['path'],'destination':dest,'sha256':a['sha256'],'name':a['name']})
  if collisions:
   self.pending=None;return {'status':'collision','text':'目的地已存在同名檔：\n'+'\n'.join(collisions)+'\n已停止，不覆寫、不改名。請先取消或手動處理同名檔，再重新預覽。'}
  goal={'user':user,'intent':dict(r),'folder':self.source_folder(user,r['action'])};nonce=len(self.plans)+1;encoded=json.dumps({'items':items,'nonce':nonce,'session':self.session_nonce,'goal':goal},ensure_ascii=False,sort_keys=True);pid=hashlib.sha256(encoded.encode()).hexdigest()[:16]
  plan={'id':pid,'items':items,'nonce':nonce,'state':'pending','intent':dict(r),'goal':goal}
  self.pending=plan;self.plans.append(plan)
  text='分類預覽（尚未修改）：\n| 原始路徑 | 目的路徑 |\n|---|---|\n'+'\n'.join('| '+a['source']+' | '+a['destination']+' |' for a in items)+f'\n共{len(items)}個檔案。計畫ID：{pid}。請確認後才會建立資料夾、移動並逐檔驗證。'
  return {'status':'preview','text':text,'plan_id':pid,'selected':[a['name'] for a in items]}
 def request(self,user):
  if self.pending:self.pending['state']='superseded';self.pending=None
  self.history.append({'role':'user','content':user});feedback=None;result=None
  spec=analyze(user,self.clock,paths_in(user));self.last_semantic_contract=spec
  # This entrypoint is task-only. Missing/unsupported conditions never fall back to chat.
  try:
   for path in paths_in(user):self.checked(path)
  except ScopeError as error:
   result={'status':'refused','mode':'task','text':'超出授權範圍，不能執行：'+str(error)};self.history.append({'role':'assistant','content':result['text']});return result
  if not spec['resource'] or spec['error']:
   result={'status':'clarify','mode':'task','text':spec['error'] or '目前是任務模式，請提供素材資料夾與要做的操作。'};self.history.append({'role':'assistant','content':result['text']});return result
  for attempt in range(2):
   constraints=compile_constraints(spec)
   r=self.planner.ask([{'role':'user','content':user}],feedback,constraints);entry={'attempt':attempt+1,'raw':r,'validation_error':None,'controller_constraints':constraints,'semantic_contract':spec};self.intent_attempts.append(entry)
   try:
    self.validate_intent(r,user)
    if r['action']=='clarify':
     reply=r['reply'] or '請提供素材路徑與整理條件。'
     if paths_in(user) and any(x in reply for x in ['已完成','已整理','已移動']):raise IntentError('沒有執行紀錄，不可宣稱已完成檔案操作')
     result={'status':r['action'],'text':reply}
    elif r['action']=='refuse':result={'status':'refused','text':'這個操作超出授權的 materials 範圍，不能執行。'}
    elif r['action']=='list':
     folder=self.source_folder(user,r['action']);assets=self.catalog(folder);result={'status':'listed','text':'\n'.join(a['name'] for a in assets)+f'\n總數：{len(assets)}個檔案。','selected':[a['name'] for a in assets],'grounded_folder':folder}
    else:
     assets=self.catalog(self.source_folder(user,r['action']))
     if r['action']=='read':
      named=mentioned_names(user,assets)
      if len(named)!=1:raise IntentError('讀取需要唯一且確實存在的文字檔名，請保留使用者原文')
      if named[0]['type']!='text':raise IntentError('此功能只讀文字素材')
      data=self.call('read_file',{'path':named[0]['path']})
      if data['is_error']:raise MCPError(data['text'])
      result={'status':'read','text':data['text'],'selected':[named[0]['name']]}
     elif r['action']=='search':
      selected=self.query(r,user,assets);result={'status':'searched','text':'\n'.join(a['name'] for a in selected)+f'\n總數：{len(selected)}個符合條件的檔案。','selected':[a['name'] for a in selected]}
     else:result=self.propose(r,user,assets)
    break
   except ScopeError as error:entry['validation_error']=str(error);result={'status':'refused','text':'超出授權範圍，不能執行：'+str(error)};break
   except FileNotFoundError as error:result={'status':'missing','text':str(error)+'，沒有建立或修改檔案。'};break
   except (IntentError,ValueError) as error:
    entry['validation_error']=str(error);feedback=str(error)
    if attempt==1:result={'status':'clarify','text':'尚未執行，請確認條件：'+str(error)}
   except Exception as error:result={'status':'error','text':'操作未完成：'+str(error),'error':repr(error)};break
  result['mode']='task';self.history.append({'role':'assistant','content':result['text']});return result
 def cancel(self,plan_id):
  if self.pending and self.pending['id']==plan_id:self.pending['state']='cancelled';self.pending=None
  return {'status':'cancelled','text':'已取消，沒有建立資料夾或移動檔案。'}
 def confirm(self,plan_id):
  if not self.pending or self.pending['id']!=plan_id or self.pending['state']!='pending':return {'status':'rejected','text':'確認已失效，請重新預覽。'}
  plan=self.pending;items=plan['items'];verified=[];self.last_receipt={}
  check=json.dumps({'items':items,'nonce':plan['nonce'],'session':self.session_nonce,'goal':plan['goal']},ensure_ascii=False,sort_keys=True)
  if hashlib.sha256(check.encode()).hexdigest()[:16]!=plan_id:
   plan['state']='invalid';self.pending=None;return {'status':'rejected','text':'預覽計畫已改變，請重新預覽。'}
  try:
   goal=plan['goal'];current=self.query(goal['intent'],goal['user'],self.catalog(goal['folder']),verify_only=True)
   expected=[{'source':a['path'],'destination':'materials/已整理/'+('圖片' if a['type']=='image' else '文案')+'/'+a['name'],'sha256':a['sha256'],'name':a['name']} for a in current]
   if expected!=items:raise IntentError('來源清單、類型或日期條件與預覽不一致，請重新預覽')
   for a in items:
    src,dst=self.checked(a['source']),self.checked(a['destination'])
    if not self.info(src).get('is_file') or not src.is_file() or digest(src)!=a['sha256']:raise IntentError('來源已改變，請重新預覽')
    if self.info(dst)['exists']:raise IntentError('預覽後出現同名檔，已停止')
   op_id=secrets.token_hex(12);op_path=ROOT/'ops'/(op_id+'.json');op_path.parent.mkdir(exist_ok=True)
   data={'operation_id':op_id,'plan_id':plan_id,'items':items,'inject':self.fault}
   with op_path.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False);f.flush();os.fsync(f.fileno())
   command=fixed_move_command(op_path)
   self.allowed_commands.add(command)
   process=self.call('start_process',{'command':command,'timeout_ms':1000,'shell':'cmd.exe'})
   if process['is_error']:raise MCPError(process['text'])
   pid=re.search(r'PID\s+(\d+)',process['text']);receipt=op_path.with_suffix('.result.json')
   if pid:self.allowed_pids.add(int(pid[1]))
   deadline=time.monotonic()+30
   while time.monotonic()<deadline:
    if receipt.exists():break
    if pid:self.call('read_process_output',{'pid':int(pid[1]),'timeout_ms':1000})
    time.sleep(.1)
   else:raise MCPError('搬移器結果未確認，停止後續操作，不宣稱成功')
   outcome=json.loads(receipt.read_text(encoding='utf-8'));self.last_receipt=outcome
   for parent in outcome['created_dirs']:self.mutations.append({'name':'create_directory','path':parent,'plan_id':plan_id,'confirmed':True})
   for a in items:
    if a['destination'] in outcome['moved']:self.mutations.append({**a,'operation':'move_file','plan_id':plan_id,'confirmed':True,'atomic_no_replace':True})
   if not outcome['success']:
    plan['state']='failed';self.pending=None
    return {'status':'failed','text':'操作未完成，已停止並嘗試還原；可能保留空資料夾。','error':outcome.get('error'),'rollback':outcome['rollback'],'receipt':outcome}
   for a in items:
    dst=self.checked(a['destination']);info=self.info(dst)
    if not info.get('is_file') or self.checked(a['source']).exists() or digest(dst)!=a['sha256']:raise MCPError('檔案驗證未通過')
    verified.append(a['destination'])
   plan['state']='completed';self.pending=None
   return {'status':'completed','text':f'已完成移動{len(items)}個檔案，逐檔驗證{len(verified)}個全部通過。\n'+'\n'.join(verified),'verified':verified,'moved':len(items),'receipt':outcome}
  except Exception as error:
   plan['state']='failed';self.pending=None
   return {'status':'failed','text':'操作未完成或驗證未完成，已停止：'+str(error),'error':repr(error),'rollback':getattr(self,'last_receipt',{}).get('rollback',[])}
