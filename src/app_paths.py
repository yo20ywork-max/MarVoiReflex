from pathlib import Path
import base64,os,sys,subprocess
def source_root():return Path(__file__).resolve().parent.parent

def bundle_root():
    if getattr(sys,'frozen',False):return Path(sys.executable).resolve().parent
    configured=os.environ.get('MARVOI_ASSETS_ROOT')
    if configured:return Path(configured).expanduser().resolve()
    import json
    link=source_root()/'app-link.json'
    if link.is_file():
        selected=Path(json.loads(link.read_text(encoding='utf-8'))['app_root']).expanduser()
        return (source_root()/selected).resolve() if not selected.is_absolute() else selected.resolve()
    return source_root()

def web_root():
    return (bundle_root() if getattr(sys,'frozen',False) else source_root())/'web/voice'

def data_root():
    default=bundle_root()/'Data-MarVoiVoice' if getattr(sys,'frozen',False) else source_root()/'.local-data'
    return Path(os.environ.get('CROSSGEN_DATA_DIR',str(default))).expanduser().resolve()

def model_url():return os.environ['CROSSGEN_MODEL_URL']
def bridge_url():return os.environ['CROSSGEN_BRIDGE_URL']
def fixed_move_command(manifest):
    # Only a fixed local helper and its validated manifest are invoked. Paths stay literal.
    manifest=Path(manifest).resolve();root=data_root()
    if manifest.parent!=root/'ops' or manifest.suffix!='.json':raise ValueError('Unapproved manifest')
    args=[str(Path(sys.executable).resolve())]
    if not getattr(sys,'frozen',False):args.append(str(Path(__file__).with_name('main.py')))
    args+=['--atomic-move',str(manifest),'--data-dir',str(root)]
    literal=lambda x:"'"+x.replace("'","''")+"'"
    # Wait for the actual GUI-subsystem EXE; a bare PowerShell invocation can
    # return while that child is still starting, before its receipt exists.
    script="$s=New-Object System.Diagnostics.ProcessStartInfo;"+"$s.FileName="+literal(args[0])+";$s.Arguments="+literal(subprocess.list2cmdline(args[1:]))+";$s.UseShellExecute=$false;$s.CreateNoWindow=$true;$p=[System.Diagnostics.Process]::Start($s);$p.WaitForExit();exit $p.ExitCode"
    encoded=base64.b64encode(script.encode('utf-16-le')).decode('ascii')
    return 'powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -EncodedCommand '+encoded
