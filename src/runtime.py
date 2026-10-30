from pathlib import Path
from datetime import date
import json,re,secrets,threading,time,hashlib
import requests
from app_paths import data_root,model_url
from backend import Services,write_json
from voice_engine import VoiceEngine

class Runtime:
    def __init__(self):
        self.root=data_root();self.root.mkdir(parents=True,exist_ok=True);self.services=Services();self.voice=VoiceEngine();self.ready=False;self.error=None;self.op_lock=threading.RLock();self.state_lock=threading.RLock();self.call_id=None;self.generation=0;self.chat_history=[];self.close_timer=None;self.client_attached=False
    def start(self):
        try:
            self.services.start()
            from assistant_modes import Assistant
            from intent import Planner
            class GroundedPlanner(Planner):
                def ask(self,history,feedback=None,constraints=None):
                    c=dict(constraints or {})
                    if 'keyword_choices' not in c:c['keyword_choices']=getattr(self,'grounded_keywords',[''])
                    return super().ask(history,feedback,c)
            self.assistant=Assistant(self.root/'sessions'/'live',date.today(),42)
            self.assistant.task.planner=GroundedPlanner(self.root/'sessions'/'task.requests.jsonl',42,date.today());self.ready=True
        except BaseException as e:self.error=str(e);self.services.stop()
    def call_start(self):
        if not self.ready:raise RuntimeError(self.error or '助理仍在啟動。')
        with self.state_lock:
            self.call_id=secrets.token_hex(16);self.generation+=1;cid=self.call_id;generation=self.generation
        self.voice.ensure()
        if not self.current(cid,generation):raise RuntimeError('通話已取消。')
        return {'call_id':cid,'voice':self.voice.voice_name,'asr':'faster-whisper-small int8 CPU','asr_load_s':self.voice.load_s}
    def call_end(self):
        with self.state_lock:self.call_id=None;self.generation+=1
    def cancel_turn(self):
        with self.state_lock:self.generation+=1
    def current(self,call_id,generation):
        with self.state_lock:return call_id==self.call_id and generation==self.generation
    def log(self,value):
        p=self.root/'logs'/'latency.jsonl';p.parent.mkdir(exist_ok=True)
        with p.open('a',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False)+'\n')
    def chat(self,user):
        from semantics import MOVE,READ,SEARCH
        if re.search(MOVE+'|'+READ+'|'+SEARCH,user) and re.search(r'檔案|素材|圖片|文案|資料夾',user):
            return {'status':'chat','mode':'chat','text':'請切到交辦，我會先顯示預覽。','executed':False,'llm_s':0}
        prompt=f'你是 MarVoiReflex，本機中文語音助理。今天是{date.today()}。用台灣繁體中文自然對話，每次只說一到兩句，盡量六十字內，不使用 Markdown 或列表。聊天模式沒有檔案工具，不可假裝已操作電腦；想操作檔案請使用者切到交辦。使用者給的名稱、數字和條件依原文保留。'
        messages=[{'role':'system','content':prompt}]+self.chat_history[-8:]+[{'role':'user','content':user}];t=time.perf_counter()
        response=requests.post(model_url()+'/v1/chat/completions',json={'messages':messages,'temperature':.1,'seed':42,'max_tokens':160,'stream':False,'chat_template_kwargs':{'enable_thinking':False},'cache_prompt':True},timeout=(5,45));response.raise_for_status();raw=response.json();choice=raw['choices'][0];text=choice['message']['content'].strip()
        if not text:raise RuntimeError('模型沒有產生回覆。')
        self.chat_history.extend([{'role':'user','content':user},{'role':'assistant','content':text}]);self.chat_history=self.chat_history[-10:]
        return {'status':'chat','mode':'chat','text':text,'executed':False,'llm_s':time.perf_counter()-t,'truncated':choice.get('finish_reason')=='length'}
    def task(self,text):
        from flow import paths_in,ScopeError
        from semantics import analyze
        task=self.assistant.task;task.clock=date.today();task.planner.clock=date.today()
        normalized=re.sub(r'[，。！？!?,\s]+$','',text).strip()
        if re.fullmatch(r'(?:好|好啊|好的|是|同意|確認|確定|直接搬|執行|開始執行|確認執行|確認搬移)+',normalized):
            return {'status':'clarify','mode':'task','text':'請在畫面按確認，才會搬動檔案。','preserve_pending':True}
        if normalized in ['取消','取消操作','不要執行','先不要動','先取消']:
            if task.pending:return dict(task.cancel(task.pending['id']),mode='task')
            return {'status':'cancelled','mode':'task','text':'沒有待確認的操作。'}
        spec=analyze(text,date.today(),paths_in(text))
        if spec['actions'] is None:return {'status':'clarify','mode':'task','text':'請說要做的素材任務。','preserve_pending':True}
        user=text if spec['resource'] else 'materials：'+text
        if not spec['error']:
            try:
                for path in paths_in(text):task.checked(path)
            except ScopeError as error:
                if task.pending:task.cancel(task.pending['id'])
                return {'status':'refused','mode':'task','text':'超出授權範圍，不能執行：'+str(error)}
            assets=task.catalog();candidates=set()
            for a in assets:
                m=re.match(r'(.+?)[_ -]+20\d{6}',a['name'])
                if m and m[1] in text:candidates.add(m[1])
            task.planner.grounded_keywords=['']+sorted(candidates,key=len,reverse=True)
            for candidate in sorted(candidates,key=len,reverse=True):
                if candidate in user and '「'+candidate+'」' not in user:user=user.replace(candidate,'「'+candidate+'」',1)
        result=task.request(user)
        if task.pending:result['plan_id']=task.pending['id'];result['items']=task.pending['items']
        return result
    @staticmethod
    def spoken(result):
        if result['mode']=='chat':return result['text']
        status=result['status'];n=len(result.get('selected',[]))
        if status=='preview':return f'找到{n}份符合的素材。請檢查預覽，按確認後才會整理。'
        if status in ['searched','listed']:return f'找到{n}個檔案，清單已顯示。'
        if status=='completed':return f'已整理{result.get("moved",0)}個檔案，驗證通過。'
        if status=='read':return result['text'][:150]
        return result['text'][:140]
    def turn(self,content,mode,call_id):
        if mode not in ['chat','task']:raise ValueError('請選擇聊天或交辦。')
        with self.state_lock:
            if call_id!=self.call_id:raise PermissionError('通話已結束。')
            generation=self.generation
        if not self.op_lock.acquire(blocking=False):raise RuntimeError('BUSY')
        began=time.perf_counter();turn_id=secrets.token_hex(12)
        try:
            asr=self.voice.transcribe(content)
            if not self.current(call_id,generation):return {'status':'cancelled','turn_id':turn_id}
            if not asr['text']:return {'status':'no_speech','turn_id':turn_id,'metrics':{'asr_s':asr['asr_s'],'server_total_s':time.perf_counter()-began}}
            start=time.perf_counter();result=self.chat(asr['text']) if mode=='chat' else self.task(asr['text']);processing=time.perf_counter()-start
            if not self.current(call_id,generation):return {'status':'cancelled','turn_id':turn_id}
            audio=self.voice.synthesize(self.spoken(result));metrics={'asr_s':asr['asr_s'],'assistant_s':processing,'tts_s':audio['tts_s'],'server_total_s':time.perf_counter()-began,'input_audio_s':asr['audio_seconds'],'reply_audio_s':audio['audio_seconds']}
            self.log({'event':'server_turn','at':time.time(),'turn_id':turn_id,'mode':mode,'result_status':result['status'],'recognized_chars':len(asr['text']),'reply_chars':len(result['text']),**metrics})
            if not self.current(call_id,generation):return {'status':'cancelled','turn_id':turn_id}
            return {'status':'ok','turn_id':turn_id,'recognized':asr['text'],'result':result,'audio':audio,'metrics':metrics}
        finally:self.op_lock.release()
    def text(self,mode,text):
        if not self.ready:raise RuntimeError(self.error or '助理仍在啟動。')
        with self.op_lock:return self.chat(text) if mode=='chat' else self.task(text)
    def control(self,action,plan_id,call_id=None):
        if action not in ['confirm','cancel']:raise ValueError('未知操作。')
        with self.op_lock:
            result=self.assistant.handle('task',control=action,plan_id=plan_id)
            with self.state_lock:active=bool(call_id and call_id==self.call_id)
            if active:result['audio']=self.voice.synthesize(self.spoken(result))
            return result
    def stop(self):self.call_end();self.services.stop()
