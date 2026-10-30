'use strict';
(function(){
  const stories = globalThis.TRA_NEWS || [];
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function renderNews(){
    const grid = document.getElementById('news-story-grid');
    if(!grid || !stories.length) return;
    const [featured, ...rest] = stories;
    grid.innerHTML = `
      <article class="news-feature" data-news-id="${esc(featured.id)}">
        <img src="${esc(featured.image)}" alt="${esc(featured.imageAlt)}" loading="lazy">
        <div>
          <span class="pill">${esc(featured.status)}</span>
          <h3><button class="news-feature-title" data-news-id="${esc(featured.id)}">${esc(featured.title)}</button></h3>
          <p>${esc(featured.excerpt)}</p>
          <button class="news-read-link" data-news-id="${esc(featured.id)}">Đọc câu chuyện <span aria-hidden="true">↗</span></button>
        </div>
      </article>
      <div class="news-list">
        ${rest.map((story, index) => `
          <article class="news-list-item">
            <img class="news-thumb" src="${esc(story.image)}" alt="${esc(story.imageAlt)}" loading="lazy">
            <div class="news-item-copy">
              <p class="eyebrow">${esc(story.category)} · ${esc(story.date)}</p>
              <h3><button data-news-id="${esc(story.id)}">${esc(story.title)}</button></h3>
              <p>${esc(story.excerpt)}</p>
              <button class="news-read-link" data-news-id="${esc(story.id)}">Đọc bài <span aria-hidden="true">↗</span></button>
            </div>
          </article>`).join('')}
        <article class="news-list-item news-destination-link">
          <img class="news-thumb" src="assets/tours/ho-nui-coc.jpg" alt="Mặt hồ Núi Cốc yên bình giữa núi đồi xanh" loading="lazy">
          <div class="news-item-copy">
            <p class="eyebrow">ĐIỂM ĐẾN · HỒ NÚI CỐC</p>
            <h3><a href="https://mythainguyen.vn/vi/honuicoc" target="_blank" rel="noopener">Một khoảng trời bình yên bên hồ Núi Cốc</a></h3>
            <p>Khám phá không gian hồ và những trải nghiệm tham quan quanh vùng.</p>
            <a class="news-read-link" href="https://mythainguyen.vn/vi/honuicoc" target="_blank" rel="noopener">Đọc trên cổng du lịch <span aria-hidden="true">↗</span></a>
          </div>
        </article>
      </div>`;
  }

  function openNewsArticle(id){
    const story = stories.find(item => item.id === id);
    if(!story) return;
    const article = `
      <article class="news-article">
        <header class="news-article-header">
          <p class="eyebrow">${esc(story.category)}</p>
          <h2>${esc(story.title)}</h2>
          <div class="news-article-meta"><span>${esc(story.date)}</span><i></i><span>${esc(story.status)}</span></div>
        </header>
        <figure class="news-article-figure">
          <img src="${esc(story.image)}" alt="${esc(story.imageAlt)}">
          <figcaption>${esc(story.imageCredit)}</figcaption>
        </figure>
        <p class="news-article-lead">${esc(story.lead)}</p>
        <div class="news-article-body">
          ${story.sections.map((section, index) => `
            <section>
              <span class="news-section-number">0${index + 1}</span>
              <div><h3>${esc(section.heading)}</h3><p>${esc(section.body)}</p></div>
            </section>`).join('')}
        </div>
        <p class="news-source">${esc(story.source)}</p>
      </article>`;
    if(typeof globalThis.showModal === 'function') globalThis.showModal(article);
    else {
      const modal = document.getElementById('modal');
      const content = document.getElementById('modal-content');
      if(!modal || !content) return;
      content.innerHTML = article;
      if(!modal.open) modal.showModal();
    }
    document.getElementById('modal')?.scrollTo({top:0});
  }

  document.addEventListener('click', event => {
    const button = event.target.closest('[data-news-id]');
    if(!button) return;
    event.preventDefault();
    openNewsArticle(button.dataset.newsId);
  });

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderNews);
  else renderNews();
})();
