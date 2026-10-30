from pathlib import Path
import ctypes,hashlib,json,os,secrets,socket,subprocess,threading,time
from ctypes import wintypes
import psutil,requests
from app_paths import bundle_root,data_root
MODEL_SHA='ec2d5801640099e97d8d7e8003ad4d81f336e757811f03a26173dddf386602fd'
def write_json(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
class Job:
    """Windows terminates app-owned services if the app itself exits unexpectedly."""
    def __init__(self):
        k=ctypes.WinDLL('kernel32',use_last_error=True);self.k=k
        class BASIC(ctypes.Structure):_fields_=[('PerProcessUserTimeLimit',ctypes.c_int64),('PerJobUserTimeLimit',ctypes.c_int64),('LimitFlags',wintypes.DWORD),('MinimumWorkingSetSize',ctypes.c_size_t),('MaximumWorkingSetSize',ctypes.c_size_t),('ActiveProcessLimit',wintypes.DWORD),('Affinity',ctypes.c_size_t),('PriorityClass',wintypes.DWORD),('SchedulingClass',wintypes.DWORD)]
        class IO(ctypes.Structure):_fields_=[(n,ctypes.c_uint64) for n in ['ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount']]
        class EXT(ctypes.Structure):_fields_=[('BasicLimitInformation',BASIC),('IoInfo',IO),('ProcessMemoryLimit',ctypes.c_size_t),('JobMemoryLimit',ctypes.c_size_t),('PeakProcessMemoryUsed',ctypes.c_size_t),('PeakJobMemoryUsed',ctypes.c_size_t)]
        k.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR];k.CreateJobObjectW.restype=wintypes.HANDLE
        k.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD];k.SetInformationJobObject.restype=wintypes.BOOL
        k.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE];k.AssignProcessToJobObject.restype=wintypes.BOOL
        k.CloseHandle.argtypes=[wintypes.HANDLE];self.handle=k.CreateJobObjectW(None,None)
        e=EXT();e.BasicLimitInformation.LimitFlags=0x2000
        if not self.handle or not k.SetInformationJobObject(self.handle,9,ctypes.byref(e),ctypes.sizeof(e)):raise ctypes.WinError(ctypes.get_last_error())
    def add(self,p):
        if not self.k.AssignProcessToJobObject(self.handle,wintypes.HANDLE(int(p._handle))):raise ctypes.WinError(ctypes.get_last_error())
    def close(self):
        if self.handle:self.k.CloseHandle(self.handle);self.handle=None
class Services:
    def __init__(self):self.processes=[];self.job=None;self.ready=False;self.root=data_root();self.assets=bundle_root()/'assets';self.lock=threading.RLock()
    def start(self,status=lambda x:None):
        with self.lock:
            if self.ready:return
            self.root.mkdir(parents=True,exist_ok=True)
            for n in ['logs','workspace/materials','ops','home','sessions']:(self.root/n).mkdir(parents=True,exist_ok=True)
            material=self.root/'workspace'/'materials'
            if material.is_symlink() or material.is_junction():raise RuntimeError('素材工作區不可是連結')
            status('正在檢查本機模型…');model=self.assets/'models'/'MiniCPM5-2B-Q4_K_M.gguf'
            with model.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
            if actual!=MODEL_SHA:raise RuntimeError('模型檔不完整，請重新解壓完整 App 資料夾。')
            model_port=free_port();bridge_port=free_port()
            while bridge_port==model_port:bridge_port=free_port()
            os.environ['CROSSGEN_MODEL_URL']=f'http://127.0.0.1:{model_port}';os.environ['CROSSGEN_BRIDGE_URL']=f'http://127.0.0.1:{bridge_port}'
            runtime=self.assets/'runtime'/'llama-server.exe';node=self.assets/'node'/'node.exe'
            cfg=self.root/'home'/'.claude-server-commander'/'config.json'
            write_json(cfg,{'allowedDirectories':[str(material)],'telemetryEnabled':False,'pendingWelcomeOnboarding':False,'welcomeOnboardingEligible':False,'defaultShell':'cmd.exe','fileReadLineLimit':1000,'fileWriteLineLimit':50,'blockedCommands':['format','diskpart','shutdown','reboot','netsh','reg','del','rmdir']})
            env=dict(os.environ,USERPROFILE=str(self.root/'home'),HOME=str(self.root/'home'),APPDATA=str(self.root/'home'/'AppData'/'Roaming'),LOCALAPPDATA=str(self.root/'home'/'AppData'/'Local'),TEMP=str(self.root/'temp'),TMP=str(self.root/'temp'),DESKTOP_COMMANDER_DISABLE_TELEMETRY='1',CUDA_VISIBLE_DEVICES='-1',ROCR_VISIBLE_DEVICES='',GGML_VK_VISIBLE_DEVICES='',GGML_BACKEND_PATH=str(runtime.parent),GGML_BACKEND_DL_PATH=str(runtime.parent))
            (self.root/'temp').mkdir(exist_ok=True)
            self.job=Job();status('正在載入 CPU 模型與素材工具…')
            args=[str(runtime),'-m',str(model),'--host','127.0.0.1','--port',str(model_port),'--device','none','--gpu-layers','0','--no-op-offload','--threads','4','--threads-batch','4','--ctx-size','4096','--batch-size','512','--ubatch-size','128','--parallel','1','--no-context-shift','--jinja','--reasoning','off','--chat-template-kwargs','{"enable_thinking":false}','--cache-ram','512','--offline']
            try:
                for name,cmd in [('model',args),('mcp',[str(node),str(self.assets/'bridge.mjs'),str(self.assets),str(self.root),str(bridge_port)])]:
                    with (self.root/'logs'/(name+'.log')).open('ab') as log:p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,cwd=self.root,env=env,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
                    self.processes.append((name,p));self.job.add(p)
                for _ in range(600):
                    if any(p.poll() is not None for _,p in self.processes):raise RuntimeError('啟動未完成，請查看 Data/logs 記錄。')
                    try:
                        state=json.loads((self.root/'bridge-state.json').read_text(encoding='utf-8'))
                        if state['port']==bridge_port and requests.get(os.environ['CROSSGEN_MODEL_URL']+'/health',timeout=.3).status_code==200:
                            requests.get(os.environ['CROSSGEN_BRIDGE_URL']+'/status',headers={'Authorization':'Bearer '+state['token']},timeout=1).raise_for_status();break
                    except (OSError,ValueError,requests.RequestException):pass
                    time.sleep(.1)
                else:raise RuntimeError('啟動超時，請查看 Data/logs。')
                self.ready=True;write_json(self.root/'service-status.json',{'ready':True,'CPU_only':True,'threads':4,'ports':[model_port,bridge_port],'pids':{n:p.pid for n,p in self.processes}});status('已就緒 · CPU 模式 · 不使用顯卡')
            except BaseException:self.stop();raise
    def stop(self):
        with self.lock:
            if self.processes:
                try:
                    state=json.loads((self.root/'bridge-state.json').read_text(encoding='utf-8'))
                    requests.post(os.environ['CROSSGEN_BRIDGE_URL']+'/shutdown',headers={'Authorization':'Bearer '+state['token']},timeout=5)
                except (OSError,ValueError,KeyError,requests.RequestException):pass
                for name,p in reversed(self.processes):
                    if p.poll() is None:
                        if name=='model':p.terminate()
                        try:p.wait(timeout=5)
                        except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
            if self.job:self.job.close();self.job=None
            self.processes=[];self.ready=False
            if self.root.exists():write_json(self.root/'service-status.json',{'ready':False,'stopped':True,'at':time.time()})
