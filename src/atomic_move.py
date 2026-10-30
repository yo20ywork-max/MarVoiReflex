"""Data-only approved batch mover. Win32 MoveFileW never replaces a target."""
from pathlib import Path
from ctypes import wintypes
import ctypes,hashlib,json,os,stat,sys,time
from app_paths import data_root
ROOT=data_root();MAT=ROOT/'workspace'/'materials'
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
kernel.MoveFileW.argtypes=[wintypes.LPCWSTR,wintypes.LPCWSTR];kernel.MoveFileW.restype=wintypes.BOOL
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(value):
 raw=ROOT/'workspace'/value
 if MAT.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:raise RuntimeError('Reparse root blocked')
 p=raw.resolve()
 if not p.is_relative_to(MAT.resolve()):raise RuntimeError('Outside materials blocked')
 current=MAT
 for part in raw.relative_to(MAT).parts:
  current=current/part
  if current.exists() and current.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:raise RuntimeError('Reparse entry blocked')
 return p
def move(src,dst):
 if not kernel.MoveFileW(str(src),str(dst)):raise ctypes.WinError(ctypes.get_last_error())
def run(op):
 items=op['items'];moved=[];result={'success':False,'atomic_no_replace':True,'moved':[],'created_dirs':[],'rollback':[],'injected':op.get('inject')}
 try:
  for item in items:
   src,dst=check(item['source']),check(item['destination'])
   if not src.is_file() or sha(src)!=item['sha256']:raise RuntimeError('Source changed after preview')
   if dst.exists():raise FileExistsError('Destination already exists')
  for item in items:
   parent=check(item['destination']).parent
   if not parent.exists():result['created_dirs'].append(parent.relative_to(ROOT/'workspace').as_posix())
   parent.mkdir(parents=True,exist_ok=True)
  for index,item in enumerate(items):
   src,dst=check(item['source']),check(item['destination'])
   if op.get('inject')=='second_move' and index==1:raise RuntimeError('Injected second-move failure')
   if op.get('inject')=='race_collision' and index==1:
    with dst.open('xb') as f:f.write(b'SYNTHETIC CONCURRENT FILE - MUST NOT OVERWRITE');f.flush();os.fsync(f.fileno())
   move(src,dst);moved.append(item);result['moved'].append(item['destination'])
  for item in items:
   src,dst=check(item['source']),check(item['destination'])
   if src.exists() or not dst.is_file() or sha(dst)!=item['sha256']:raise RuntimeError('Post-move verification failed')
  result['success']=True
 except Exception as error:
  result['error']=repr(error)
  for item in reversed(moved):
   try:
    src,dst=check(item['source']),check(item['destination'])
    if not dst.is_file() or sha(dst)!=item['sha256']:raise RuntimeError('Moved file changed; no blind rollback')
    move(dst,src);result['rollback'].append({'source':item['source'],'restored':sha(src)==item['sha256']})
   except Exception as rollback_error:result['rollback'].append({'source':item['source'],'restored':False,'error':repr(rollback_error)})
 return result
def main(manifest):
 if sys.stdout:sys.stdout.reconfigure(encoding='utf-8')
 p=Path(manifest).resolve()
 if not p.is_relative_to((ROOT/'ops').resolve()) or p.suffix!='.json':raise RuntimeError('Unapproved operation file')
 receipt=p.with_suffix('.result.json')
 op=json.loads(p.read_text(encoding='utf-8'))
 if receipt.exists():
  cached=json.loads(receipt.read_text(encoding='utf-8'))
  if cached['operation_id']!=op['operation_id']:raise RuntimeError('Receipt operation mismatch')
  return cached
 result=run(op);result['operation_id']=op['operation_id']
 temp=receipt.with_suffix('.partial')
 with temp.open('w',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
 temp.replace(receipt)
 return result
