const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const projectRoot = __dirname;
const dist = path.join(projectRoot, 'dist');
const context = vm.createContext({ Intl });

for (const file of ['tours-data.js', 'cuisine-data.js', 'news-data.js']) {
  vm.runInContext(fs.readFileSync(path.join(dist, file), 'utf8'), context, { filename: file });
}

const plain = value => JSON.parse(JSON.stringify(value));
const tourCatalog = plain(context.TRA_CATALOG);
const cuisine = plain(context.TRA_CUISINE);
const news = plain(context.TRA_NEWS);
const bookingConfig = JSON.parse(fs.readFileSync(path.join(dist, 'data', 'tour-booking-config-v2.json'), 'utf8'));
// Preserve the visible, fictional review examples as reference data, but never index them as customer facts.
vm.runInContext(fs.readFileSync(path.join(dist, 'tour-reviews-data.js'), 'utf8'), context, { filename: 'tour-reviews-data.js' });
const demoReviewTours = plain(context.TRA_CATALOG.tours).map(tour => ({
  tour_id: tour.id,
  tour_code: tour.code,
  rating: tour.demoRating,
  review_count: tour.demoReviewCount,
  disclosure: tour.demoReviewDisclosure,
  reviews: tour.demoReviews,
}));
// The website also renders this outbound destination card beside the 3 full articles.
const destinationCard = {
  id: 'ho-nui-coc-destination-card',
  kind: 'destination_link',
  title: 'Một khoảng trời bình yên bên hồ Núi Cốc',
  category: 'ĐIỂM ĐẾN · HỒ NÚI CỐC',
  date: null,
  status: 'Liên kết tới cổng du lịch Thái Nguyên',
  excerpt: 'Khám phá không gian hồ và những trải nghiệm tham quan quanh vùng.',
  image: 'assets/tours/ho-nui-coc.jpg',
  imageAlt: 'Mặt hồ Núi Cốc yên bình giữa núi đồi xanh',
  source: 'Cổng du lịch Thái Nguyên — Hồ Núi Cốc',
  sourceUrl: 'https://mythainguyen.vn/vi/honuicoc',
  lead: '',
  sections: [],
  contentNote: 'Thẻ điểm đến dẫn tới trang ngoài; website không lưu toàn văn nội dung nguồn.',
};
const newsItems = [...news, destinationCard];
const documents = [];
const addDocument = (id, title, pageContent, metadata) => {
  const text = String(pageContent || '').replace(/\s+/g, ' ').trim();
  if (text) documents.push({ id, page_content: text, metadata });
};
const list = values => (values || []).filter(Boolean).join('; ');
const sourceRecords = sourceIds => (sourceIds || []).map(id => ({ id, ...tourCatalog.sources[id] })).filter(source => source.title || source.url);

