from pathlib import Path
from app_paths import model_url
import copy,json,time,requests
ROOT=Path(__file__).resolve().parent
SYSTEM='''你是小型商家的素材意圖解析器。使用台灣繁體中文。請依JSON結構輸出。
先判斷最終目的，再判斷前置步驟。「整理到、分類、搬移」的最終目的是organize；「只預覽、先給對照表」用preview。即使要求「先列出原始與目的路徑」，也不是list。list只用在單純列出資料夾檔案。
action：一般問答、計算、活動點子、整理對話中已提供的資料用chat；缺少整理路徑或條件用clarify；列出資料夾用list；依條件找檔案用search；讀取文字檔用read；只展示分類對照用preview；要求整理後等待確認用organize；檢查是否同名用check；越過materials範圍的實際檔案操作用refuse。
一般聊天所需資訊已在對話中時直接回答，不查檔案，也不重問已給過的資訊。chat與clarify把回覆寫在reply；其他動作reply留空，實際結果由程式回報。沒有執行記錄不可說已完成操作。
folder只填使用者指定的資料夾相對路徑；沒有另指定就填materials。不要把檔名翻成英文或轉換繁簡體。
keyword只填使用者原文的活動名稱或檔名搜尋文字。明確指定檔案名稱時keyword留空。kind依要求填images、texts或all；同時包含圖片與文案用all。
date_scope：未限制日期用any，指定本週用this_week，指定起迄日期用range並填YYYY-MM-DD的start/end。其他情形start/end留空。不要自行添加日期限制。
聊天遵守指定的句數、字數與預算；有預算上限時說清楚獎勵數量與成本上限。姓名、店名、商品與日期依原文保留。計算節省比例時以原本耗時為分母，節省量是原本耗時減去新耗時。'''
SYSTEM='''你是已授權的中文素材意圖解析器，只判斷檔案任務，不自行執行。輸出固定JSON欄位action、folder、keyword、kind、date_scope、start、end、reply。
判別例子（只示意語意）：「看看資料夾全部名稱和數量，別修改」選list；「讀一下說明文件內容」選read；「先列出移動前後對照，等確認才分類」選preview；「整理到分類資料夾，先給預覽」選organize；「列出還沒建立的子資料夾」仍選list，由工具確認它是否存在。
先看最終目的：「整理到、分類、移動、搬到」用organize；只要操作對照或只預覽用preview。要求「先列出原始與目的路徑」也是preview或organize，不能誤選list。list限只查看資料夾清單；search按條件找檔；read讀文字檔；check查同名衝突；缺少必要條件用clarify。
materials與其子資料夾已授權讀取，即使子資料夾不存在也在授權範圍內，應用list實際查詢。只對materials以外的實際檔案操作用refuse。沒有工具結果不能猜測檔案存在或不存在。
folder只用使用者指定的資料夾路徑，預設materials。keyword只用使用者原文中的活動名稱或搜尋文字，不翻譯、不轉換繁簡；已指定完整檔名時可留空。kind填images、texts或all，同時包含圖片與文案用all。
使用者說本週或這週時，date_scope填this_week；明確起迄日期填range並在start/end填YYYY-MM-DD；未限制日期填any且start/end留空。不能漏掉或自行增加日期條件。
reply只在clarify/refuse填簡短說明，其他動作留空。不要宣稱已完成任何操作。'''
SCHEMA={'type':'object','properties':{
 'action':{'type':'string','enum':['clarify','list','search','read','preview','organize','check','refuse']},
 'folder':{'type':'string','maxLength':256},'keyword':{'type':'string','maxLength':100},
 'kind':{'type':'string','enum':['all','images','texts']},
 'date_scope':{'type':'string','enum':['any','this_week','range']},
 'start':{'type':'string','maxLength':10},'end':{'type':'string','maxLength':10},
 'reply':{'type':'string','maxLength':2400}},
 'required':['action','folder','keyword','kind','date_scope','start','end','reply'],'additionalProperties':False}
