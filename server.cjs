const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const envFile=path.join(__dirname,'.env');
if(fs.existsSync(envFile))for(const line of fs.readFileSync(envFile,'utf8').split(/\r?\n/)){const trimmed=line.trim();if(!trimmed||trimmed.startsWith('#'))continue;const match=trimmed.match(/^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);if(!match||process.env[match[1]]!==undefined)continue;let value=match[2].trim();if((value.startsWith('"')&&value.endsWith('"'))||(value.startsWith("'")&&value.endsWith("'")))value=value.slice(1,-1);else value=value.replace(/\s+#.*$/,'').trim();process.env[match[1]]=value;}
const {createDemoBookingApi}=require('./demo-booking-api.cjs');
const {createAdminApi}=require('./admin-api.cjs');
const {createCustomerApi}=require('./customer-api.cjs');
const {createRagChatApi}=require('./rag-chat.cjs');
const root=path.resolve(__dirname,'dist');
const privateDir=path.resolve(__dirname,'.private');
const demoBookingApi=createDemoBookingApi(path.join(root,'data','tour-booking-config-v2.json'),path.join(privateDir,'booking-state.json'));
const adminApi=createAdminApi({storePath:path.join(privateDir,'admin-users.json'),bookingApi:demoBookingApi});
const customerApi=createCustomerApi({storePath:path.join(privateDir,'customer-users.json'),bookingApi:demoBookingApi});
demoBookingApi.setCustomerResolver(customerApi.getCustomerFromRequest);
const ragChatApi=createRagChatApi(path.join(root,'data','rag-knowledge-base.json'));
http.createServer((req,res)=>{
  let pathname;
  try{pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);}catch{res.writeHead(400);return res.end('Bad request');}
  const url=new URL(req.url,'http://localhost');
  if(adminApi.matches(url)){adminApi.handle(req,res,url);return;}
  if(customerApi.matches(url)){customerApi.handle(req,res,url);return;}
  if(demoBookingApi.matches(url)){demoBookingApi.handle(req,res,url);return;}
  if(ragChatApi.matches(url)){if(req.method!=='POST'){res.writeHead(405,{'Allow':'POST'});return res.end();}ragChatApi.handle(req,res);return;}
  if(pathname.startsWith('/api/')){
    const upstream=http.request({hostname:'127.0.0.1',port:8000,path:req.url,method:req.method,headers:req.headers},response=>{res.writeHead(response.statusCode||502,response.headers);response.pipe(res);});
    upstream.on('error',()=>{if(!res.headersSent){res.writeHead(503,{'Content-Type':'application/json; charset=utf-8'});res.end(JSON.stringify({detail:'AI Travel Planner API chưa chạy. Hãy khởi động FastAPI tại cổng 8000.'}));}});
    req.pipe(upstream);return;
  }
  let file=path.resolve(root,'.'+pathname);
  if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403);return res.end();}
  try{if(fs.statSync(file).isDirectory())file=path.join(file,'index.html');}catch{}
  fs.readFile(file,(e,data)=>{if(e){res.writeHead(404);return res.end('Not found');}res.setHeader('Content-Type',({'html':'text/html; charset=utf-8','css':'text/css','js':'text/javascript','jpg':'image/jpeg','png':'image/png','svg':'image/svg+xml','json':'application/json','woff':'font/woff','woff2':'font/woff2'})[path.extname(file).slice(1)]||'application/octet-stream');res.setHeader('X-Content-Type-Options','nosniff');res.end(data);});
}).listen(4173,'127.0.0.1',()=>console.log('Local: http://127.0.0.1:4173'));