for (const tour of tourCatalog.tours) {
  const common = {
    entity_type: 'tour', entity_id: tour.id, code: tour.code, title: tour.name,
    destinations: tour.places, destination_ids: tour.destinationIds,
    tags: tour.tags, duration_days: tour.days, duration_nights: tour.nights,
    price_min: tour.price, price_max: tour.priceMax, currency: tour.currency,
    status: tour.status, status_label: tour.statusLabel,
    source_ids: tour.sourceIds, sources: sourceRecords(tour.sourceIds),
  };

  addDocument(`${tour.code}-overview`, tour.name, [
    `${tour.code}: ${tour.name}`, tour.label, list(tour.tags),
    `Điểm đến: ${list(tour.places)}. Thời lượng: ${tour.days} ngày ${tour.nights} đêm.`,
    `Giá dự kiến: ${tour.price}–${tour.priceMax} ${tour.currency}/người lớn.`,
    tour.summary, tour.description, `Điểm nhấn: ${list(tour.highlights)}.`,
  ].join('\n'), { ...common, document_type: 'tour_overview' });

  addDocument(`${tour.code}-planning-details`, `${tour.name} — thông tin thực tế và lưu ý`, [
    `Đối tượng phù hợp: ${tour.audience}`, `Mức vận động: ${tour.difficulty}`,
    `Quy mô đoàn: ${tour.group}`, `Thời điểm: ${tour.season}`,
    `Di chuyển: ${tour.transport}`, `Điểm đón/trả: ${tour.departure}`,
    `Lịch khởi hành: ${tour.departureSchedule}`, `Ẩm thực: ${tour.food}`,
    `Lưu trú: ${tour.lodging}`, `Chính sách trẻ em: ${tour.children}`,
    `Đặt chỗ và hủy đổi: ${tour.cancellation}`, `Bảo hiểm: ${tour.insurance}`,
    `Phương án thời tiết: ${tour.weatherPlan}`, `Lưu ý: ${list(tour.notes)}.`,
    `Chuẩn bị: ${list(tour.packing)}.`, `Điều kiện cần xác nhận: ${list(tour.operationChecklist)}.`,
    `Giá: ${tour.pricingNote}`, `Khung giờ: ${tour.timingNote}`, `Địa lý: ${tour.geographyNote}`,
  ].join('\n'), { ...common, document_type: 'tour_planning_details' });

  addDocument(`${tour.code}-services`, `${tour.name} — dịch vụ bao gồm và chưa bao gồm`, [
    `Dự kiến bao gồm: ${list(tour.included)}.`,
    `Không bao gồm: ${list(tour.excluded)}.`,
  ].join('\n'), { ...common, document_type: 'tour_services' });

  for (const day of tour.itinerary || []) {
    const activities = (day.activities || []).map(item => `${item.time}: ${item.title}. ${item.description}`).join('\n');
    addDocument(`${tour.code}-day-${day.day}`, `${tour.name} — ngày ${day.day}: ${day.title}`, [
      `${tour.code}: ${tour.name}. Ngày ${day.day}: ${day.title}.`,
      `Bữa ăn: ${list(day.meals)}. Lưu trú: ${day.stay}.`, activities,
    ].join('\n'), { ...common, document_type: 'tour_itinerary_day', day_number: day.day, day_title: day.title });
  }

  // Keep a complete, human-readable record chunk alongside the focused retrieval chunks.
  const fullRecord = [
    `${tour.code}: ${tour.name}.`, tour.summary, tour.description,
    `Mã: ${tour.id}; trạng thái: ${tour.statusLabel}; tuyến: ${list(tour.places)}.`,
    `Thời lượng: ${tour.days} ngày ${tour.nights} đêm. Giá dự kiến: ${tour.price}–${tour.priceMax} ${tour.currency}/người lớn.`,
    `Giá và thời điểm: ${tour.pricingNote} ${tour.timingNote}`,
    `Đối tượng: ${tour.audience}. Độ khó: ${tour.difficulty}. Quy mô: ${tour.group}. Mùa: ${tour.season}.`,
    `Phương tiện: ${tour.transport}. Đón/trả: ${tour.departure}. Lịch khởi hành: ${tour.departureSchedule}.`,
    `Ẩm thực: ${tour.food}. Lưu trú: ${tour.lodging}.`,
    `Điểm nhấn: ${list(tour.highlights)}.`,
    ...(tour.itinerary || []).map(day => `Lịch trình ngày ${day.day} — ${day.title}. Bữa ăn: ${list(day.meals)}. Lưu trú: ${day.stay}. Hoạt động: ${(day.activities || []).map(a => `${a.time} ${a.title}: ${a.description}`).join('; ')}.`),
    `Bao gồm: ${list(tour.included)}. Không bao gồm: ${list(tour.excluded)}.`,
    `Chuẩn bị: ${list(tour.packing)}. Lưu ý: ${list(tour.notes)}.`,
    `Chính sách trẻ em: ${tour.children}. Hủy/đổi: ${tour.cancellation}. Bảo hiểm: ${tour.insurance}.`,
    `Thời tiết: ${tour.weatherPlan}. Địa lý: ${tour.geographyNote}. Điều kiện cần xác nhận: ${list(tour.operationChecklist)}.`,
    `Nguồn: ${sourceRecords(tour.sourceIds).map(s => `${s.title} (${s.url})`).join('; ')}.`,
  ].join('\n');
  addDocument(`${tour.code}-full-record`, tour.name, fullRecord, { ...common, document_type: 'tour_full_record' });
}

const flatten = (value, prefix = '') => {
  if (value == null || typeof value !== 'object') return [`${prefix}: ${value ?? 'không có'}`];
  if (Array.isArray(value)) return value.flatMap((item, index) => flatten(item, `${prefix}[${index + 1}]`));
  return Object.entries(value).flatMap(([key, item]) => flatten(item, prefix ? `${prefix}.${key}` : key));
};

