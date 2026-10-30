from chat_session import ChatSession
from flow import Flow
class Assistant:
 """The caller chooses a mode explicitly; the model never routes between modes."""
 def __init__(self,out,clock,seed=42):
  self.chat=ChatSession(out/'chat',seed);self.task=Flow(out/'task',clock,seed)
 def handle(self,mode,text='',control=None,plan_id=None):
  if mode=='chat':
   if control:raise ValueError('聊天模式不接受執行或確認操作')
   return self.chat.reply(text)
  if mode!='task':raise ValueError('請明確選擇 chat 或 task 模式')
  if control=='confirm':return dict(self.task.confirm(plan_id),mode='task')
  if control=='cancel':return dict(self.task.cancel(plan_id),mode='task')
  if control:raise ValueError('未知的任務控制事件')
  return self.task.request(text)
