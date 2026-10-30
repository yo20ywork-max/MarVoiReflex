"""Task conditions compiled from the user's text only; no benchmark/oracle imports."""
from datetime import date,timedelta
import re
IMAGE_WORDS=r'圖片檔|圖片|图像|圖像|照片|相片|圖檔|图档|影像|配圖|視覺素材|縮圖|宣傳照|宣傳圖|活動圖|主視覺|海報圖|插圖'
TEXT_WORDS=r'文字檔|文字文件|文字稿|文字|文案|文本|貼文稿|稿件|說明文件'
CURRENT_WEEK=r'(?:本|這|这)(?:一)?(?:個|个)?(?:週|周|星期|禮拜|礼拜)|當週|當周'
OTHER_TIME=r'(?:上|下)(?:一)?(?:個|个)?(?:週|周|星期|禮拜|礼拜|月)|昨天|前天|明天|後天|最近|近期|那(?:一)?(?:週|周|天|幾天|段時間)|上次.*(?:日期|週|星期|禮拜)|今年|去年|月底|上旬|中旬|下旬|近[一二三四五六七八九十\d]+天'
READ=r'讀取|讀一下|讀出|讀給我|讀一遍|逐字|閱讀|唸|念一下|念出|朗讀|調閱|原文|全文|完整內容|檔案內容'
SEARCH=r'搜尋|搜索|搜一下|檢索|找出|找一下|找找|先找|幫我找|幫忙找|撈|挑出|篩出|篩選|查找|查詢|尋找'
MOVE=r'整理|分類|歸位|歸檔|歸類|收整|收好|收納|搬移|搬動|移動|移到|搬到|放到|放入|收進|移入|歸到|搬'
PREVIEW=r'預覽|對照|去向|分類計畫|整理計畫|預計.*位置|搬之前.*搬之後'
LIST=r'列出|列給我|列一下|清單|名單|盤點|清點|數一下|點一下|有哪些|有什麼|多少|幾個|幾份|總數|數量|檔名|名稱|名字|清冊'
QUOTES=r'「([^」]+)」|“([^”]+)”|"([^"\n]+)"|`([^`\n]+)`'
EXT=r'png|jpe?g|webp|txt|md'
def quoted(text):return [next(x for x in m.groups() if x is not None) for m in re.finditer(QUOTES,text)]
def date_range(text,clock):
 token=r'(?:20\d{2}[年/\.\-])?\d{1,2}[月/\.\-]\d{1,2}(?:日|號)?'
 m=re.search('('+token+r')\s*(?:起|開始)?\s*(?:到|至|~|～|–|—)\s*('+token+')',text)
 if not m:return None
 def parse(s,y):
  a=[int(n) for n in re.findall(r'\d+',s)];return date(*(a if len(a)==3 else [y]+a))
 lo=parse(m[1],clock.year);hi=parse(m[2],lo.year)
 if hi<lo and not re.match(r'20\d{2}',m[2]):hi=date(hi.year+1,hi.month,hi.day)
 if hi<lo:raise ValueError('日期起點晚於終點')
 return lo,hi
def semantic_text(text,paths=()):
 def mask(m):
  v=next(x for x in m.groups() if x is not None).strip()
  is_semantic=bool(re.fullmatch('(?:'+IMAGE_WORDS+'|'+TEXT_WORDS+'|'+CURRENT_WEEK+r'|所有|全部|本週|這週|\.?(?:'+EXT+'))',v,re.I))
  is_date=bool(re.fullmatch(r'[\d年/月日號.\-~～至到\s]+',v))
  prefix=text[max(0,m.start()-10):m.start()]
  if re.search(r'活動名稱|名為|叫作|叫做|名叫|檔名為',prefix):return ' '
  return v if is_semantic or is_date else ' '
 s=re.sub(QUOTES,mask,text)
 for p in sorted(paths,key=len,reverse=True):s=s.replace(p,' ')
 s=re.sub(r'[^\s，。；「」“”`"]+\.(?:'+EXT+r')\b',' ',s,flags=re.I)
 return s
def focus(text):
 parts=[]
 for c in re.split(r'[，,。；;\n！？!?]',text):
  deferred=re.search(r'晚點|晚一點|稍後|等會再|等一下再|之後再|暫時不|先不看|先別看|先不要看|不用看|不用處理',c)
  if deferred:
   a=re.split(r'現在(?:先)?|目前(?:先)?|這次(?:先)?|只要|只找|只看',c[deferred.end():],maxsplit=1)
   if len(a)==2:c=a[1]
   else:continue
  if re.match(r'\s*(?:先)?(?:不要|不找|不看|不用|先別|先不|別看)\s*(?:'+IMAGE_WORDS+'|'+TEXT_WORDS+')',c):
   a=re.split(r'只要|只找|只看|但是|不過|改成',c,maxsplit=1)
   if len(a)==2:c=a[1]
   else:continue
  if re.search(r'發文|上架|開會|展示|貼文',c) and not re.search(READ+'|'+SEARCH+'|'+MOVE+'|'+PREVIEW+'|'+LIST,c):continue
  # A negated file action is not a positive request to move/organize.
  c=re.sub(r'(?:先)?(?:不要|不用|不必|不需要|無需|無須|禁止|不准|先別|先不|別|不)\s*(?:真的|實際|直接|再|先)?\s*(?:搬移|搬動|移動|改動|修改|改寫|變更|更動|覆寫|刪除|執行|搬|動)(?:任何)?(?:檔案|素材|原檔|內容|它們)?',' ',c)
  parts.append(c)
 return '，'.join(parts)
