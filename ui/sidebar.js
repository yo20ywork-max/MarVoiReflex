// Sidebar presentation only. The existing chat, call and confirmation handlers stay in control.
(() => {
 'use strict';
 document.querySelectorAll('[data-ui-icon]').forEach(e=>e.innerHTML=icon(e.dataset.uiIcon));
 const words={zh:{welcome:'今天想做什麼？',startChat:'聊聊想法',organize:'整理素材',materialPreview:'素材預覽',openAssets:'開啟素材清單',openChat:'開啟聊天',thisConversation:'這段對話',openTask:'開啟任務',materials:'素材',openCall:'開啟通話',callMode:'通話模式',appearance:'外觀',emptyChat:'還沒有對話',emptyAssets:'尚無素材',settings:'設定',close:'收起清單',replySpeed:'回覆速度'},en:{welcome:'What’s on your mind?',startChat:'Let’s chat',organize:'Organize assets',materialPreview:'Asset preview',openAssets:'Open asset list',openChat:'Open chat',thisConversation:'This conversation',openTask:'Open tasks',materials:'Assets',openCall:'Open call',callMode:'Call mode',appearance:'Appearance',emptyChat:'No messages yet',emptyAssets:'No assets yet',settings:'Settings',close:'Close list',replySpeed:'Reply time'}};
 const title=p=>p==='settings'?words[language].settings:C[language][p];
 const panel=$('libraryPanel'),shell=$('window'),rail=$('sidebar');
 const fine=matchMedia('(hover:hover) and (pointer:fine)');
 const narrow=matchMedia('(max-width:680px)');
 let pane=null,openTimer=null,closeTimer=null,restoring=false,keyboard=false,liveUnlocked=false;
 const clearTimers=()=>{clearTimeout(openTimer);clearTimeout(closeTimer);};
 const isOpen=()=>shell.dataset.library==='open';
 function syncLabels(){
  document.querySelectorAll('[data-ui-text]').forEach(e=>e.textContent=words[language][e.dataset.uiText]||'');
  $('pageTitle').textContent=C[language][mode];$('callModeLabel').textContent=callMode==='task'?C[language].callTask:C[language].callChat;
  $('languageValue').textContent=language==='zh'?'繁體中文':'English';
  for(const p of ['chat','task','call','settings']){$(p+'Tab').setAttribute('aria-label',title(p));$(p+'Tab').title=title(p);}
  $('libraryClose').title=words[language].close;$('libraryClose').setAttribute('aria-label',words[language].close);
  if(pane)$('libraryTitle').textContent=title(pane);
  $('contextOpen').setAttribute('aria-label',(language==='zh'?'開啟':'Open ')+C[language][mode]);
  $('assetLibrary').setAttribute('aria-label',words[language].openAssets);$('emptyImport').setAttribute('aria-label',words[language].openAssets);
  const status=$('compact').querySelector('.state span:last-child');$('appStateText').textContent=status.textContent;$('appStateText').title=status.textContent;
  if(document.documentElement.dataset.runtime==='live'&&!liveUnlocked&&typeof liveReady!=='undefined'&&liveReady){liveUnlocked=true;for(const id of ['chatSend','taskSend','import','demo'])$(id).disabled=false;}
  if(pane==='chat')renderRecent();if(pane==='task')renderAssets();
 }
 function emptyRow(text){const n=document.createElement('p');n.className='library-empty';n.textContent=text;return n;}
 function renderRecent(){
  const host=$('recentMessages'),rows=[...$('chatArea').querySelectorAll('.message.user')].slice(-8).reverse();host.replaceChildren();
  if(!rows.length){host.append(emptyRow(words[language].emptyChat));return;}
  for(const row of rows){const b=document.createElement('button');b.className='library-link';b.textContent=row.querySelector('.text').textContent;b.onclick=()=>{go('chat');row.scrollIntoView({block:'nearest',behavior:'instant'});};host.append(b);}
 }
 function renderAssets(){
  const host=$('assetList');host.replaceChildren();if(!assets.length){host.append(emptyRow(words[language].emptyAssets));return;}
  for(const asset of assets.slice(0,100)){
   const b=document.createElement('button');b.className='library-link';b.innerHTML=icon(asset.type==='image'?'image':'files');const label=document.createElement('span');label.className='asset-label';label.textContent=asset.name;b.append(label);b.title=asset.name;
   b.onclick=()=>{go('task');$('taskInput').value='預覽「'+asset.name+'」';$('taskInput').focus({preventScroll:true});};host.append(b);
  }
 }
 function syncIcons(){
  for(const p of ['chat','task','call','settings']){const b=$(p+'Tab');b.dataset.open=String(isOpen()&&pane===p);b.setAttribute('aria-expanded',String(isOpen()&&pane===p));}
  $('contextOpen').setAttribute('aria-expanded',String(isOpen()&&pane===mode));
 }
 function openLibrary(next,focus=false){
  clearTimers();pane=next;for(const p of ['chat','task','call','settings'])$(p+'Library').hidden=p!==next;
  $('libraryTitle').textContent=title(next);shell.dataset.library='open';panel.inert=false;panel.setAttribute('aria-hidden','false');
  $('libraryScrim').hidden=!narrow.matches;$('readingSurface').inert=narrow.matches;
  panel.setAttribute('role',narrow.matches?'dialog':'region');if(narrow.matches)panel.setAttribute('aria-modal','true');else panel.removeAttribute('aria-modal');
  if(next==='chat')renderRecent();if(next==='task')renderAssets();syncIcons();
  if(focus)panel.querySelector('button:not(:disabled)')?.focus({preventScroll:true});
 }
 function closeLibrary(restoreFocus=false){
  clearTimers();const former=pane;shell.dataset.library='closed';panel.setAttribute('aria-hidden','true');panel.inert=true;$('libraryScrim').hidden=true;$('readingSurface').inert=false;syncIcons();
  if(restoreFocus&&former){restoring=true;$(former+'Tab').focus({preventScroll:true});queueMicrotask(()=>restoring=false);}
 }
 function deferClose(){clearTimeout(closeTimer);closeTimer=setTimeout(()=>{if(!panel.contains(document.activeElement)&&!rail.contains(document.activeElement))closeLibrary();},220);}
 function go(next){setMode(next);closeLibrary();if(next==='chat')$('chatInput').focus({preventScroll:true});else if(next==='task')$('taskInput').focus({preventScroll:true});else $('callToggle').focus({preventScroll:true});}
 for(const p of ['chat','task','call','settings']){
  const b=$(p+'Tab');
  b.addEventListener('pointerenter',e=>{if(!fine.matches||e.pointerType==='touch')return;clearTimers();openTimer=setTimeout(()=>openLibrary(p),90);});
  b.addEventListener('pointerleave',e=>{clearTimeout(openTimer);if(!panel.contains(e.relatedTarget))deferClose();});
  b.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();openLibrary(p,!fine.matches||e.detail===0);},true);
  b.addEventListener('focus',()=>{if(!restoring&&keyboard)openLibrary(p);});
  b.addEventListener('keydown',e=>{if(e.key==='ArrowRight'){e.preventDefault();openLibrary(p,true);}});
 }
 panel.addEventListener('pointerenter',()=>clearTimeout(closeTimer));
 panel.addEventListener('pointerleave',e=>{if(fine.matches&&!rail.contains(e.relatedTarget))deferClose();});
 $('libraryClose').onclick=()=>closeLibrary(true);$('libraryScrim').onclick=()=>closeLibrary(true);
 $('contextOpen').onclick=()=>openLibrary(mode,true);$('assetLibrary').onclick=() => openLibrary('task',true);$('emptyImport').onclick=()=>openLibrary('task',true);$('openMaterials').onclick=()=>openLibrary('task',true);
 $('goChat').onclick=()=>go('chat');$('goTask').onclick=()=>go('task');$('goCall').onclick=()=>go('call');$('focusChat').onclick=()=>go('chat');$('brandHome').onclick=e=>{e.preventDefault();go('chat');};
 for(const id of ['import','demo'])$(id).addEventListener('click',()=>{setMode('task');closeLibrary();});
 for(const id of ['callChatMode','callTaskMode'])$(id).addEventListener('click',()=>{go('call');syncLabels();});
 document.addEventListener('pointerdown',e=>{keyboard=false;if(isOpen()&&!panel.contains(e.target)&&!rail.contains(e.target)&&e.target!==$('contextOpen')&&!$('contextOpen').contains(e.target))closeLibrary();},true);
 document.addEventListener('keydown',e=>{
  keyboard=true;if(document.querySelector('dialog[open]'))return;
  if(e.key==='Escape'&&isOpen()){e.preventDefault();closeLibrary(true);}
  if(e.key==='ArrowLeft'&&isOpen()&&panel.contains(e.target)&&!e.target.matches('input,textarea,select')){e.preventDefault();closeLibrary(true);}
  if(e.key==='Tab'&&isOpen()&&narrow.matches){const list=[...panel.querySelectorAll('button:not(:disabled),a[href],input:not(:disabled),textarea')].filter(x=>x.getClientRects().length);const first=list[0],last=list.at(-1);if(e.shiftKey&&(e.target===first||!panel.contains(e.target))){e.preventDefault();last?.focus();}else if(!e.shiftKey&&(e.target===last||!panel.contains(e.target))){e.preventDefault();first?.focus();}}
 },true);
 window.addEventListener('blur',()=>{if(fine.matches)closeLibrary();});
 narrow.addEventListener('change',()=>{if(isOpen())openLibrary(pane);});
 const copyBase=copy;copy=function(){copyBase();syncLabels();};
 const modeBase=setMode;setMode=function(next){modeBase(next);syncLabels();};
 const countBase=updateCount;updateCount=function(){countBase();if(pane==='task')renderAssets();};
 const callBase=updateCallUI;updateCallUI=function(){callBase();$('callModeLabel').textContent=callMode==='task'?C[language].callTask:C[language].callChat;};
 const messageBase=message;message=function(...args){messageBase(...args);if(pane==='chat'&&isOpen())renderRecent();};
 new MutationObserver(syncLabels).observe($('compact').querySelector('.state'),{childList:true,characterData:true,subtree:true});
 const metric=$('callMetrics');if(metric){const label=document.createElement('div');label.className='library-group-label';label.textContent=words[language].replySpeed;label.dataset.uiText='replySpeed';$('metricsSlot').append(label,metric);}
 closeLibrary();syncLabels();
 window.MarVoiSidebar={open:openLibrary,close:closeLibrary,state:()=>({open:isOpen(),pane,mode})};
})();
