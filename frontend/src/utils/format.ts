import {API} from '../api/client';
export const frameUrl=(path:string)=>path.startsWith('http')?path:`${API}${path.startsWith('/')?path:`/${path}`}`;
export const dateTime=(v:string)=>new Date(v).toLocaleString();
export const ago=(v:string)=>{const seconds=Math.max(0,Math.floor((Date.now()-new Date(v).getTime())/1000));return seconds<60?`${seconds}s ago`:seconds<3600?`${Math.floor(seconds/60)} min ago`:seconds<86400?`${Math.floor(seconds/3600)} hr ago`:`${Math.floor(seconds/86400)} days ago`};
export const pct=(v:number|null|undefined)=>v==null?'—':`${(v*100).toFixed(1)}%`;
