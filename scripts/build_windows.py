"""Build the native shell only; external runtime assets are not copied."""
from pathlib import Path
import os,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
if os.name!='nt':raise SystemExit('Windows x64 is required.')
(ROOT/'build/temp').mkdir(parents=True,exist_ok=True)
os.environ.update(TEMP=str(ROOT/'build/temp'),TMP=str(ROOT/'build/temp'),PYINSTALLER_CONFIG_DIR=str(ROOT/'build/cache'))
subprocess.run([sys.executable,str(ROOT/'scripts/build_ui.py')],check=True)
cmd=[sys.executable,'-m','PyInstaller','--noconfirm','--onedir','--windowed','--name','MarVoiReflex','--contents-directory','voice_runtime','--distpath',str(ROOT/'dist'),'--workpath',str(ROOT/'build/work'),'--specpath',str(ROOT/'build'),'--icon',str(ROOT/'web/voice/brand.ico'),'--paths',str(ROOT/'src'),'--collect-data','opencc','--collect-data','faster_whisper','--collect-binaries','ctranslate2','--collect-data','webview','--collect-all','clr_loader','--collect-all','pythonnet']
for n in ['webview.platforms.winforms','webview.platforms.edgechromium','clr','pythonnet','win32com.client','pythoncom','pywintypes','tokenizers','psutil']:cmd+=['--hidden-import',n]
for n in ['torch','tensorflow','transformers','PySide6','tkinter','matplotlib','pandas','scipy','IPython','pyarrow','pytest','ctranslate2.converters','ctranslate2.specs','webview.platforms.qt','webview.platforms.gtk','webview.platforms.cocoa','webview.platforms.android','webview.platforms.cef']:cmd+=['--exclude-module',n]
subprocess.run(cmd+[str(ROOT/'src/main.py')],cwd=ROOT,check=True)
import shutil
shutil.copytree(ROOT/'web',ROOT/'dist/MarVoiReflex/web',dirs_exist_ok=True)
print('Native shell built. See docs/development.md for adding validated assets and notices.')
