from pathlib import Path
import io,json,re,secrets,threading,time,wave
from app_paths import bundle_root,data_root

class VoiceEngine:
    def __init__(self):self.model=None;self.lock=threading.RLock();self.load_s=0;self.voice_name=None
    def ensure(self):
        with self.lock:
            if self.model:return
            from faster_whisper import WhisperModel
            from opencc import OpenCC
            started=time.perf_counter();self.model=WhisperModel(str(bundle_root()/'assets/asr/faster-whisper-small'),device='cpu',compute_type='int8',cpu_threads=4,num_workers=1,local_files_only=True)
            self.converter=OpenCC('s2twp');self.load_s=time.perf_counter()-started
            self.voices()
    def voices(self):
        import pythoncom,win32com.client
        pythoncom.CoInitialize();speaker=None;token=None
        try:
            speaker=win32com.client.Dispatch('SAPI.SpVoice');items=[]
            for token in speaker.GetVoices():
                lang=token.GetAttribute('Language').lower();name=token.GetDescription()
                if any(x in lang.split(';') for x in ['404','804','c04']):items.append(name)
            if not items:raise RuntimeError('這台 Windows 尚未安裝離線中文朗讀語音。')
            self.voice_name=next((x for x in items if 'Hanhan' in x),items[0]);return items
        finally:
            token=None;speaker=None;pythoncom.CoUninitialize()
    def transcribe(self,content):
        self.ensure()
        import numpy as np
        from faster_whisper.audio import decode_audio
        start=time.perf_counter();audio=decode_audio(io.BytesIO(content),sampling_rate=16000)
        if not 0.15<=len(audio)/16000<=22:raise ValueError('每次語音需介於 0.15 到 22 秒。')
        if not np.isfinite(audio).all():raise ValueError('無效音訊。')
        rms=float(np.sqrt(np.mean(audio**2)))
        if rms<.002:return {'text':'','audio_seconds':len(audio)/16000,'asr_s':time.perf_counter()-start,'rms':rms}
        segments,info=self.model.transcribe(audio,language='zh',beam_size=1,best_of=1,temperature=0,condition_on_previous_text=False,vad_filter=False,without_timestamps=True,max_new_tokens=160,
            initial_prompt='繁體中文。行銷素材、圖片、文案、本週、整理、預覽、確認、取消、資料夾。',hotwords='素材 圖片 文案 本週 整理 預覽')
        parts=list(segments);text=self.converter.convert(''.join(x.text for x in parts).strip())
        if parts and all(x.no_speech_prob>.85 and x.avg_logprob<-1 for x in parts):text=''
        return {'text':text,'audio_seconds':len(audio)/16000,'asr_s':time.perf_counter()-start,'rms':rms}
    def synthesize(self,text):
        import pythoncom,win32com.client
        text=re.sub(r'[`#*_]+','',text).strip()
        if not text:return None
        text=text[:220];root=data_root()/'audio';root.mkdir(parents=True,exist_ok=True);name=secrets.token_hex(16)+'.wav';target=root/name;start=time.perf_counter();pythoncom.CoInitialize()
        stream=None;speaker=None;token=None;tokens=[]
        try:
            speaker=win32com.client.Dispatch('SAPI.SpVoice')
            tokens=list(speaker.GetVoices());token=next((t for t in tokens if t.GetDescription()==self.voice_name),None)
            if token is None:
                token=next((t for t in tokens if '404' in t.GetAttribute('Language').lower().split(';')),None)
            if token is None:raise RuntimeError('找不到離線中文朗讀語音。')
            self.voice_name=token.GetDescription();speaker.Voice=token;speaker.Rate=1;speaker.Volume=100
            stream=win32com.client.Dispatch('SAPI.SpFileStream');stream.Open(str(target),3,False);speaker.AudioOutputStream=stream
            speaker.Speak(text,16);stream.Close();stream=None
        finally:
            if stream:
                try:stream.Close()
                except Exception:pass
            stream=None;speaker=None;token=None;tokens=[];pythoncom.CoUninitialize()
        with wave.open(str(target),'rb') as f:seconds=f.getnframes()/f.getframerate()
        self.trim_cache(root)
        return {'id':name,'url':'/api/audio/'+name,'tts_s':time.perf_counter()-start,'audio_seconds':seconds,'voice':self.voice_name}
    @staticmethod
    def trim_cache(root):
        files=sorted((p for p in root.glob('*.wav') if re.fullmatch(r'[0-9a-f]{32}\.wav',p.name)),key=lambda p:p.stat().st_mtime,reverse=True);total=0
        for i,p in enumerate(files):
            total+=p.stat().st_size
            if i>30 or total>64*1024**2:
                if p.resolve().parent==root.resolve():p.unlink(missing_ok=True)
