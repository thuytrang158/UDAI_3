'use strict';
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');

const hashPassword=(password,salt)=>crypto.scryptSync(password,salt,64).toString('hex');
function createCustomerApi({storePath,bookingApi}){
 const sessions=new Map(),loginWindows=new Map();let store;
 try{store=JSON.parse(fs.readFileSync(storePath,'utf8'));}catch(e){if(e.code!=='ENOENT')throw e;store={users:[]};save();}
 function save(){fs.mkdirSync(path.dirname(storePath),{recursive:true,mode:0o700});const tmp=storePath+'.tmp';fs.writeFileSync(tmp,JSON.stringify(store,null,2),{mode:0o600});fs.renameSync(tmp,storePath);fs.chmodSync(storePath,0o600);}
 const json=(res,status,data,extra={})=>{res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff',...extra});res.end(JSON.stringify(data));};
 const body=(req,cb)=>{let size=0,parts=[];req.on('data',x=>{size+=x.length;if(size>20000){cb(Error('Yêu cầu quá lớn.'));req.destroy();}else parts.push(x);});req.on('end',()=>{try{cb(null,JSON.parse(Buffer.concat(parts).toString()||'{}'));}catch{cb(Error('Dữ liệu không hợp lệ.'));}});};
 const parseCookies=req=>Object.fromEntries(String(req.headers.cookie||'').split(';').map(x=>x.trim().split('=').map(decodeURIComponent)).filter(x=>x.length===2));
 const publicUser=u=>({id:u.id,fullName:u.fullName,email:u.email,phone:u.phone,createdAt:u.createdAt});
 const getSession=req=>{const token=parseCookies(req).tour_customer,s=token&&sessions.get(token);return s&&s.expiresAt>Date.now()?s:null;};
 const getCustomerFromRequest=req=>getSession(req)?.user||null;
 const getUser=(req,res,write=false)=>{const s=getSession(req);if(!s){json(res,401,{error:'Vui lòng đăng nhập để tiếp tục.'});return null;}if(write&&req.headers['x-csrf-token']!==s.csrf){json(res,403,{error:'Phiên làm việc đã hết hạn. Tải lại trang và thử lại.'});return null;}return s;};
 const csrfToken=()=>crypto.randomBytes(24).toString('base64url');
 function makeSession(user,res){const token=crypto.randomBytes(32).toString('base64url'),csrf=csrfToken();sessions.set(token,{user,csrf,expiresAt:Date.now()+30*24*60*60*1000});return json(res,200,{customer:publicUser(user),csrf},{'Set-Cookie':`tour_customer=${token}; HttpOnly; SameSite=Strict; Path=/api; Max-Age=2592000`});}
 async function handle(req,res,url){
  const origin=req.headers.origin;if(origin&&origin!==`http://${req.headers.host}`&&origin!==`https://${req.headers.host}`)return json(res,403,{error:'Yêu cầu không hợp lệ.'});
  const method=req.method,p=url.pathname;
  if(method==='POST'&&p==='/api/customer/register')return body(req,(e,b)=>{if(e)return json(res,400,{error:e.message});const fullName=String(b.fullName||'').trim(),email=String(b.email||'').trim().toLowerCase(),phone=String(b.phone||'').trim(),password=String(b.password||'');if(fullName.length<2||fullName.length>80)return json(res,422,{error:'Nhập họ tên từ 2 đến 80 ký tự.'});if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)||email.length>150)return json(res,422,{error:'Email chưa hợp lệ.'});if(!/^(?:\+84|0)[0-9]{9}$/.test(phone.replace(/[\s-]/g,'')))return json(res,422,{error:'Số điện thoại chưa hợp lệ.'});if(password.length<10||password.length>128)return json(res,422,{error:'Mật khẩu cần ít nhất 10 ký tự.'});if(store.users.some(u=>u.email===email))return json(res,409,{error:'Email này đã được đăng ký.'});const salt=crypto.randomBytes(16).toString('hex'),user={id:crypto.randomUUID(),fullName,email,phone,salt,passwordHash:hashPassword(password,salt),createdAt:new Date().toISOString()};store.users.push(user);save();return makeSession(user,res);});
  if(method==='POST'&&p==='/api/customer/login')return body(req,(e,b)=>{if(e)return json(res,400,{error:e.message});const ip=req.socket.remoteAddress||'local',w=loginWindows.get(ip);if(w&&w.until>Date.now()&&w.count>=10)return json(res,429,{error:'Bạn đã thử đăng nhập quá nhiều lần. Vui lòng đợi một phút.'});if(!w||w.until<Date.now())loginWindows.set(ip,{count:1,until:Date.now()+60000});else w.count++;const email=String(b.email||'').trim().toLowerCase(),user=store.users.find(u=>u.email===email);let valid=false;try{const candidate=hashPassword(String(b.password||''),user?.salt||'not-a-real-salt');valid=!!user&&crypto.timingSafeEqual(Buffer.from(candidate,'hex'),Buffer.from(user.passwordHash,'hex'));}catch{}if(!valid)return json(res,401,{error:'Email hoặc mật khẩu chưa chính xác.'});return makeSession(user,res);});
  if(method==='GET'&&p==='/api/customer/session'){const s=getSession(req);return s?json(res,200,{customer:publicUser(s.user),csrf:s.csrf}):json(res,401,{error:'Chưa đăng nhập.'});}
  if(method==='POST'&&p==='/api/customer/logout'){const s=getUser(req,res,true);if(!s)return;sessions.delete(parseCookies(req).tour_customer);return json(res,200,{ok:true},{'Set-Cookie':'tour_customer=; HttpOnly; SameSite=Strict; Path=/api; Max-Age=0'});}
  const session=getUser(req,res,method!=='GET');if(!session)return;
  if(method==='GET'&&p==='/api/customer/bookings'){return json(res,200,{items:bookingApi.customerList(session.user.id)});}
  if(method==='GET'&&p==='/api/customer/notifications'){const items=bookingApi.customerList(session.user.id).flatMap(b=>(b.statusHistory||[]).filter(h=>['administrator','payment'].includes(h.by)).map((h,i)=>({id:`${b.code}-${h.at}-${i}`,bookingCode:b.code,tourName:b.tourName,status:h.status,at:h.at,by:h.by,reason:h.reason||''}))).sort((a,b)=>b.at.localeCompare(a.at));return json(res,200,{items});}
  const pay=p.match(/^\/api\/customer\/bookings\/([^/]+)\/payment$/);if(method==='POST'&&pay)return body(req,(e,b)=>{if(e)return json(res,400,{error:e.message});const result=bookingApi.customerPay(decodeURIComponent(pay[1]),session.user.id,b.outcome);if(result.error)return json(res,409,{error:result.error});return json(res,200,{booking:result.booking,message:result.message});});
  return json(res,404,{error:'Không tìm thấy chức năng.'});
 }
 return {matches:url=>url.pathname.startsWith('/api/customer/'),handle,getCustomerFromRequest};
}
module.exports={createCustomerApi};