for (const bookingTour of bookingConfig.tours || []) {
  const meta = {
    entity_type: 'tour_booking', entity_id: bookingTour.tourId, tour_code: bookingTour.tourCode,
    title: bookingTour.name, content_status: 'demo_simulation',
    disclaimer: bookingConfig.publicNotice,
  };
  addDocument(`booking-${bookingTour.tourCode}-options`, `${bookingTour.name} — giá và tùy chọn đặt tour mô phỏng`, [
    bookingConfig.publicNotice, bookingTour.bookingTagline,
    ...flatten(bookingTour.pricing, 'Giá'),
    ...flatten(bookingTour.departures && Object.fromEntries(Object.entries(bookingTour.departures).filter(([key]) => key !== 'list')), 'Khởi hành'),
    ...flatten(bookingTour.travelerPolicy, 'Khách đi tour'),
    ...flatten(bookingTour.transport, 'Phương tiện'),
    ...flatten(bookingTour.accommodation, 'Lưu trú'),
    ...flatten(bookingTour.addons, 'Dịch vụ thêm'),
    ...flatten(bookingTour.checkout, 'Đặt tour'),
    ...flatten(bookingTour.faq, 'Hỏi đáp'),
  ].join('\n'), { ...meta, document_type: 'tour_booking_options' });

  for (const departure of bookingTour.departures?.list || []) {
    addDocument(`booking-${departure.departureId}`, `${bookingTour.name} — lịch khởi hành mô phỏng ${departure.date}`, [
      bookingConfig.publicNotice,
      `Tour ${bookingTour.tourCode}: ngày ${departure.date}, giờ ${departure.time}; nhóm giá ${departure.fareClassLabel}.`,
      `Phụ thu mô phỏng: người lớn ${departure.surchargeAdultVND} VND, trẻ em ${departure.surchargeChildVND} VND, trẻ nhỏ ${departure.surchargeInfantVND} VND.`,
      `Sức chứa mẫu: ${departure.capacitySeats}; số đã đặt mẫu: ${departure.bookedSeatsDemoSeed}; trạng thái mẫu: ${departure.seatStatus}.`,
      departure.note,
    ].join('\n'), { ...meta, document_type: 'tour_demo_departure', departure_id: departure.departureId, departure_date: departure.date });
  }
}

addDocument('booking-global-demo-rules', 'Quy tắc giá, tuổi và đặt tour mô phỏng', [
  bookingConfig.publicNotice,
  bookingConfig.sourceNote,
  `Tuổi và chính sách: ${flatten(bookingConfig.ageBands, 'Nhóm tuổi').join('; ')}.`,
  `Công thức: ${flatten(bookingConfig.pricingEngine, 'Tính giá').join('; ')}.`,
  `Quy tắc demo: ${flatten(bookingConfig.demoRules, 'Quy tắc').join('; ')}.`,
  `Hỏi đáp chung: ${(bookingConfig.faqsGlobal || []).map(f => `Hỏi: ${f.q} Đáp: ${f.a}`).join('\n')}`,
].join('\n'), { entity_type: 'tour_booking', document_type: 'booking_global_rules', content_status: 'demo_simulation' });

for (const item of cuisine) {
  const story = item.story || {};
  addDocument(`cuisine-${item.id}`, item.name, [
    `${item.name}${item.subName ? ` (${item.subName})` : ''}.`,
    `Khu vực: ${item.region}. Nhóm: ${item.category}.`,
    item.summary, `Hương vị: ${list(item.tasteNotes)}.`,
    `Nguồn gốc: ${story.origin}`, `Nguyên liệu: ${story.ingredients}`,
    `Cách làm: ${story.making}`, `Trải nghiệm: ${story.experience}`,
    `Gợi ý nơi tìm: ${story.recommendSpot}`, `Gợi ý thưởng thức: ${story.tableMoment}`,
    `Ghi chú biên tập: ${story.journalNote}`,
  ].join('\n'), {
    entity_type: 'cuisine', entity_id: item.id, document_type: 'cuisine_item',
    title: item.name, region: item.region, category: item.category,
    related_tour_id: story.relatedTourId ?? null,
    provenance: 'Nội dung biên tập trên website; không có nguồn tham khảo riêng trong bản ghi.',
    engagement_data_excluded: ['likes', 'reviews'],
  });
}

for (const article of news) {
  const articleMeta = {
    entity_type: 'news', entity_id: article.id, title: article.title,
    category: article.category, date: article.date, status: article.status,
    source: article.source, image_alt: article.imageAlt,
  };
  addDocument(`news-${article.id}-summary`, article.title, [
    `${article.title}.`, `Chuyên mục: ${article.category}. Ngày biên tập/đăng: ${article.date}. Trạng thái: ${article.status}.`,
    article.excerpt, article.lead, `Nguồn ghi trong bài: ${article.source}`,
  ].join('\n'), { ...articleMeta, document_type: 'news_summary', section_heading: null });
  for (const [index, section] of (article.sections || []).entries()) {
    addDocument(`news-${article.id}-section-${index + 1}`, `${article.title} — ${section.heading}`, [
      `${article.title}. ${section.heading}.`, section.body, `Nguồn ghi trong bài: ${article.source}`,
    ].join('\n'), { ...articleMeta, document_type: 'news_section', section_heading: section.heading, section_number: index + 1 });
  }
}

