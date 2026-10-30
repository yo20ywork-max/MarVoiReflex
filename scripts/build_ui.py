"""Build the approved UI using only this repository's editable sources."""
from pathlib import Path
import base64
ROOT=Path(__file__).resolve().parent.parent
def build():
    ui=ROOT/'ui';out=ROOT/'web/voice';out.mkdir(parents=True,exist_ok=True)
    text=lambda name:(ui/name).read_text(encoding='utf-8')
    uri=lambda name,mime:'data:'+mime+';base64,'+base64.b64encode((ui/name).read_bytes()).decode()
    css=text('app.css').replace('__FONT_URI__',uri('NotoSansTC.woff2','font/woff2'))
    csp="default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; media-src 'self' blob:; worker-src 'self'; base-uri 'none'; form-action 'none'"
    core=text('rounded-icons.js')+'\n'+text('core.js')
    controllers='<script>'+core+'</script><script>window.MARVOI_KEY="__SESSION_TOKEN__";window.MARVOI_SHELL="__NATIVE_SHELL__";</script><script src="/live.js"></script>'
    for name in ['sidebar.js','rounded-ui.js','composer.js','native-shell.js']:controllers+='<script>'+text(name)+'</script>'
    html=text('app.template.html').replace('__STYLE__',css).replace('__ICON_URI__',uri('ntpu-official.svg','image/svg+xml')).replace('__CSP__',csp).replace('<!-- CONTROLLERS -->',controllers).replace('<!-- FONT_LICENSE -->','<!-- '+text('NotoSansTC-OFL.txt')+' -->').replace('data-theme="light"','data-theme="light" data-runtime="live"',1)
    for name in ['chatSend','taskSend','import','demo','callToggle','chatVoice','taskVoice']:html=html.replace('id="'+name+'"','id="'+name+'" disabled',1)
    (out/'index.html').write_text(html,encoding='utf-8',newline='\n')
    return out/'index.html'
if __name__=='__main__':print(build())
