// Normalize legacy inline glyphs while retaining their existing button handlers.
(() => {
 'use strict';
 const family='rounded-v1';
 const metricsClose=document.getElementById('metricsClose');if(metricsClose)metricsClose.innerHTML=icon('close');
 function normalizePaths(){
  for(const button of document.querySelectorAll('#files .path-details')){
   if(button.querySelector('svg')?.dataset.iconFamily!==family)button.innerHTML=icon('chevronDown');
  }
 }
 function normalizeSendState(){
  const button=document.getElementById('callDemo'),svg=button?.querySelector('svg');
  if(svg&&svg.dataset.iconFamily!==family&&svg.querySelector('rect'))button.innerHTML=icon('stop');
 }
 for(const button of document.querySelectorAll('.call-modes button')){
  const check=document.createElement('span');check.className='mode-check';check.setAttribute('aria-hidden','true');check.innerHTML=icon('check');button.append(check);
  const update=()=>{check.hidden=button.getAttribute('aria-pressed')!=='true';};update();
  new MutationObserver(update).observe(button,{attributes:true,attributeFilter:['aria-pressed']});
 }
 normalizePaths();normalizeSendState();
 new MutationObserver(normalizePaths).observe(document.getElementById('files'),{childList:true,subtree:true});
 new MutationObserver(normalizeSendState).observe(document.getElementById('callDemo'),{childList:true,subtree:true});
 window.MarVoiRoundedUI={family,icons:Object.keys(I)};
})();