class Planner:
 def __init__(self,path,seed=42,clock=None):self.path=path;self.seed=seed;self.clock=clock;self.records=[]
 def ask(self,history,feedback=None,constraints=None):
  context=SYSTEM+('\n本次作業日期：'+str(self.clock)+'；未寫年份的日期以此作業日期為準。' if self.clock else '')
  messages=[{'role':'system','content':context}]+history
  if feedback:
   if self.records and self.records[-1].get('parsed'):messages.append({'role':'assistant','content':json.dumps(self.records[-1]['parsed'],ensure_ascii=False)})
   messages += [{'role':'user','content':'請修正上一個意圖解析：'+feedback+'。只修正條件，不要執行或編造結果。'}]
  schema=copy.deepcopy(SCHEMA)
  if constraints:
   if constraints.get('actions'):schema['properties']['action']['enum']=constraints['actions']
   if 'keyword_choices' in constraints:schema['properties']['keyword']['enum']=constraints['keyword_choices']
   for field in ['kind','date_scope','start','end']:
    if field+'_choices' in constraints:schema['properties'][field]['enum']=constraints[field+'_choices']
  payload={'messages':messages,'response_format':{'type':'json_schema','json_schema':{'name':'material_intent','strict':True,'schema':schema}},'temperature':.1,'top_p':.95,'top_k':50,'min_p':0,'repeat_penalty':1.05,'seed':self.seed,'max_tokens':640,'stream':False,'chat_template_kwargs':{'enable_thinking':False},'cache_prompt':True}
  start=time.perf_counter();record={'payload':payload,'feedback':feedback,'controller_constraints':constraints}
  try:
   r=requests.post(model_url()+'/v1/chat/completions',json=payload,timeout=(5,60));r.raise_for_status();raw=r.json();record['response']=raw
   choice=raw['choices'][0]
   if choice.get('finish_reason')=='length':raise RuntimeError('output_truncated')
   value=json.loads(choice['message']['content'])
   if set(value)!=set(SCHEMA['required']):raise ValueError('Intent missing or unknown fields')
   for key,spec in SCHEMA['properties'].items():
    if not isinstance(value[key],str):raise ValueError('Intent field must be string')
    if 'enum' in spec and value[key] not in spec['enum']:raise ValueError('Invalid intent enum')
   record['parsed']=value;record['schema_valid']=True
  except Exception as error:record['error']=repr(error);value=None
  record['elapsed_s']=time.perf_counter()-start;self.records.append(record)
  self.path.parent.mkdir(parents=True,exist_ok=True)
  with self.path.open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
  return value
 def chat(self,history):
  prompt='你在聊天模式，只能對話，沒有執行外部工具，不可宣稱已讀取、開啟、修改或搬移任何本機檔案。你是小型商家的中文助理，使用台灣繁體中文，簡短清楚。這是一般聊天，不操作檔案。系統中AI負責理解需求，可呼叫外部程式讀檔或搬檔；這種呼叫外部功能就是工具呼叫。資料已提供時直接回答，不重問已知資訊。依原文保留姓名、店名、商品和日期，勿自行增添優惠。遵守指定句數、字數與點數；有預算限制時每一點都必須明確寫出獎品數量及總成本上限，不能只說低成本。計算節省比例時，減少量是原本耗時減去新耗時，再除以原本耗時。'
  payload={'messages':[{'role':'system','content':prompt}]+history,'temperature':.1,'top_p':.95,'top_k':50,'seed':self.seed,'max_tokens':512,'stream':False,'chat_template_kwargs':{'enable_thinking':False},'cache_prompt':True}
  start=time.perf_counter();record={'mode':'chat','payload':payload}
  try:
   response=requests.post(model_url()+'/v1/chat/completions',json=payload,timeout=(5,60));response.raise_for_status();raw=response.json();record['response']=raw
   if raw['choices'][0].get('finish_reason')=='length':raise RuntimeError('chat_output_truncated')
   text=raw['choices'][0]['message']['content'];record['text']=text
  except Exception as error:record['error']=repr(error);text='這次回覆沒有完成，請再試一次。'
  record['elapsed_s']=time.perf_counter()-start;self.records.append(record)
  self.path.parent.mkdir(parents=True,exist_ok=True)
  with self.path.open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
  return text