def analyze(user,clock,paths=()):
 masked=semantic_text(user,paths);s=focus(masked);result={'semantic':s,'resource':bool(paths or re.search(r'\bmaterials\b',user,re.I) or re.search(r'\.(?:'+EXT+r')\b',user,re.I)),'actions':None,'kind':None,'date_scope':'any','start':'','end':'','keyword_choices':None,'error':None,'type_explicit':False,'explicit_type_set':[]}
 if re.search(r'複製|拷貝|備份|刪除|清空|覆寫|覆蓋|取代|排序|最新|最舊|最大|最小',s):result['error']='此原型不執行複製、刪除、覆寫或排序；請改用查看或確認後分類。'
 if re.search(r'排除|不含|略過',s):result['error']='請明確指定要處理的檔名、類型和日期；此原型不猜複雜排除條件。'
 try:
  span=date_range(s,clock)
  weeks=bool(re.search(CURRENT_WEEK,s))
  if span:
   if re.search(r'(?:上|下)(?:個|一)?(?:週|周|星期|禮拜)',s):result['error']='日期條件不一致，請提供單一明確範圍。'
   result.update(date_scope='range',start=span[0].isoformat(),end=span[1].isoformat())
  elif weeks:
   if re.search(r'(?:上|下)(?:一)?(?:個|个)?(?:週|周|星期|禮拜|礼拜)',s):result['error']='週別條件不一致，請指定單一週別或明確日期範圍。'
   result['date_scope']='this_week'
  elif re.search(OTHER_TIME+r'|今天(?=的|拍|素材|圖片|圖檔|文案)|當天的|剛才.*(?:週|日期)|前面.*(?:週|日期)',s):result['error']='日期條件不明確或尚未支援，請提供本週或明確起迄日期。'
  elif re.search(r'20\d{2}[年/\.\-]\d|\d{1,2}月\d{1,2}',s):result['error']='請提供完整起迄日期，不能自行忽略日期條件。'
 except ValueError as e:result['error']='日期無效：'+str(e)
 image=bool(re.search(IMAGE_WORDS+r'|(?<![A-Za-z0-9])\.?\b(?:png|jpe?g|webp)\b',s,re.I))
 text=bool(re.search(TEXT_WORDS+r'|(?<![A-Za-z0-9])\.?\b(?:txt|md)\b',s,re.I))
 if image or text:
  result.update(kind='all' if image and text else 'images' if image else 'texts',type_explicit=True,explicit_type_set=(['image'] if image else [])+(['text'] if text else []))
 values=quoted(user)
 semantic_literal=re.compile('^(?:'+IMAGE_WORDS+'|'+TEXT_WORDS+'|'+CURRENT_WEEK+r'|所有|全部|\.?(?:'+EXT+'))$',re.I)
 names=[v for v in values if re.search(r'[^/\\.]\.(?:'+EXT+r')$',v,re.I)]
 literals=[v for v in values if '/' not in v and '\\' not in v and v!='materials' and not semantic_literal.fullmatch(v) and not re.search(r'\.(?:'+EXT+r')$',v,re.I) and not re.fullmatch(r'[\d年/月日號.\-~～至到\s]+',v)]
 read=bool(re.search(READ,s));moving=bool(re.search(MOVE,s));preview=bool(re.search(PREVIEW,s));listing=bool(re.search(LIST,s));search=bool(re.search(SEARCH,s))
 if re.search(r'解釋|教我|原理|什麼意思|差別|為什麼',s) and not read:result['error']='這是操作說明問題，可切換聊天模式討論；執行任務時請指定要做的操作。'
 if read:result['actions']=['read']
 elif moving or preview:result['actions']=['preview','organize','check']
 elif search or (listing and (literals or names or result['type_explicit'] or result['date_scope']!='any')):result['actions']=['search']
 elif listing:result['actions']=['list']
 if names or result['actions']==['list']:result['keyword_choices']=['']
 elif len(set(literals))==1 and result['actions']!=['read']:result['keyword_choices']=list(dict.fromkeys(literals))
 elif len(set(literals))>1 and result['actions']!=['read']:result['error']='一次只處理一個活動，或請提供明確檔名清單。'
 # A generic type/week request contains no campaign keyword. Keep date words
 # in the date condition instead of letting the model reuse them as a name.
 if result['keyword_choices'] is None and not literals and not names:
  first=re.split(r'[，,。；;\n]',user,1)[0].strip()
  types='(?:'+IMAGE_WORDS+'|'+TEXT_WORDS+')'
  generic=r'(?:(?:請|幫我|麻煩|先|只)\s*)*(?:整理|分類|預覽|搜尋|找出|列出)\s*materials\s*(?:'+CURRENT_WEEK+r'|所有|全部)(?:的)?\s*'+types+r'(?:\s*(?:與|和|及|跟)\s*'+types+r')*'
  if re.fullmatch(generic,first,re.I):result['keyword_choices']=['']
 return result
def constraints(spec):
 d={'date_scope_choices':[spec['date_scope']],'start_choices':[spec['start']],'end_choices':[spec['end']]}
 if spec['actions']:d['actions']=spec['actions']
 d['kind_choices']=[spec['kind'] or 'all']
 if spec['keyword_choices'] is not None:d['keyword_choices']=spec['keyword_choices']
 return d
