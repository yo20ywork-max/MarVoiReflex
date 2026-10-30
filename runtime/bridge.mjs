import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
const [assets,root,portText]=process.argv.slice(2);
const port=Number(portText),cwd=path.join(root,'workspace');
const deps=path.join(assets,'node','node_modules');
const {Client}=await import(pathToFileURL(path.join(deps,'@modelcontextprotocol/sdk/dist/esm/client/index.js')).href);
const {StdioClientTransport}=await import(pathToFileURL(path.join(deps,'@modelcontextprotocol/sdk/dist/esm/client/stdio.js')).href);
const packageRoot=path.join(deps,'@wonderwhy-er/desktop-commander');
const version=JSON.parse(fs.readFileSync(path.join(packageRoot,'package.json'),'utf8')).version;
if(version!=='0.3.1')throw Error('Unexpected MCP version');
const client=new Client({name:'CrossGenAssistantCPU',version:'1.0.0'},{capabilities:{}});
const errlog=fs.createWriteStream(path.join(root,'logs','mcp-stderr.log'),{flags:'a'});
const transport=new StdioClientTransport({command:process.execPath,args:[path.join(packageRoot,'dist','index.js'),'--no-onboarding'],cwd,stderr:'pipe',env:{...process.env,DESKTOP_COMMANDER_DISABLE_TELEMETRY:'1'}});
transport.stderr?.pipe(errlog);
await client.connect(transport,{timeout:30000});
const catalog=await client.listTools(undefined,{timeout:15000});
const token=crypto.randomBytes(24).toString('hex');
const state={pid:process.pid,token,port,version,toolCount:catalog.tools.length,cwd};
const allowed=new Set(['list_directory','read_file','get_file_info','start_search','get_more_search_results','stop_search','start_process','read_process_output']);
let seq=0,queue=Promise.resolve();
const server=http.createServer(async(req,res)=>{
  const reply=(status,data)=>{res.writeHead(status,{'content-type':'application/json; charset=utf-8'});res.end(JSON.stringify(data));};
  if(req.headers.authorization!==`Bearer ${token}`){reply(401,{error:'Unauthorized'});return;}
  if(req.method==='GET'&&req.url==='/status'){reply(200,{...state,token:undefined});return;}
  if(req.method==='POST'&&req.url==='/shutdown'){reply(200,{stopping:true});await queue.catch(()=>{});await client.close();errlog.end();server.close(()=>process.exit(0));return;}
  if(req.method!=='POST'||req.url!=='/call'){reply(404,{error:'Unknown endpoint'});return;}
  try{
    let body='';for await(const chunk of req){body+=chunk;if(body.length>1048576)throw Error('Request too large');}
    const request=JSON.parse(body);if(!allowed.has(request.name)){reply(403,{error:'Tool unavailable in this app'});return;}
    const perform=async()=>{
      const index=++seq,start=performance.now();let record;
      try{const result=await client.callTool({name:request.name,arguments:request.arguments},undefined,{timeout:30000});record={index,label:request.label??null,name:request.name,arguments:request.arguments,elapsedMs:performance.now()-start,result};}
      catch(error){record={index,name:request.name,arguments:request.arguments,error:String(error)};}
      fs.appendFileSync(path.join(root,'logs','mcp-wire.jsonl'),JSON.stringify(record)+'\n');return record;
    };
    const operation=queue.then(perform);queue=operation.then(()=>{},()=>{});reply(200,await operation);
  }catch(error){reply(500,{error:String(error)});}
});
server.listen(port,'127.0.0.1',()=>fs.writeFileSync(path.join(root,'bridge-state.json'),JSON.stringify(state)));
