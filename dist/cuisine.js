'use strict';
// Quản lý hiển thị và tương tác ẩm thực Thái Nguyên & Miền Xanh
(function(){
  const dishes = globalThis.TRA_CUISINE || [];
  let activeCuisineCategory = '';
  const esc = s => (typeof escapeHTML === 'function' ? escapeHTML(s) : String(s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])));
  
  // Quản lý lượt like từ localStorage
  function getCuisineLikesStore(){
    try {
      return JSON.parse(localStorage.getItem('tra-cuisine-likes')) || {};
    } catch(e) {
      return {};
    }
  }
  
  function saveCuisineLikesStore(store){
    try {
      localStorage.setItem('tra-cuisine-likes', JSON.stringify(store));
    } catch(e) {}
  }
  
  function getDishLikes(dish){
    const store = getCuisineLikesStore();
    const delta = store[dish.id] ? 1 : 0;
    return dish.likes + delta;
  }
  
  function isDishLiked(dishId){
    const store = getCuisineLikesStore();
    return !!store[dishId];
  }
  
  function toggleDishLike(dishId){
    const store = getCuisineLikesStore();
    if(store[dishId]){
      delete store[dishId];
    } else {
      store[dishId] = true;
    }
    saveCuisineLikesStore(store);
  }

  // Quản lý bình luận người dùng thêm vào
  function getCuisineReviewsStore(dishId){
    try {
      const all = JSON.parse(localStorage.getItem('tra-cuisine-reviews')) || {};
      return all[dishId] || [];
    } catch(e) {
      return [];
    }
  }

  function addCuisineReview(dishId, review){
    try {
      const all = JSON.parse(localStorage.getItem('tra-cuisine-reviews')) || {};
      if(!all[dishId]) all[dishId] = [];
      all[dishId].unshift(review);
      localStorage.setItem('tra-cuisine-reviews', JSON.stringify(all));
    } catch(e) {}
  }

  function cuisineCardHTML(d){
    const liked = isDishLiked(d.id);
    const likesCount = getDishLikes(d);
    return `
      <article class="cuisine-card" data-cuisine-id="${esc(d.id)}">
        <div class="cuisine-card-media">
          <img src="${esc(d.image)}" alt="${esc(d.name)}" loading="lazy">
          <span class="cuisine-badge">${esc(d.badge || d.category)}</span>
          <button class="cuisine-like-btn ${liked ? 'liked' : ''}" data-like-id="${esc(d.id)}" aria-label="Thích món ăn này" title="${liked ? 'Bỏ thích' : 'Thích món ăn'}">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
            <span class="like-num">${likesCount}</span>
          </button>
        </div>
        <div class="cuisine-card-body">
          <div class="cuisine-region">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="#d83c2d" aria-hidden="true" style="vertical-align:-2px;margin-right:4px;">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 0 1 0-5 2.5 2.5 0 0 1 0 5z"/>
            </svg>
            <span>${esc(d.region)}</span>
          </div>
          <h3>${esc(d.name)}</h3>
          <p class="cuisine-summary">${esc(d.summary)}</p>
          <div class="cuisine-taste-tags">
            ${(d.tasteNotes || []).slice(0, 2).map(tag => `<span class="taste-pill">${esc(tag)}</span>`).join('')}
          </div>
          <div class="cuisine-card-footer">
            <span class="cuisine-category-label">${esc(d.category)}</span>
            <button class="cuisine-explore-btn" data-open-cuisine="${esc(d.id)}">Khám phá câu chuyện <span>↗</span></button>
          </div>
        </div>
      </article>
    `;
  }

  function filteredDishes(){
    if(!activeCuisineCategory) return dishes;
    return dishes.filter(d => d.category === activeCuisineCategory);
  }

  function renderCuisineList(){
    const grid = document.getElementById('cuisine-grid');
    if(!grid) return;
    const list = filteredDishes();
    grid.innerHTML = list.map(cuisineCardHTML).join('');
  }

  // Giao diện Blog ẩm thực chuyên sâu trong modal
  function cuisineBlogHTML(d){
    const liked = isDishLiked(d.id);
    const likesCount = getDishLikes(d);
    const userReviews = getCuisineReviewsStore(d.id);
    const allReviews = [...userReviews, ...(d.reviews || [])];

    // Tìm tour gợi ý nếu có
    let relatedTourHTML = '';
    if(d.story && d.story.relatedTourId && globalThis.TRA_CATALOG && globalThis.TRA_CATALOG.tours){
      const relatedTour = globalThis.TRA_CATALOG.tours.find(t => t.id === d.story.relatedTourId);
      if(relatedTour){
        relatedTourHTML = `
          <div class="cuisine-related-tour">
            <div class="related-tour-info">
              <span class="eyebrow" style="color:var(--green,#225941);margin:0 0 4px;">HÀNH TRÌNH GỢI Ý ĐỂ THƯỞNG THỨC</span>
              <h4>${esc(relatedTour.name)}</h4>
              <p class="micro">${esc(relatedTour.places.join(' → '))}</p>
            </div>
            <button class="button small" onclick="document.getElementById('modal').close(); openTour(${relatedTour.id});">Xem tour ngay ↗</button>
          </div>
        `;
      }
    }

    return `
      <article class="cuisine-blog">
        <header class="cuisine-blog-header">
          <p class="cuisine-blog-kicker"><span>NHẬT KÝ ẨM THỰC</span><i></i><span>${esc(d.category.toUpperCase())}</span></p>
          <h2>${esc(d.name)}</h2>
          <p class="cuisine-blog-sub">${esc(d.subName || d.summary)}</p>
          <div class="cuisine-blog-meta">
            <span class="meta-item cuisine-location"><svg width="14" height="14" viewBox="0 0 24 24" fill="#d83c2d" aria-hidden="true"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 0 1 0-5 2.5 2.5 0 0 1 0 5z"/></svg>${esc(d.region)}</span>
            <span class="badge-mini">${esc(d.badge || d.category)}</span>
            <button class="cuisine-blog-like-btn ${liked ? 'liked' : ''}" data-like-id="${esc(d.id)}" aria-label="${liked ? 'Bỏ yêu thích' : 'Yêu thích món ăn'}">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
              <span>Yêu thích <b class="like-num">${likesCount}</b></span>
            </button>
          </div>
        </header>

        <figure class="cuisine-blog-hero">
          <img src="${esc(d.image)}" alt="${esc(d.name)}" fetchpriority="high">
          <figcaption>${esc(d.imageCaption || d.name)} <span>· Ẩm thực địa phương</span></figcaption>
        </figure>

        <p class="cuisine-blog-lead">${esc(d.summary)}</p>
        ${d.story.journalNote ? `
          <aside class="cuisine-journal-note">
            <span>GỢI Ý THƯỞNG THỨC</span>
            <p>${esc(d.story.journalNote)}</p>
          </aside>
        ` : ''}

        <div class="cuisine-article-layout">
          <div class="cuisine-blog-content">
            <section class="blog-section">
              <span class="blog-section-label">01 · CÂU CHUYỆN MÓN ĂN</span>
              <h3>Từ nếp nhà đến đặc sản vùng đất</h3>
              <p>${esc(d.story.origin)}</p>
            </section>

            <section class="blog-section">
              <span class="blog-section-label">02 · NGUYÊN LIỆU</span>
              <h3>Những thành phần làm nên hương vị</h3>
              <p>${esc(d.story.ingredients)}</p>
            </section>

            <section class="blog-section">
              <span class="blog-section-label">03 · CÁCH LÀM</span>
              <h3>Sự tỉ mỉ trong từng công đoạn</h3>
              <p>${esc(d.story.making)}</p>
            </section>

            <section class="blog-section blog-experience">
              <span class="blog-section-label">04 · TRẢI NGHIỆM THƯỞNG THỨC</span>
              <h3>Chậm lại để cảm nhận trọn vị</h3>
              <p>${esc(d.story.experience)}</p>
            </section>

            <section class="blog-section blog-table-moment">
              <span class="blog-section-label">05 · GỢI Ý CHO CHUYẾN ĐI</span>
              <h3>Một khoảnh khắc ngon miệng ở địa phương</h3>
              <p>${esc(d.story.tableMoment || '')}</p>
            </section>
          </div>

          <aside class="cuisine-article-aside" aria-label="Thông tin món ăn">
            <section class="cuisine-taste-card">
              <span class="aside-eyebrow">GHI CHÚ HƯƠNG VỊ</span>
              <h3>Một chút về món này</h3>
              <div class="taste-bar-items">
                ${(d.tasteNotes || []).map(note => `<span class="taste-chip">${esc(note)}</span>`).join('')}
              </div>
            </section>
            <section class="cuisine-spot-box">
              <span class="aside-eyebrow">GỢI Ý GHÉ THĂM</span>
              <h3>Nếm thử tại địa phương</h3>
              <p>${esc(d.story.recommendSpot)}</p>
              <p class="spot-note">Nên liên hệ trước để hỏi tình trạng phục vụ và thời điểm có món.</p>
            </section>
            <div class="cuisine-aside-note"><span aria-hidden="true">✦</span><p>Ẩm thực ngon hơn khi được kể cùng câu chuyện về vùng đất và những người gìn giữ hương vị ấy.</p></div>
          </aside>
        </div>

        ${relatedTourHTML}

        <section class="cuisine-reviews-section">
          <div class="reviews-header">
            <h3>Cảm nhận & Bình luận yêu thích (${allReviews.length})</h3>
            <p class="micro">Chia sẻ trải nghiệm hương vị thực tế của bạn về món ăn này.</p>
          </div>

          <form id="cuisine-comment-form" class="cuisine-comment-form" data-for-dish="${esc(d.id)}">
            <div class="form-row">
              <input type="text" name="name" class="field" placeholder="Họ và tên của bạn..." required maxlength="60">
              <select name="rating" class="field" style="max-width:160px;">
                <option value="5">★★★★★ Tuyệt hảo</option>
                <option value="4">★★★★☆ Rất ngon</option>
                <option value="3">★★★☆☆ Độc đáo</option>
              </select>
            </div>
            <textarea name="comment" class="field" rows="3" placeholder="Viết cảm nhận của bạn về hương vị món ăn..." required maxlength="600"></textarea>
            <button type="submit" class="button small">Gửi bình luận của bạn ↗</button>
          </form>

          <div class="cuisine-reviews-list">
            ${allReviews.map(r => `
              <div class="cuisine-review-item">
                <div class="review-meta">
                  <b>${esc(r.name)}</b>
                  <span class="stars">${'★'.repeat(r.rating || 5)}${'☆'.repeat(5 - (r.rating || 5))}</span>
                  <small>${esc(r.date || 'Hôm nay')}</small>
                </div>
                <p>${esc(r.comment)}</p>
              </div>
            `).join('')}
          </div>
        </section>
      </article>
    `;
  }

  function openCuisine(id){
    const d = dishes.find(x => x.id === id);
    if(!d) return;
    showModal(cuisineBlogHTML(d));
    const modal = document.getElementById('modal');
    if(modal) modal.scrollTop = 0;

    // Gắn sự kiện submit bình luận mới
    const form = document.getElementById('cuisine-comment-form');
    if(form){
      form.onsubmit = function(e){
        e.preventDefault();
        const name = form.elements['name'].value.trim();
        const comment = form.elements['comment'].value.trim();
        const rating = Number(form.elements['rating'].value) || 5;
        if(!name || !comment) return;

        const dateStr = new Intl.DateTimeFormat('vi-VN', {
          day: '2-digit', month: '2-digit', year: 'numeric'
        }).format(new Date());

        addCuisineReview(d.id, {
          name, comment, rating, date: dateStr
        });

        toast('Cảm ơn bạn đã gửi cảm nhận về món ' + d.name + '!');
        openCuisine(d.id); // Reload blog modal with new comment
      };
    }
  }

  // Khởi tạo và lắng nghe sự kiện
  function initCuisine(){
    renderCuisineList();

    // Lắng nghe click filter tabs
    const filterContainer = document.getElementById('cuisine-categories');
    if(filterContainer){
      filterContainer.onclick = function(e){
        const btn = e.target.closest('[data-category]');
        if(!btn) return;
        activeCuisineCategory = btn.dataset.category;
        filterContainer.querySelectorAll('button').forEach(b => {
          b.classList.toggle('selected', b === btn);
        });
        renderCuisineList();
      };
    }

    // Lắng nghe sự kiện toàn trang cho ẩm thực (Like và Mở Blog)
    document.addEventListener('click', function(e){
      // Nút Like
      const likeBtn = e.target.closest('[data-like-id]');
      if(likeBtn){
        e.preventDefault();
        e.stopPropagation();
        const dishId = likeBtn.dataset.likeId;
        const d = dishes.find(x => x.id === dishId);
        if(!d) return;
        toggleDishLike(dishId);
        
        // Cập nhật lại tất cả nút like có id này trên trang
        const isNowLiked = isDishLiked(dishId);
        const count = getDishLikes(d);
        document.querySelectorAll(`[data-like-id="${dishId}"]`).forEach(btn => {
          btn.classList.toggle('liked', isNowLiked);
          const numEl = btn.querySelector('.like-num');
          if(numEl) numEl.textContent = count;
        });
        return;
      }

      // Nút mở modal chi tiết Blog
      const openBtn = e.target.closest('[data-open-cuisine]');
      if(openBtn){
        e.preventDefault();
        openCuisine(openBtn.dataset.openCuisine);
        return;
      }

      // Nhấp vào thân thẻ món ăn
      const card = e.target.closest('.cuisine-card');
      if(card && !e.target.closest('button')){
        e.preventDefault();
        openCuisine(card.dataset.cuisineId);
      }
    });

    // Mở trực tiếp nếu URL hash là #cuisine-[id]
    if(/^#cuisine-[a-z0-9-]+$/.test(location.hash)){
      const id = location.hash.replace('#cuisine-', '');
      openCuisine(id);
    }
  }

  // Chạy khi DOM sẵn sàng
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', initCuisine);
  } else {
    initCuisine();
  }

  // Export hàm để có thể gọi từ bên ngoài nếu cần
  globalThis.openCuisine = openCuisine;
})();
