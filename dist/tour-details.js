'use strict';
// Full editorial tour pages are rendered from the same catalogue exported as JSON/Markdown.
function tourMarkdown(t){
 const bullets=xs=>xs.map(x=>'- '+x).join('\n');
 return `# ${t.code} — ${t.name}\n\n${t.summary}\n\n${t.description}\n\n## Thông tin nhanh\n\n- Trạng thái: ${t.statusLabel}\n- Thời lượng: ${t.days} ngày ${t.nights} đêm\n- Tuyến: ${t.places.join(' → ')}\n- Phong cách: ${t.tags.join(', ')}\n- Giá dự kiến: ${money(t.price)} – ${money(t.priceMax)}/người lớn\n- Điểm đón/trả: ${t.departure}\n- Lịch khởi hành: ${t.departureSchedule}\n- Quy mô: ${t.group}\n- Phù hợp: ${t.audience}\n- Mức vận động: ${t.difficulty}\n- Thời điểm: ${t.season}\n- Di chuyển: ${t.transport}\n\n${t.pricingNote}\n\n${t.timingNote}\n\n## Điểm nhấn\n\n${bullets(t.highlights)}\n\n## Lịch trình\n\n${t.itinerary.map(d=>`### Ngày ${d.day}: ${d.title}\n\nĂn: ${d.meals.join(', ')}. Nghỉ: ${d.stay}.\n\n${d.activities.map(a=>`- **${a.time} · ${a.title}:** ${a.description}`).join('\n\n')}`).join('\n\n')}\n\n## Ăn uống và lưu trú\n\n${t.food}\n\n${t.lodging}\n\n## Dự kiến bao gồm\n\n${bullets(t.included)}\n\n## Không bao gồm\n\n${bullets(t.excluded)}\n\n## Chuẩn bị\n\n${bullets(t.packing)}\n\n## Lưu ý riêng\n\n${bullets(t.notes)}\n\n## Phương án thời tiết\n\n${t.weatherPlan}\n\n## Trẻ em, đặt chỗ và bảo hiểm\n\n${t.children}\n\n${t.cancellation}\n\n${t.insurance}\n\n## Điều kiện trước khi mở bán\n\n${bullets(t.operationChecklist)}\n\n## Nguồn đối chiếu điểm đến\n\n${t.sourceIds.map(id=>`- [${TRA_CATALOG.sources[id].title}](${TRA_CATALOG.sources[id].url})`).join('\n')}\n\n${TRA_CATALOG.editorialNote}\n`+demoReviewsMarkdown(t);
}
function tourDetailsHTML(t){
 const esc=escapeHTML, list=xs=>'<ul>'+xs.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>';
 const directions='https://www.google.com/maps/dir/?api=1&origin='+encodeURIComponent('Trung tâm Thái Nguyên Việt Nam')+'&destination='+encodeURIComponent('Trung tâm Thái Nguyên Việt Nam')+'&waypoints='+encodeURIComponent(t.places.map(p=>p+' Thái Nguyên Việt Nam').join('|'))+'&travelmode=driving';
 return `<article class="tour-details">${tourMapSectionHTML(t,directions)}<p class="eyebrow">${t.code} · ${t.days} NGÀY ${t.nights? t.nights+' ĐÊM':''} · ${esc(t.label)}</p><h2>${esc(t.name)}</h2><div class="detail-rating">${demoRatingHTML(t)}</div><div class="card-tags detail-tags">${t.tags.map(tag=>`<span class="tag-badge">${esc(tag)}</span>`).join('')}</div>${tourQuickFactsHTML(t)}<h3 id="tour-overview">Giới thiệu hành trình</h3><p class="tour-lead">${esc(t.summary)}</p><div class="tour-route"><svg class="location-icon" viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true" style="color:#d84534;vertical-align:-2px;margin-right:6px"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 0 1 0-5 2.5 2.5 0 0 1 0 5z"/></svg>${t.places.map(p=>esc(p)).join(' <span>→</span> ')}</div><p>${esc(t.description)}</p><div class="detail-facts"><div><small>GIÁ DỰ KIẾN / NGƯỜI LỚN</small><b>${money(t.price)} – ${money(t.priceMax)}</b></div><div><small>QUY MÔ ĐOÀN</small><b>${esc(t.group)}</b></div></div><p class="editorial-status">${esc(t.statusLabel)}</p><p class="micro">${esc(t.pricingNote)}</p><div class="detail-actions"><button class="button" id="book-demo">Đặt tour ↗</button><button class="outline" id="download-tour">Tải lịch trình .md</button><a class="outline" href="${directions}" target="_blank" rel="noopener">Tra tuyến di chuyển ↗</a></div><p class="micro">Liên kết bản đồ chỉ hỗ trợ tra tuyến theo tên địa điểm, chưa phải tuyến khảo sát; một số thiết bị giới hạn số điểm trung gian.</p><h3>Điều khiến chuyến đi đáng nhớ</h3>${list(t.highlights)}<div class="detail-overview"><h3>Chuyến đi này dành cho ai?</h3><p>${esc(t.audience)}</p><p><b>Mức vận động:</b> ${esc(t.difficulty)}</p><p><b>Thời điểm gợi ý:</b> ${esc(t.season)}</p><p><b>Đón và trả khách:</b> ${esc(t.departure)}</p><p><b>Khởi hành:</b> ${esc(t.departureSchedule)}</p><p><b>Di chuyển:</b> ${esc(t.transport)}</p></div><h3 id="tour-itinerary">Lịch trình chi tiết</h3><p class="micro">${esc(t.timingNote)}</p><div class="itinerary">${t.itinerary.map(d=>`<section class="itinerary-day"><div class="day-header"><span>${String(d.day).padStart(2,'0')}</span><div><h4>Ngày ${d.day} · ${esc(d.title)}</h4><small>Ăn: ${d.meals.map(esc).join(' · ')}<br>Nghỉ: ${esc(d.stay)}</small></div></div><ol>${d.activities.map(a=>`<li><time>${esc(a.time)}</time><div><h5>${esc(a.title)}</h5><p>${esc(a.description)}</p></div></li>`).join('')}</ol></section>`).join('')}</div><h3 id="tour-services">Ăn uống & lưu trú</h3><p>${esc(t.food)}</p><p>${esc(t.lodging)}</p><div class="service-columns"><section><h3>Dự kiến bao gồm</h3>${list(t.included)}</section><section><h3>Không bao gồm</h3>${list(t.excluded)}</section></div><h3>Trước khi lên đường</h3>${list(t.packing)}<h3>Lưu ý của hành trình</h3>${list(t.notes)}<div class="weather-plan"><h3>Nếu thời tiết thay đổi</h3><p>${esc(t.weatherPlan)}</p></div>${tourReviewsHTML(t)}<details><summary>Trẻ em, đặt chỗ và bảo hiểm</summary><p>${esc(t.children)}</p><p>${esc(t.cancellation)}</p><p>${esc(t.insurance)}</p></details><details><summary>Nguồn tham khảo & trạng thái biên tập</summary><p>${esc(TRA_CATALOG.editorialNote)}</p><p>${esc(t.geographyNote)}</p><ul>${t.sourceIds.map(id=>`<li><a href="${TRA_CATALOG.sources[id].url}" target="_blank" rel="noopener">${esc(TRA_CATALOG.sources[id].title)} ↗</a></li>`).join('')}</ul><p>Cập nhật nội dung: 14/10/2026.</p><h4>Việc cần xác nhận trước khi mở bán</h4>${list(t.operationChecklist)}</details></article>`;
}
function tourMapSectionHTML(t,directions){
 const esc=escapeHTML;
 const stops=t.stops||[];
 return `<section class="tour-detail-map-box" aria-label="Bản đồ các điểm đến trong tour"><div class="tour-map-header"><div class="tour-map-title"><svg class="location-icon" viewBox="0 0 24 24" width="16" height="16" fill="#d83c2d" aria-hidden="true" style="vertical-align:-3px;margin-right:6px"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 0 1 0-5 2.5 2.5 0 0 1 0 5z"/></svg><b>Bản đồ điểm đến</b> · Google Maps <small>(${stops.length} điểm)</small></div><a class="tour-map-gmaps-link" href="${directions}" target="_blank" rel="noopener">Mở trên Google Maps ↗</a></div><div id="tour-detail-map" class="tour-detail-map" role="region" aria-label="Bản đồ tương tác các điểm đến"></div><div class="tour-map-stops" aria-label="Danh sách điểm dừng">${stops.map((s,idx)=>`<button type="button" class="map-stop-chip" data-stop-idx="${idx}" title="Xem vị trí ${esc(s.name)} trên bản đồ"><span class="stop-num">${idx+1}</span><span class="stop-name">${esc(s.name)}</span></button>`).join('')}</div><p class="micro tour-map-note">Nhấp vào số thứ tự điểm đến hoặc ghim đỏ trên bản đồ để xem chi tiết vị trí.</p></section>`;
}
function renderTourDetailMap(t){
 if(typeof window==='undefined'||!window.L)return;
 const mapEl=document.getElementById('tour-detail-map');
 if(!mapEl)return;
 if(window._currentTourMap){
  try{window._currentTourMap.remove();}catch(e){}
  window._currentTourMap=null;
 }
 const stops=(t.stops||[]).filter(s=>typeof s.lat==='number'&&typeof s.lng==='number');
 if(!stops.length)return;
 const map=L.map(mapEl,{scrollWheelZoom:false,zoomControl:true});
 window._currentTourMap=map;
 const googleLayer=L.tileLayer('https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',{subdomains:['0','1','2','3'],maxZoom:19,attribution:'© Google Maps'});
 googleLayer.addTo(map);
 googleLayer.on('tileerror',function(){
  if(!map._osmFallback){
   map._osmFallback=true;
   L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap'}).addTo(map);
  }
 });
 const markers=[];
 const latlngs=stops.map(s=>[s.lat,s.lng]);
 stops.forEach((s,idx)=>{
  const pinHtml=`<div class="tour-pin-marker" data-stop="${idx}"><span class="pin-badge">${idx+1}</span><div class="pin-tip"></div></div>`;
  const icon=L.divIcon({className:'custom-tour-pin-wrap',html:pinHtml,iconSize:[28,36],iconAnchor:[14,36],popupAnchor:[0,-34]});
  const marker=L.marker([s.lat,s.lng],{icon}).addTo(map);
  const gmapsPlaceUrl=`https://www.google.com/maps/search/?api=1&query=${s.lat},${s.lng}`;
  const popupHtml=`<div class="tour-pin-popup"><b>${idx+1}. ${escapeHTML(s.name)}</b><p>${escapeHTML(s.region||'')}</p><a href="${gmapsPlaceUrl}" target="_blank" rel="noopener">Mở điểm này trên Google Maps ↗</a></div>`;
  marker.bindPopup(popupHtml);
  markers.push(marker);
 });
 if(latlngs.length>=2){
  L.polyline(latlngs,{color:'#d83c2d',weight:3.5,opacity:0.85,dashArray:'6, 8',lineJoin:'round'}).addTo(map);
 }
 const bounds=L.latLngBounds(latlngs);
 map.fitBounds(bounds,{padding:[35,35],maxZoom:14});
 setTimeout(()=>{
  if(window._currentTourMap===map){
   map.invalidateSize();
   map.fitBounds(bounds,{padding:[35,35],maxZoom:14});
  }
 },200);
 const stopBtns=document.querySelectorAll('.tour-detail-map-box .map-stop-chip');
 stopBtns.forEach((btn,idx)=>{
  btn.onclick=(e)=>{
   e.preventDefault();
   stopBtns.forEach(b=>b.classList.toggle('active',b===btn));
   const stop=stops[idx];
   if(!stop)return;
   map.flyTo([stop.lat,stop.lng],Math.max(map.getZoom(),13),{duration:0.8});
   if(markers[idx])markers[idx].openPopup();
  };
 });
}
openTour=function(id){const t=tours.find(t=>t.id===id);if(!t){toast('Không tìm thấy tour.');return;}showModal(tourDetailsHTML(t));$('#modal').scrollTop=0;bindTourEngagement(t);renderTourDetailMap(t);$('#book-demo').onclick=()=>booking(t);$('#download-tour').onclick=()=>download(t.slug+'.md',tourMarkdown(t));};
// Filter options come from the complete catalogue; personal trip planning is unchanged.
$('#destination').innerHTML='<option value="">Tất cả điểm đến</option>'+TRA_CATALOG.places.map(p=>`<option>${escapeHTML(p.name)}</option>`).join('');
$('#duration').innerHTML='<option value="">Bao nhiêu ngày cũng được</option>'+[1,2,3,4,5].map(d=>`<option value="${d}">${d} ngày${d>1?' '+(d-1)+' đêm':''}</option>`).join('');
$('#price').innerHTML='<option value="">Tất cả mức giá</option><option value="1000000">Đến 1 triệu</option><option value="3000000">Đến 3 triệu</option><option value="5000000">Đến 5 triệu</option><option value="8000000">Đến 8 triệu</option>';
const allUniqueTags=['',...new Set(TRA_CATALOG.tours.flatMap(t=>t.tags))];
$('#tags').innerHTML=allUniqueTags.map(tag=>`<button class="chip ${tag===activeTag?'selected':(tag||activeTag?'':'selected')}" data-tag="${escapeHTML(tag)}">${escapeHTML(tag)||'Tất cả'}</button>`).join('');
renderTours();
if(/^#tour-\d+$/.test(location.hash))openTour(Number(location.hash.slice(6)));

function tourPhotoGallery(t){return '';}
