const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const nodes=new Map(),storage=new Map();
const document={querySelector(s){if(!nodes.has(s))nodes.set(s,{value:'',innerHTML:'',textContent:'',style:{},addEventListener(){},querySelectorAll(){return[];}});return nodes.get(s);},querySelectorAll(){return[];},addEventListener(){}};
const ctx=vm.createContext({document,Intl,console,location:{hash:''},setTimeout,clearTimeout,localStorage:{getItem:k=>storage.get(k)??null,setItem:(k,v)=>storage.set(k,v)}});
vm.runInContext(fs.readFileSync('dist/tours-data.js','utf8'),ctx);
vm.runInContext(fs.readFileSync('dist/tour-reviews-data.js','utf8'),ctx);
vm.runInContext(fs.readFileSync('dist/tour-engagement.js','utf8'),ctx);
vm.runInContext(fs.readFileSync('dist/app.js','utf8'),ctx);
vm.runInContext(fs.readFileSync('dist/tour-details.js','utf8'),ctx);
const run=s=>vm.runInContext(s,ctx);
assert.equal(run('filteredTours().length'),10);
nodes.get('#destination').value='Đồi chè Tân Cương';assert.equal(run('filteredTours().length'),5);
nodes.get('#price').value='1000000';assert.equal(run('filteredTours().length'),2);
nodes.get('#duration').value='3';assert.equal(run('filteredTours().length'),0);
for(const key of ['#destination','#price','#duration'])nodes.get(key).value='';
nodes.get('#sort').value='asc';assert.equal(run('filteredTours()[0].price'),790000);
run('activeTag="Trekking"');assert.equal(run('filteredTours().length'),2);run('activeTag=""');
nodes.get('#destination').value='Hang Thẳm Phầy';assert.equal(run('filteredTours()[0].code'),'TJ08');nodes.get('#destination').value='';
nodes.get('#duration').value='5';assert.equal(run('filteredTours()[0].code'),'TJ10');nodes.get('#duration').value='';
let p=run('generatePlan({budget:1500000,people:2,days:2,style:"Thiên nhiên",selected:[0,1]})');
assert.equal(p.total,1690000);assert.equal(p.groupTotal,3380000);assert.equal(p.stops.length,2);assert.ok(p.total>p.budget);
let q=run('generatePlan({budget:2000000,people:4,days:2,style:"Văn hóa",selected:[]})');assert.equal(q.stops[0].name,'ATK Định Hóa');assert.equal(q.groupTotal,q.total*4);
assert.equal(run('escapeHTML("<script>")'),'&lt;script&gt;');
assert.ok(document.querySelector('#tour-grid').innerHTML.includes('tour-card'));
for(const file of ['index.html','style.css','app.js','assets/tea.jpg','assets/lake.jpg','assets/culture.jpg','assets/tea2.jpg'])assert.ok(fs.existsSync('dist/'+file));
console.log('PASS: tour filtering, sorting, budget, group pricing, style selection, text escaping, initial rendering and assets.');
const catalogue=JSON.parse(fs.readFileSync('dist/data/tours.json','utf8'));
assert.equal(catalogue.tours.length,10);assert.equal(catalogue.places.length,13);
assert.equal(new Set(catalogue.tours.map(t=>t.id)).size,10);
const coverage=new Set(catalogue.tours.flatMap(t=>t.destinationIds));for(const p of catalogue.places)assert.ok(coverage.has(p.id),p.name);
assert.deepEqual(JSON.parse(JSON.stringify(ctx.TRA_CATALOG)),catalogue,'Exports must match the website data');
for(const t of catalogue.tours){
 assert.equal(t.itinerary.length,t.days,t.code);assert.equal(t.nights,t.days-1);assert.ok(t.priceMax>=t.price);assert.equal(t.rating,null);assert.equal(t.reviewCount,0);
 assert.ok(t.places.length>=2);assert.ok(fs.existsSync('dist/assets/'+t.image));
 assert.equal(t.itinerary.filter(d=>d.stay!=='Không lưu trú').length,t.nights,t.code+' overnight count');
 for(const d of t.itinerary){assert.ok(d.activities.length>=4);let last=0;for(const a of d.activities){const match=a.time.match(/^(\d{2}):(\d{2})–(\d{2}):(\d{2})$/);assert.ok(match,a.time);const start=+match[1]*60+(+match[2]),end=+match[3]*60+(+match[4]);assert.ok(start>=last&&end>start,t.code+' chronological activities');last=end;}}
 for(const id of t.sourceIds)assert.ok(catalogue.sources[id]?.url.startsWith('https://'));
 assert.ok(t.stops&&t.stops.length>=2);
 for(const s of t.stops){assert.equal(typeof s.lat,'number');assert.equal(typeof s.lng,'number');}
 const html=run(`tourDetailsHTML(tours.find(t=>t.id===${t.id}))`);assert.ok(!html.includes('undefined'));assert.ok(html.includes('Lịch trình chi tiết'));assert.ok(html.includes('Ngày '+t.days));assert.ok(html.includes('id="tour-detail-map"'));assert.ok(html.includes('Bản đồ điểm đến'));
 const markdown=run(`tourMarkdown(tours.find(t=>t.id===${t.id}))`);assert.ok(markdown.includes(t.name));assert.ok(markdown.includes('Không bao gồm'));
}
assert.equal((nodes.get('#tour-grid').innerHTML.match(/đánh giá mô phỏng/g)||[]).length,10,'Every tour rating is labeled');
const html=fs.readFileSync('dist/index.html','utf8');assert.ok(html.indexOf('tours-data.js')<html.indexOf('src="app.js"'));assert.ok(html.includes('tour-details.css'));assert.ok(html.includes('data/tours.json'));
console.log('PASS: 10 complete tour records, 13-destination coverage, day/night counts, chronological schedules, no fake ratings, detail rendering and consistent JSON export.');
