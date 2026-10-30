"""Point a source checkout at an existing full App. Does not copy/download models."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parent.parent
REQUIRED=['models/MiniCPM5-2B-Q4_K_M.gguf','runtime/llama-server.exe','node/node.exe','bridge.mjs','asr/faster-whisper-small/model.bin','node/node_modules/@wonderwhy-er/desktop-commander/dist/index.js']
def validate(app_root,check_hash=False):
    root=Path(app_root).expanduser().resolve()
    missing=[p for p in REQUIRED if not (root/'assets'/p).is_file()]
    if missing:raise ValueError('Missing runtime assets: '+', '.join(missing))
    if check_hash:
        with (root/'assets'/REQUIRED[0]).open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        if digest!='ec2d5801640099e97d8d7e8003ad4d81f336e757811f03a26173dddf386602fd':raise ValueError('Model SHA-256 mismatch')
    return root
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--app-root',required=True);p.add_argument('--check-hash',action='store_true');args=p.parse_args()
    root=validate(args.app_root,args.check_hash)
    (ROOT/'app-link.json').write_text(json.dumps({'app_root':str(root)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Runtime configured. app-link.json is local-only; models were not copied.')
