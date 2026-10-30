// One 24px outline family. Curved contours, rounded terminals and shared weight.
function roundedGearPath(){
 const count=32,step=2*Math.PI/count;
 const point=t=>{const r=8.4+1.05*Math.cos(8*t),dr=-8.4*Math.sin(8*t);return {x:12+r*Math.cos(t),y:12+r*Math.sin(t),dx:dr*Math.cos(t)-r*Math.sin(t),dy:dr*Math.sin(t)+r*Math.cos(t)};};
 const n=v=>v.toFixed(3),first=point(-Math.PI/2);let d='M'+n(first.x)+' '+n(first.y);
 for(let i=0;i<count;i++){const a=point(-Math.PI/2+i*step),b=point(-Math.PI/2+(i+1)*step);d+='C'+[a.x+a.dx*step/3,a.y+a.dy*step/3,b.x-b.dx*step/3,b.y-b.dy*step/3,b.x,b.y].map(n).join(' ');}
 return '<path d="'+d+'Z"/><circle cx="12" cy="12" r="3.15"/>';
}
const I=Object.freeze({
 moon:'<path d="M10.15 3.85C6.5 4.7 3.8 8 3.8 12C3.8 16.55 7.45 20.2 12 20.2C16 20.2 19.3 17.5 20.15 13.85Q20.3 13.15 19.65 13.45C17.05 14.7 13.9 14.15 11.8 12.05C9.7 9.95 9.15 6.8 10.55 4.35Q10.9 3.65 10.15 3.85Z"/>',
 sun:'<circle cx="12" cy="12" r="3.75"/><path d="M12 2.75v1.5M12 19.75v1.5M2.75 12h1.5M19.75 12h1.5M5.45 5.45l1.05 1.05M17.5 17.5l1.05 1.05M5.45 18.55l1.05-1.05M17.5 6.5l1.05-1.05"/>',
 globe:'<circle cx="12" cy="12" r="8.75"/><path d="M12 3.25C15.6 7.5 15.6 16.5 12 20.75C8.4 16.5 8.4 7.5 12 3.25M3.4 12C8.6 10.7 15.4 10.7 20.6 12"/>',
 minus:'<path d="M6 12h12"/>',
 close:'<path d="M7 7C10.1 10.1 13.9 13.9 17 17M17 7C13.9 10.1 10.1 13.9 7 17"/>',
 arrow:'<path d="M5 12h13.5M13.8 7.5C15.4 8.8 16.8 10.1 18.2 11.3Q18.9 12 18.2 12.7C16.8 13.9 15.4 15.2 13.8 16.5"/>',
 up:'<path d="M12 19V5.5M7.5 10.2C8.8 8.6 10.1 7.2 11.3 5.8Q12 5.1 12.7 5.8C13.9 7.2 15.2 8.6 16.5 10.2"/>',
 chat:'<path d="M20.5 11.2C20.5 15.65 16.9 18.65 12 18.65C10.9 18.65 9.8 18.5 8.9 18.2Q8.5 18.1 8.1 18.3L5.2 19.55Q4.15 20 4.4 18.9L5 16.6Q5.15 16.05 4.8 15.6C3.95 14.4 3.5 12.9 3.5 11.2C3.5 6.75 7.1 3.75 12 3.75C16.9 3.75 20.5 6.75 20.5 11.2Z"/>',
 folder:'<path d="M3.25 9V7.4C3.25 5.2 4.45 4 6.65 4H9Q10 4 10.7 4.8L12.1 6.3Q12.7 7 13.65 7H17.35C19.55 7 20.75 8.2 20.75 10.4V16.6C20.75 18.8 19.55 20 17.35 20H6.65C4.45 20 3.25 18.8 3.25 16.6V9Z"/>',
 files:'<path d="M8.4 3.5H14.8C15.7 3.5 16.35 3.8 16.95 4.4L19.1 6.55Q20 7.45 20 8.6V17.2C20 19.3 18.8 20.5 16.7 20.5H8.3C6.2 20.5 5 19.3 5 17.2V6.8C5 4.7 6.3 3.5 8.4 3.5Z"/><path d="M14.7 3.8V6.2Q14.7 8 16.5 8H19.7M9 12.3h6.2M9 16h4.1"/>',
 plus:'<path d="M12 5.5v13M5.5 12h13"/>',
 image:'<rect x="3.5" y="3.5" width="17" height="17" rx="4.75"/><circle cx="8.5" cy="8.5" r="1.45"/><path d="M4 16C5.7 14.3 6.9 12.4 8.3 12.4C9.7 12.4 11.3 15 12.8 16.1M11.8 15.1C13 13.6 13.7 12.8 14.7 12.8C16 12.8 18.5 16.3 20.2 17.8"/>',
 phone:'<path d="M8.2 4.2C7.8 3.3 6.9 3 6 3.4L4.8 3.9C3.8 4.3 3.2 5.3 3.4 6.4C4.6 13.6 10.4 19.4 17.6 20.6C18.7 20.8 19.7 20.2 20.1 19.2L20.6 18C21 17.1 20.7 16.2 19.8 15.8L17.5 14.7C16.7 14.3 15.8 14.5 15.2 15.1L14.7 15.6Q14.3 16 13.8 15.7C11.4 14.4 9.6 12.6 8.3 10.2Q8 9.7 8.4 9.3L8.9 8.8C9.5 8.2 9.7 7.3 9.3 6.5Z"/>',
 mic:'<rect x="8.5" y="3" width="7" height="11" rx="3.5"/><path d="M5.5 10.5v1.8a6.5 6.5 0 0 0 13 0v-1.8M12 18.8V21M9 21h6"/>',
 micOff:'<path d="M8.5 8.5v2a3.5 3.5 0 0 0 5.7 2.7M15.5 8.8V6.5a3.5 3.5 0 0 0-6.4-1.9M5.5 10.5v1.8a6.5 6.5 0 0 0 11 4.7M18.5 12.3v-1.8M12 18.8V21M9 21h6M4 4l16 16"/>',
 play:'<path d="M8 6.8C8 5.7 9.2 5.1 10.1 5.7L18.2 10.6C19.2 11.2 19.2 12.8 18.2 13.4L10.1 18.3C9.2 18.9 8 18.3 8 17.2Z"/>',
 stop:'<rect x="6" y="6" width="12" height="12" rx="4"/>',
 settings:roundedGearPath(),
 chevronDown:'<path d="M7 9.5C8.5 10.9 9.8 12.2 11.2 13.3Q12 14 12.8 13.3C14.2 12.2 15.5 10.9 17 9.5"/>',
 panelLeft:'<rect x="3.5" y="4.5" width="17" height="15" rx="4"/><path d="M9 4.7v14.6"/>',
 panelClose:'<path d="M14.5 7.5C13.3 8.6 12.2 9.7 11.2 10.8Q10.2 12 11.2 13.2C12.2 14.3 13.3 15.4 14.5 16.5"/>',
 refresh:'<path d="M19.4 8.5A8 8 0 1 0 20 14M19.5 4.3v3.5Q19.5 9 18.3 9h-3.5"/>',
 check:'<path d="M6.5 12.2 9.3 15Q10.2 15.9 11.1 14.9L18 7.7"/>',
 voice:'<path d="M5 10v4M8.5 7.5v9M12 5v14M15.5 8v8M19 10v4"/>',
 maximize:'<rect x="5" y="5" width="14" height="14" rx="4"/>'
});
const icon=key=>{const name=Object.hasOwn(I,key)?key:'files';return '<svg class="ui-icon" data-icon-name="'+name+'" data-icon-family="rounded-v1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'+I[name]+'</svg>';};
