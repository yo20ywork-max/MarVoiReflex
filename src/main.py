from pathlib import Path
import argparse,atexit,http.cookies,json,mimetypes,os,re,secrets,shutil,subprocess,sys,threading,time,urllib.parse
os.environ.update(CUDA_VISIBLE_DEVICES='-1',ROCR_VISIBLE_DEVICES='',GGML_VK_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',TOKENIZERS_PARALLELISM='false',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--atomic-move');ap.add_argument('--data-dir');ap.add_argument('--no-browser',action='store_true');ap.add_argument('--port',type=int,default=0);ap.add_argument('--stop',action='store_true');args=ap.parse_args()
    if args.data_dir:os.environ['CROSSGEN_DATA_DIR']=str(Path(args.data_dir).resolve())
    from app_paths import data_root,bundle_root,web_root
    if args.atomic_move:
        from atomic_move import main as move
        move(args.atomic_move);return
    from backend import write_json,Job
    import requests
    root=data_root();root.mkdir(parents=True,exist_ok=True)
    (root/'temp').mkdir(exist_ok=True)
    os.environ.update(TEMP=str(root/'temp'),TMP=str(root/'temp'),HF_HOME=str(root/'temp/hf'),XDG_CACHE_HOME=str(root/'temp/cache'))
    if args.stop:
        state=json.loads((root/'connection.json').read_text(encoding='utf-8'));requests.post(state['origin']+'/api/shutdown',headers={'X-MarVoi-Key':state['token']},json={},timeout=5);return
    # A second launch shares the existing app instead of loading another model.
    import msvcrt
    instance=(root/'instance.lock').open('a+b')
    if instance.seek(0,2)==0:instance.write(b'0');instance.flush()
    instance.seek(0)
    try:msvcrt.locking(instance.fileno(),msvcrt.LK_NBLCK,1)
    except OSError:
        if args.no_browser:raise RuntimeError('此資料夾的助理已經啟動。')
        state=json.loads((root/'connection.json').read_text(encoding='utf-8'))
        requests.get(state['origin']+'/api/status',headers={'X-MarVoi-Key':state['token']},timeout=3).raise_for_status()
        requests.post(state['origin']+'/api/window',headers={'X-MarVoi-Key':state['token']},json={'action':'show'},timeout=5).raise_for_status();return
    from runtime import Runtime
    runtime=Runtime();token=secrets.token_hex(24);web=web_root();browser_job=None;close_timer=None;native_shell=None
    class Server(ThreadingHTTPServer):daemon_threads=True;allow_reuse_address=False
    class Handler(BaseHTTPRequestHandler):
        server_version='MarVoiReflex/0.2'
        def log_message(self,*a):pass
        def fail(self,code,error):self.reply(code,{'error':str(error)})
        def reply(self,code,value):
            body=json.dumps(value,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):pass
        def check_host(self):
            return self.headers.get('Host') in [f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}']
        def auth(self):return self.check_host() and secrets.compare_digest(self.headers.get('X-MarVoi-Key',''),token) and self.headers.get('Origin',origin)==origin
        def body(self,limit=65536):
            n=int(self.headers.get('Content-Length','0'))
            if n<0 or n>limit:raise ValueError('內容超過上限。')
            return self.rfile.read(n)
        def json_body(self):return json.loads(self.body() or b'{}')
        def do_GET(self):
            if not self.check_host():self.fail(403,'Host rejected');return
            parsed=urllib.parse.urlsplit(self.path);path=parsed.path
            if path in ['/','/index.html']:
                cookies=http.cookies.SimpleCookie();cookies.load(self.headers.get('Cookie',''));cookie=cookies.get('mrv_session');provided=urllib.parse.parse_qs(parsed.query).get('launch',[''])[0]
                if not secrets.compare_digest(provided,token) and not (cookie and secrets.compare_digest(cookie.value,token)):self.fail(403,'請從 MarVoiReflex.exe 啟動。');return
                raw=(web/'index.html').read_text(encoding='utf-8').replace('__SESSION_TOKEN__',token).replace('__NATIVE_SHELL__','frameless' if native_shell else 'web').encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Set-Cookie',f'mrv_session={token}; SameSite=Strict; HttpOnly; Path=/');self.send_header('Permissions-Policy','microphone=(self), camera=()');self.send_header('X-Frame-Options','DENY');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
            if path in ['/live.js','/audio-worklet.js']:
                p=web/path.lstrip('/');data=p.read_bytes();self.send_response(200);self.send_header('Content-Type','application/javascript; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
            if not self.auth():self.fail(403,'Unauthorized');return
            if path=='/api/status':self.reply(200,{'ready':runtime.ready,'error':runtime.error,'CPU_only':True,'scope':'materials','voice_ready':runtime.voice.model is not None});return
            if path=='/api/assets':
                try:
                    with runtime.op_lock:items=runtime.assistant.task.catalog() if runtime.ready else []
                    self.reply(200,{'assets':[{'name':a['name'],'type':a['type'],'path':a['path']} for a in items]})
                except Exception as e:self.fail(400,e)
                return
            if path=='/api/window/status':
                self.reply(200,native_shell.snapshot if native_shell else {'ready':False,'host':'headless' if args.no_browser else 'starting'});return
            if re.fullmatch(r'/api/audio/[0-9a-f]{32}\.wav',path):
                p=root/'audio'/path.rsplit('/',1)[1]
                if not p.is_file():self.fail(404,'音訊已過期。');return
                data=p.read_bytes();self.send_response(200);self.send_header('Content-Type','audio/wav');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers()
                try:self.wfile.write(data)
                except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):pass
                return
            self.fail(404,'Not found')
        def do_POST(self):
            nonlocal close_timer
            path=urllib.parse.urlsplit(self.path).path
            # sendBeacon cannot set a custom header; its JSON body contains the same secret.
            if path=='/api/client/detach':
                try:
                    v=self.json_body()
                    if not self.check_host() or v.get('key')!=token:self.fail(403,'Unauthorized');return
                    if close_timer:close_timer.cancel()
                    close_timer=threading.Timer(8,shutdown);close_timer.daemon=True;close_timer.start();self.reply(200,{'ok':True})
                except Exception as e:self.fail(400,e)
                return
            if not self.auth():self.fail(403,'Unauthorized');return
            try:
                if path=='/api/voice/turn':
                    content=self.body(2_000_000);mode=self.headers.get('X-Voice-Mode','');cid=self.headers.get('X-Call-ID','');self.reply(200,runtime.turn(content,mode,cid));return
                if path=='/api/assets/import':
                    name=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get('name',[''])[0]
                    if not name or name in ['.','..'] or re.search(r'[<>:"/\\|?*\x00-\x1f]',name) or name.rstrip(' .')!=name:raise ValueError('檔名無效。')
                    if Path(name).suffix.lower() not in ['.png','.jpg','.jpeg','.webp','.txt','.md']:raise ValueError('只支援圖片、TXT 與 MD。')
                    n=int(self.headers.get('Content-Length','0'))
                    if not 0<=n<=32*1024**2:raise ValueError('單檔最多32MB。')
                    mat=root/'workspace/materials'
                    if mat.is_symlink() or mat.is_junction():raise ValueError('不允許連結工作區。')
                    p=mat/name
                    with runtime.op_lock:
                        if runtime.assistant.task.pending:runtime.assistant.task.cancel(runtime.assistant.task.pending['id'])
                        with p.open('xb') as f:
                            left=n
                            while left:
                                chunk=self.rfile.read(min(left,1024*1024))
                                if not chunk:raise ValueError('檔案未傳完整。')
                                f.write(chunk);left-=len(chunk)
                    self.reply(200,{'ok':True,'name':name});return
                v=self.json_body()
                if path=='/api/client/attach':
                    if close_timer:close_timer.cancel();close_timer=None
                    self.reply(200,{'ok':True});return
                if path=='/api/window':
                    if not native_shell:raise RuntimeError('目前沒有桌面視窗。')
                    self.reply(200,native_shell.control(v.get('action'),v.get('edge'),v.get('width'),v.get('height')));return
                if path=='/api/window/ready':
                    if not native_shell:raise RuntimeError('目前沒有桌面視窗。')
                    self.reply(200,native_shell.client_ready(v));return
                if path=='/api/call/start':self.reply(200,runtime.call_start());return
                if path=='/api/call/end':runtime.call_end();self.reply(200,{'ok':True});return
                if path=='/api/call/cancel':runtime.cancel_turn();self.reply(200,{'ok':True});return
                if path=='/api/text':
                    mode=v.get('mode');text=v.get('text','')
                    if mode not in ['chat','task'] or not isinstance(text,str) or not 0<len(text)<=3000:raise ValueError('文字或模式無效。')
                    self.reply(200,{'result':runtime.text(mode,text)});return
                if path=='/api/task/control':self.reply(200,{'result':runtime.control(v.get('action'),v.get('plan_id'),v.get('call_id'))});return
                if path=='/api/assets/demo':
                    from demo_data import create_demo
                    with runtime.op_lock:
                        if runtime.assistant.task.pending:runtime.assistant.task.cancel(runtime.assistant.task.pending['id'])
                        names=create_demo(root/'workspace/materials')
                    self.reply(200,{'created':len(names)});return
                if path=='/api/metrics':
                    allowed=['turn_id','speech_end_to_play_s','confirmation_to_play_s','client_total_s','vad_wait_s','network_wait_s','audio_decode_s','audio_output_latency_s','interrupted','error']
                    record={k:v[k] for k in allowed if k in v};record.update(event='client_playback',at=time.time());runtime.log(record);self.reply(200,{'ok':True});return
                if path=='/api/shutdown':self.reply(200,{'ok':True});threading.Thread(target=shutdown,daemon=True).start();return
                self.fail(404,'Not found')
            except FileExistsError:self.fail(409,'同名檔案已存在，沒有覆寫。')
            except PermissionError as e:self.fail(403,e)
            except Exception as e:self.fail(409 if str(e)=='BUSY' else 400,e)
    server=Server(('127.0.0.1',args.port),Handler);origin=f'http://127.0.0.1:{server.server_port}';launch=origin+'/?launch='+token
    stopping=threading.Event()
    def shutdown():
        nonlocal browser_job
        if stopping.is_set():return
        stopping.set();runtime.call_end()
        with runtime.op_lock:runtime.stop()
        server.shutdown()
        if browser_job:browser_job.close();browser_job=None
        if native_shell:native_shell.destroy()
        write_json(root/'stopped.json',{'at':time.time(),'stopped':True})
    write_json(root/'connection.json',{'origin':origin,'url':launch,'token':token,'pid':os.getpid(),'started':time.time()})
    threading.Thread(target=runtime.start,daemon=True).start();atexit.register(runtime.stop)
    server_thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.2},daemon=True);server_thread.start()
    try:
        if not args.no_browser:
            from native_shell import NativeShell
            native_shell=NativeShell(launch,root,shutdown)
            native_shell.run()
        else:server_thread.join()
    finally:
        shutdown();runtime.stop();server.server_close()

if __name__=='__main__':
    try:main()
    except Exception:
        import traceback
        from app_paths import data_root
        root=data_root();(root/'logs').mkdir(parents=True,exist_ok=True);(root/'logs/startup-error.txt').write_text(traceback.format_exc(),encoding='utf-8')
        if not any(flag in sys.argv for flag in ['--no-browser','--atomic-move','--stop']):ctypes=__import__('ctypes');ctypes.windll.user32.MessageBoxW(None,'啟動未完成，請查看 Data-MarVoiVoice/logs/startup-error.txt。','MarVoiReflex',16)
        sys.exit(1)
