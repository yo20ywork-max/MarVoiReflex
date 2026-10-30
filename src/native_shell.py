"""The app's own frameless WebView2 window; no external window manipulation."""
from pathlib import Path
import ctypes,json,os,threading,time,urllib.parse

RADIUS_DIP=28
EDGES={'n':12,'s':15,'w':10,'e':11,'nw':13,'ne':14,'sw':16,'se':17}

class NativeShell:
    def __init__(self,url,data_dir,on_close):
        import webview
        self.webview=webview;self.root=Path(data_dir);self.origin=urllib.parse.urlsplit(url)._replace(path='',query='',fragment='').geturl()
        self.on_close=on_close;self.ready=False;self.maximized=False;self.error=None;self._handlers=[];self.snapshot={};self._last_record=0
        os.environ['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS']='--disable-gpu --disable-gpu-compositing'
        self.window=webview.create_window('MarVoiReflex',url,width=1120,height=800,min_size=(680,520),frameless=True,easy_drag=False,shadow=False,resizable=True,background_color='#FFFFFF',text_select=True,zoomable=False)
        self.window.events.before_show+=self._prepare
        self.window.events.closed+=lambda:threading.Thread(target=on_close,daemon=True).start()
    def _record(self,**extra):
        value={**self.snapshot,'host':'WebView2','frameless':True,'radius_DIP':RADIUS_DIP,'ready':self.ready,'error':self.error,'maximized':self.maximized,'CPU_only':True,**extra}
        previous=self.snapshot;self.snapshot=value
        if time.monotonic()-self._last_record<.25 and previous.get('ready')==self.ready and previous.get('error')==self.error:return
        self._last_record=time.monotonic();target=self.root/'native-shell.json';tmp=target.with_suffix('.json.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(tmp,target)
    def _round(self,*_):
        from System.Drawing import Region
        from System.Drawing.Drawing2D import GraphicsPath
        from System.Windows.Forms import FormWindowState
        form=self.window.native;self.maximized=form.WindowState==FormWindowState.Maximized
        if form.WindowState==FormWindowState.Minimized:return
        old=form.Region
        if self.maximized:form.Region=None
        else:
            w,h=int(form.Width),int(form.Height);dpi=float(getattr(form,'DeviceDpi',96));radius=min(round(RADIUS_DIP*dpi/96),w//2,h//2);d=2*radius
            path=GraphicsPath()
            for x,y,start in [(0,0,180),(w-d,0,270),(w-d,h-d,0),(0,h-d,90)]:path.AddArc(int(x),int(y),int(d),int(d),float(start),90.0)
            path.CloseFigure();form.Region=Region(path);path.Dispose()
        if old is not None:old.Dispose()
        self._record(native_border=str(form.FormBorderStyle),region_applied=form.Region is not None,corner_cutout=bool(form.Region is not None and not form.Region.IsVisible(0,0)),width=int(form.Width),height=int(form.Height),dpi=int(getattr(form,'DeviceDpi',96)))
    def _prepare(self):
        try:
            from System.Windows.Forms import Screen
            form=self.window.native;area=Screen.FromControl(form).WorkingArea;form.MaximizedBounds=area
            form.Width=min(form.Width,max(680,int(area.Width)-48));form.Height=min(form.Height,max(520,int(area.Height)-48))
            form.Resize+=self._round
            self._handlers.append(self._round)
            self._round()
            control=form.webview
            def core_ready(sender,args):
                if self.ready:return
                if not args.IsSuccess:
                    self.error=str(args.InitializationException);self._record();return
                core=control.CoreWebView2
                core.Settings.AreDevToolsEnabled=False;core.Settings.IsStatusBarEnabled=False
                def restrict_navigation(sender,event):
                    target=urllib.parse.urlsplit(str(event.Uri));origin=target._replace(path='',query='',fragment='').geturl()
                    if origin!=self.origin:event.Cancel=True
                # Leave WebView2 permissions at their default, user-prompted state.
                def permission(sender,event):
                    from Microsoft.Web.WebView2.Core import CoreWebView2PermissionState
                    event.State=CoreWebView2PermissionState.Default
                core.NavigationStarting+=restrict_navigation;core.PermissionRequested+=permission
                self._handlers.extend([restrict_navigation,permission])
                self.ready=True;self._round()
            control.CoreWebView2InitializationCompleted+=core_ready
            self._handlers.append(core_ready)
            if control.CoreWebView2 is not None:
                # Initialization can precede before_show on a warm WebView2 runtime.
                class Ready: IsSuccess=True
                core_ready(control,Ready())
        except Exception as exc:
            self.error=str(exc);self._record();raise
    def control(self,action,edge=None,width=None,height=None):
        if action not in {'minimize','toggle_maximize','show','drag','resize'}:raise ValueError('未知視窗操作。')
        if not self.ready:raise RuntimeError(self.error or '視窗仍在準備。')
        if action=='resize' and edge not in EDGES:raise ValueError('未知縮放方向。')
        if action=='minimize':self.window.minimize()
        elif action=='toggle_maximize':self.window.restore() if self.maximized else self.window.maximize()
        elif action=='show':self.window.restore();self.window.show()
        elif action=='resize':
            if isinstance(width,bool) or isinstance(height,bool) or not isinstance(width,(int,float)) or not isinstance(height,(int,float)):raise ValueError('視窗尺寸無效。')
            if not 680<=width<=4096 or not 520<=height<=2160:raise ValueError('視窗尺寸超出範圍。')
            from webview import FixPoint
            anchor=(FixPoint.SOUTH if 'n' in edge else FixPoint.NORTH)|(FixPoint.EAST if 'w' in edge else FixPoint.WEST)
            self.window.resize(round(width),round(height),fix_point=anchor)
        else:
            from System import Action
            form=self.window.native;hit=2
            def start():
                user32=ctypes.windll.user32
                if not user32.GetAsyncKeyState(1)&0x8000:return
                user32.ReleaseCapture();user32.SendMessageW.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_size_t,ctypes.c_ssize_t]
                user32.SendMessageW(ctypes.c_void_p(form.Handle.ToInt64()),0xA1,hit,0)
            form.BeginInvoke(Action(start))
        return {'ok':True}
    def destroy(self):
        if self.window.native is not None and not self.window.native.IsDisposed:self.window.destroy()
    def client_ready(self,value):
        required=['controls','composer','sidebar','voice','native_header'];result={k:value.get(k) is True for k in required}
        self._record(client_ready=all(result.values()),client_components=result)
        return {'ok':True}
    def run(self):
        icon=Path(__file__).resolve().parent.parent/'web/voice/brand.ico'
        if getattr(__import__('sys'),'frozen',False):icon=Path(__import__('sys').executable).resolve().parent/'web/voice/brand.ico'
        self.webview.start(gui='edgechromium',debug=False,private_mode=False,storage_path=str(self.root/'webview-profile'),icon=str(icon) if icon.is_file() else None)
