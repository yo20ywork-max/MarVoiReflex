from pathlib import Path
import re
from intent import Planner
class ChatSession:
 """No MCP client, paths, process launcher, or task-plan capability."""
 def __init__(self,out,seed=42):self.planner=Planner(Path(out).with_suffix('.requests.jsonl'),seed);self.history=[]
 def reply(self,user):
  self.history.append({'role':'user','content':user});text=self.planner.chat(self.history[-10:])
  if re.search(r'(?:已經|已幫你|已為你|已完成|已成功|我已).{0,30}(?:移動|搬移|改寫|覆寫|刪除|開啟|讀取|整理.*檔)',text):text='目前是聊天模式，沒有執行任何檔案操作。要操作素材時請使用任務模式。'
  self.history.append({'role':'assistant','content':text});return {'status':'chat','mode':'chat','executed':False,'text':text}