addDocument(`news-${destinationCard.id}`, destinationCard.title, [
  `${destinationCard.title}.`,
  `Chuyên mục: ${destinationCard.category}. Địa điểm: Hồ Núi Cốc, Thái Nguyên.`,
  destinationCard.excerpt,
  destinationCard.contentNote,
  `Nguồn đọc thêm: ${destinationCard.sourceUrl}`,
].join('\n'), {
  entity_type: 'news', entity_id: destinationCard.id, title: destinationCard.title,
  category: destinationCard.category, date: null, status: destinationCard.status,
  source: destinationCard.source, source_url: destinationCard.sourceUrl,
  image_alt: destinationCard.imageAlt, kind: destinationCard.kind,
  document_type: 'news_destination_link',
});

const output = {
  schema_version: '1.0.0',
  generated_at: new Date().toISOString(),
  language: 'vi',
  site: { name: 'Trà Journey', subject: 'Du lịch Thái Nguyên và miền xanh Ba Bể' },
  purpose: 'Dữ liệu nguồn có cấu trúc và tài liệu ngữ nghĩa để lập chỉ mục cho chatbot RAG.',
  rag_format: {
    document_fields: ['id', 'page_content', 'metadata'],
    embedding_vectors_included: false,
    note: 'Tạo embedding từ page_content; giữ metadata để trích dẫn và lọc theo loại nội dung, mã tour, địa điểm, chuyên mục hoặc ngày.',
  },
  collections: {
    tours: {
      count: tourCatalog.tours.length,
      schema_version: tourCatalog.schemaVersion,
      updated_at: tourCatalog.updatedAt,
      editorial_note: tourCatalog.editorialNote,
      sources: tourCatalog.sources,
      destinations: tourCatalog.places,
      shared_terms: tourCatalog.common,
      items: tourCatalog.tours,
    },
    tour_booking: {
      schema_version: bookingConfig.schemaVersion,
      generated_at: bookingConfig.generatedAt,
      mode: bookingConfig.mode,
      public_notice: bookingConfig.publicNotice,
      source_note: bookingConfig.sourceNote,
      editorial_note: 'Toàn bộ cấu hình booking hiện có được giữ để tham khảo. Lịch, chỗ, phí cộng thêm, phương thức và chính sách ở cấu hình này đều là mô phỏng; không sử dụng để xác nhận giao dịch thật.',
      items: bookingConfig.tours,
      global_configuration: Object.fromEntries(Object.entries(bookingConfig).filter(([key]) => !['tours'].includes(key))),
    },
    tour_demo_reviews: {
      count: demoReviewTours.reduce((sum, tour) => sum + (tour.reviews || []).length, 0),
      indexed_in_documents: false,
      editorial_note: 'Tên, điểm số và trải nghiệm đánh giá là hư cấu để minh họa giao diện; chỉ lưu để kiểm kê dữ liệu đang hiển thị và không tạo RAG documents từ nội dung này.',
      items: demoReviewTours,
    },
    cuisine: {
      count: cuisine.length,
      editorial_note: 'Nội dung mô tả ẩm thực do website biên tập; số lượt thích và nhận xét chỉ là dữ liệu giao diện, không phải nguồn sự kiện.',
      items: cuisine,
    },
    news: {
      count: newsItems.length,
      full_article_count: news.length,
      editorial_note: 'Gồm 3 bài có nội dung đầy đủ và 1 thẻ điểm đến liên kết ra cổng du lịch; thẻ ngoài không có toàn văn. Tin tức giữ nguyên ngày, trạng thái và nguồn ghi trong từng bài. Sự kiện theo thời gian cần được kiểm tra lại trước khi trả lời như thông tin hiện hành.',
      items: newsItems,
    },
  },
  document_count: documents.length,
  documents,
};

const outputPath = path.join(dist, 'data', 'rag-knowledge-base.json');
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(output, null, 2) + '\n');
console.log(`Exported ${tourCatalog.tours.length} tours, ${cuisine.length} cuisine items, ${news.length} full news articles plus ${newsItems.length - news.length} destination link, booking configuration and ${demoReviewTours.reduce((sum, tour) => sum + (tour.reviews || []).length, 0)} excluded demo reviews as ${documents.length} RAG documents.`);
