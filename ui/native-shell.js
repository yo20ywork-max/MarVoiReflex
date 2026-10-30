// The native app owns window chrome; every action targets its authenticated local host.
(() => {
 'use strict';
 if(document.documentElement.dataset.runtime!=='live'||window.MARVOI_SHELL!=='frameless')return;
 document.documentElement.dataset.shell='native';
 const windowAction=(action,extra={})=>api('/api/window',{action,...extra}).catch(error=>{console.error('Window action failed',error.message);});
 $('minimize').onclick=()=>windowAction('minimize');
 $('maximize').hidden=false;$('maximize').onclick=()=>windowAction('toggle_maximize');
 const drag=document.createElement('div');drag.className='native-drag';drag.setAttribute('aria-hidden','true');
 drag.onpointerdown=event=>{if(event.button===0){event.preventDefault();windowAction('drag');}};
 $('readingSurface').prepend(drag);
 let pendingResize=null,resizing=false;
 const flushResize=()=>{
  if(resizing||!pendingResize)return;const next=pendingResize;pendingResize=null;resizing=true;
  windowAction('resize',next).finally(()=>{resizing=false;flushResize();});
 };
 for(const edge of ['n','s','e','w','ne','nw','se','sw']){
  const handle=document.createElement('div');handle.className='native-resize native-resize-'+edge;handle.setAttribute('aria-hidden','true');
  let origin=null;
  handle.onpointerdown=event=>{if(event.button===0){event.preventDefault();event.stopPropagation();origin={x:event.screenX,y:event.screenY,width:innerWidth,height:innerHeight};handle.setPointerCapture(event.pointerId);}};
  handle.onpointermove=event=>{
   if(!origin)return;const dx=event.screenX-origin.x,dy=event.screenY-origin.y;
   const width=Math.max(680,Math.min(4096,origin.width+(edge.includes('e')?dx:edge.includes('w')?-dx:0)));
   const height=Math.max(520,Math.min(2160,origin.height+(edge.includes('s')?dy:edge.includes('n')?-dy:0)));
   pendingResize={edge,width,height};flushResize();
  };
  handle.onpointerup=event=>{origin=null;if(handle.hasPointerCapture(event.pointerId))handle.releasePointerCapture(event.pointerId);};
  handle.onpointercancel=()=>{origin=null;};
  $('window').append(handle);
 }
 api('/api/window/ready',{
  controls:typeof $('minimize').onclick==='function'&&typeof $('maximize').onclick==='function'&&typeof $('close').onclick==='function',
  composer:!!document.querySelector('.text-composer textarea'),sidebar:!!window.MarVoiSidebar,
  voice:typeof voiceRuntime==='object',native_header:document.documentElement.dataset.shell==='native'
 }).catch(error=>console.error('Native UI initialization failed',error.message));
})();
