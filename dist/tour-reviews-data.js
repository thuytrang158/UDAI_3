'use strict';
// Fictional names and experiences for the demonstration only; never verified-customer records.
(() => {
 const make=(name,party,rating,title,body,guide,planning,value)=>({name,party,rating,title,body,isDemo:true,verified:false,scores:{guide,planning,value}});
 const reviews={
 TJ01:[
 make('Nguyễn Minh Anh','Đi cùng gia đình',5,'Một ngày nhẹ nhàng mà nhiều kỷ niệm','Mình thích nhất buổi thưởng trà, được nghe giải thích từng bước nên thấy chuyến đi có chiều sâu hơn việc chỉ chụp ảnh. Lịch trình có khoảng nghỉ, bố mẹ mình theo được khá thoải mái.',5,5,5),
 make('Trần Hoàng Nam','Đi cùng bạn bè',5,'Đồi chè buổi sáng rất hợp để chụp ảnh','Nhóm mình có đủ thời gian đi bộ và chụp ảnh mà không bị gọi lên xe liên tục. Bạn hướng dẫn nói chuyện gần gũi, bữa trưa vừa miệng. Phần bên hồ giúp cả nhóm thư giãn trước khi về.',5,5,4),
 make('Lê Thu Hà','Đi cùng người thương',4,'Hợp cho cuối tuần ngắn','Phần trà thú vị hơn mình nghĩ, còn đoạn đi hồ khá thư thả. Mình muốn thời gian ở đồi chè dài hơn một chút; nếu quay lại sẽ chọn tour riêng để ở lâu hơn.',5,4,4)
 ],
 TJ02:[
 make('Phạm Ngọc Linh','Đi cùng gia đình',5,'Cả nhà có thời gian ở bên nhau','Chuyến này không quá nhiều điểm nên hai bé không bị mệt vì lên xuống xe. Buổi picnic là phần cả nhà thích nhất, có chỗ ngồi nghỉ và thời gian trò chuyện thay vì chạy theo lịch.',5,5,5),
 make('Vũ Đức Anh','Đi cùng đồng nghiệp',4,'Một ngày đổi không khí dễ chịu','Nhóm mình thích cách bố trí thưởng trà trước rồi mới picnic. Phần ăn nhẹ ổn, nhưng nếu có thêm món ít ngọt thì sẽ hợp với cả nhóm hơn. Nhìn chung lịch trình dễ theo.',4,5,4),
 make('Đỗ Mai Phương','Đi cùng bạn bè',5,'Đi ít điểm nhưng cảm nhận được nhiều','Mình đã có một buổi chiều đọc sách và ngắm cảnh đúng nghĩa. Xe di chuyển vừa phải, bạn hướng dẫn chủ động nhắc giờ tập trung nên nhóm không phải tự lo nhiều việc.',5,5,5)
 ],
 TJ03:[
 make('Bùi Quang Huy','Đi cùng gia đình',5,'Câu chuyện lịch sử khiến chuyến đi đáng nhớ','Thay vì ghé thật nhiều di tích, đoàn dành thời gian nghe thuyết minh và đặt câu hỏi. Mình thích cách kể dễ hiểu, có liên hệ với từng nơi đang đứng. Bố mình đặc biệt thích buổi sáng ở ATK.',5,5,5),
 make('Nguyễn Thảo Vy','Đi cùng bạn bè',4,'Một ngày vừa học thêm vừa thư giãn','Lịch sử buổi sáng và cảnh thác buổi chiều kết hợp khá hay. Có vài đoạn bậc thang nên cần đi giày thoải mái. Mình mong thời gian nghỉ trưa thêm khoảng 15 phút.',5,4,4),
 make('Trần Quốc Bảo','Đi cùng đồng nghiệp',5,'Thuyết minh có chiều sâu','Phần ATK được chuẩn bị kỹ, không có cảm giác nghe giới thiệu cho xong. Bữa trưa đơn giản nhưng hợp khẩu vị, buổi chiều ngắm thác giúp cả nhóm thả lỏng sau buổi tham quan.',5,5,4)
 ],
 TJ04:[
 make('Hoàng Ngọc Anh','Đi cùng bạn bè',5,'Hai ngày nhiều trải nghiệm khác nhau','Buổi đầu nhẹ nhàng ở chùa và khu dân cư, hôm sau mới dành sức lên hang nên lịch khá hợp lý. Người dẫn đường thường xuyên chờ cả nhóm, mình không cảm thấy bị thúc ép.',5,5,4),
 make('Đặng Minh Khoa','Đi cùng người thương',4,'Thích phần đi hang, cần giày tốt','Đường lên xuống có đoạn dốc nên mình mừng vì đã mang giày bám. Chỗ nghỉ đơn giản, sạch sẽ theo cảm nhận của mình. Nếu phòng cách âm tốt hơn thì buổi tối sẽ dễ ngủ hơn.',5,4,4),
 make('Lê Khánh Chi','Đi cùng bạn bè',4,'Không chỉ là đến chụp ảnh rồi về','Mình thích phần nghe chuyện địa phương và bữa cơm buổi tối. Tuyến hang vừa sức nhóm, nhưng người ít vận động nên chuẩn bị trước. Xe đi đoạn cuối hơi chậm, bù lại lịch có thời gian đệm.',4,4,4)
 ],
 TJ05:[
 make('Phan Tuấn Kiệt','Đi cùng bạn bè',5,'Một ngày vận động, một ngày nghỉ đúng ý','Cách tách ngày đi suối và ngày hồ–trà rất hợp lý. Nhóm được phổ biến tuyến trước khi đi, ai chậm hơn cũng có thời gian theo. Ngày thứ hai nhẹ nhàng giúp mình không thấy chuyến đi quá đuối.',5,5,5),
 make('Nguyễn Hoài An','Đi cùng đồng nghiệp',4,'Cần chuẩn bị thể lực nhưng rất đáng trải nghiệm','Mình đi bộ thường xuyên mà vẫn thấy vài đoạn khá tốn sức. Điểm cộng là hướng dẫn nhắc cách đặt chân và giữ khoảng cách. Mình muốn phần hướng dẫn chuẩn bị hành lý gửi sớm hơn.',5,4,4),
 make('Trịnh Gia Hân','Đi cùng bạn bè',5,'Thích nhịp đi vừa với nhóm','Mình không muốn một chuyến chạy thành tích, nên rất thích việc có điểm nghỉ và không cố đi thêm tuyến khó. Bữa tối sau ngày vận động ngon miệng, buổi thưởng trà hôm sau là kết thúc đẹp.',5,5,5)
 ],
 TJ06:[
 make('Đỗ Bảo Ngọc','Đi cùng người thương',5,'Ba Bể theo một nhịp thật chậm','Ở cùng một nơi hai đêm nên mình có cảm giác thực sự được nghỉ. Buổi đi thuyền có nhiều khoảng yên lặng để ngắm cảnh. Chủ nhà trong kịch bản trải nghiệm rất gần gũi, bữa ăn tạo cảm giác ấm cúng.',5,5,5),
 make('Ngô Thành Đạt','Đi cùng gia đình',4,'Lịch trình có khoảng nghỉ hợp lý','Phần rừng trúc đẹp nhưng có dốc, mình nghĩ nên đọc kỹ phần mức vận động trước khi chọn. Gia đình thích ngày ở hồ vì không phải liên tục chuyển xe. Phòng nghỉ ở mức cơ bản, phù hợp kỳ vọng.',5,4,4),
 make('Võ Thanh Trúc','Đi cùng bạn bè',5,'Chuyến đi để trò chuyện nhiều hơn','Nhóm mình thích buổi chiều tự do ở nơi nghỉ, không phải hoạt động nào cũng lên lịch kín. Thuyền và bữa ăn được sắp xếp thuận tiện; những đoạn di chuyển dài có dừng nghỉ nên đỡ mệt.',5,5,4)
 ],
 TJ07:[
 make('Lương Minh Đức','Đi cùng bạn bè',5,'Hợp với người thích ảnh phong cảnh','Mình thích việc dành hẳn một buổi cho Sam Chiêm, có thời gian tìm góc chụp và ngồi ngắm cảnh. Không cố ghép quá nhiều điểm nên dù có chặng xe dài, trải nghiệm vẫn thoải mái.',5,5,4),
 make('Nguyễn Yến Nhi','Đi cùng người thương',4,'Những khoảng trời rộng rất đáng nhớ','Buổi ở thảo nguyên là điểm nhấn của chuyến đi. Đoạn đường tiếp cận cần kiên nhẫn và giày dễ đi. Mình mong phần thông tin về trung chuyển được mô tả rõ hơn ngay lúc xem tour.',4,4,4),
 make('Phạm Hữu Phúc','Đi cùng bạn bè',4,'Chuyến đi gọn, phù hợp nhóm nhỏ','Sam Chiêm và Bản Chang đem lại hai khung cảnh khác nhau. Đồ ăn khá dễ dùng, chỗ nghỉ đáp ứng nhu cầu cơ bản. Lần sau mình muốn thêm thời gian ở hồ trước khi trở về.',5,4,4)
 ],
 TJ08:[
 make('Trần Nhật Minh','Đi cùng bạn bè',5,'Dành riêng một ngày cho hang là lựa chọn đúng','Mình thích cách lịch trình không ghép thêm điểm sau ngày khám phá hang. Phần kiểm tra trang bị và phổ biến quy tắc làm nhóm hiểu rõ những gì sẽ tham gia. Tối về chỉ cần ăn và nghỉ.',5,5,5),
 make('Lê Phương Thảo','Nhóm yêu khám phá',4,'Một trải nghiệm cần chuẩn bị nghiêm túc','Mình đã đọc kỹ yêu cầu thể lực nên không bị bất ngờ khi phải vận động lâu. Đội hướng dẫn giải thích rõ từng đoạn. Nếu có thêm danh sách đồ cần mang dạng checklist từ sớm thì sẽ tiện hơn.',5,4,4),
 make('Đặng Quốc Khánh','Đi cùng bạn bè',5,'Ngày hồ nhẹ nhàng trước hành trình lớn','Buổi đi hồ giúp cả nhóm làm quen trước ngày vận động. Ở cùng một nơi hai đêm rất tiện để cất đồ và nghỉ ngơi. Mình đánh giá cao việc có giới hạn tuyến, không cố đi xa chỉ để đủ điểm.',5,5,4)
 ],
 TJ09:[
 make('Nguyễn Tú Anh','Đi cùng gia đình',5,'Lịch sử và thiên nhiên kết hợp rất có duyên','Mình thích sự chuyển đổi từ vùng trà sang ATK rồi lên hồ. Mỗi nơi mang một câu chuyện riêng, không bị lặp cảm giác. Hai đêm ở Ba Bể giúp gia đình nghỉ lại đủ lâu sau chặng chuyển vùng.',5,5,5),
 make('Phạm Văn Long','Đi cùng người thương',4,'Bốn ngày phong phú, nên chuẩn bị cho chặng xe','Lịch có những ngày chuyển vùng dài nhưng đã dành riêng thời gian, không quá vội. Mình thích phần thuyết minh ATK và rừng trúc nhất. Bữa ăn có thể đổi món nhiều hơn ở các ngày cuối.',5,4,4),
 make('Hoàng Mai Linh','Đi cùng bạn bè',5,'Một chuyến đi có nhiều điều để kể','Nhóm mình thích cả trải nghiệm trà và buổi đi thuyền. Hướng dẫn chủ động báo kế hoạch ngày hôm sau, nên ai cũng dễ chuẩn bị. Chuyến đi cân bằng được tham quan và khoảng nghỉ.',5,5,4)
 ],
 TJ10:[
 make('Vũ Khánh Hòa','Đi cùng bạn bè',5,'Năm ngày để thấy nhiều sắc thái của miền xanh','Mỗi chặng có một khung cảnh khác nhau, từ đồi chè đến thảo nguyên rồi mặt hồ. Việc ở hai đêm mỗi nơi giúp mình không phải liên tục đóng mở hành lý. Ngày nghỉ ở Ba Bể là phần mình thích nhất.',5,5,5),
 make('Trần Hải Yến','Đi cùng người thương',4,'Hành trình đẹp nhưng cần dành đủ thời gian','Mình thích đi nhiều nơi nên tuyến này khá đúng ý. Có các chặng xe dài, vì vậy không nên chọn nếu chỉ muốn nghỉ ở một resort. Phần chụp ảnh tại thảo nguyên được bố trí thoải mái.',5,4,4),
 make('Nguyễn Anh Duy','Nhóm yêu nhiếp ảnh',5,'Không phải cuộc đua qua các điểm check-in','Điểm cộng là tour không cố thêm một tuyến hang vào lịch vốn đã phong phú. Có thời gian nhìn cảnh, chụp ảnh và trò chuyện. Mình mong có thêm lựa chọn thực đơn chay rõ ràng khi đăng ký.',5,5,4)
 ]};
 const highlights={
 TJ01:['Thưởng trà cùng người làm chè','Một chiều thư thả bên hồ Núi Cốc'],TJ02:['Picnic và phần ăn nhẹ ven hồ','Lịch nhẹ nhàng cho cả gia đình'],TJ03:['Nghe chuyện lịch sử tại ATK','Ngắm thác Khuôn Tát giữa màu xanh'],TJ04:['Khám phá hang với người dẫn đường','Một đêm cảm nhận nhịp sống Võ Nhai'],TJ05:['Ngày riêng cho tuyến Cửa Tử cơ bản','Hồi phục bên hồ và chén trà'],TJ06:['Hai đêm ở lại miền hồ Ba Bể','Dạo rừng trúc, thuyền ngắm hồ'],TJ07:['Thời gian chụp ảnh trên thảo nguyên','Dạo bờ hồ Bản Chang'],TJ08:['Ngày riêng khám phá hang có tổ chức','Hai đêm nghỉ, đủ thời gian hồi phục'],TJ09:['Trà, lịch sử và thiên nhiên trong một tuyến','Hai đêm nghỉ ở Ba Bể'],TJ10:['Năm điểm đến, nhiều sắc thái cảnh quan','Giảm đổi phòng: hai đêm mỗi nơi']};
 for(const t of TRA_CATALOG.tours){
   t.demoReviews=reviews[t.code];
   t.demoRating=Number((t.demoReviews.reduce((s,r)=>s+r.rating,0)/t.demoReviews.length).toFixed(1));
   t.demoReviewCount=t.demoReviews.length;
   t.demoReviewDisclosure='Đánh giá mô phỏng: tên người viết, điểm số và trải nghiệm đều là nội dung hư cấu để minh họa giao diện, không phải phản hồi khách hàng thực tế.';
   t.cardHighlights=highlights[t.code];
   t.serviceBadges=['Xe riêng',t.nights?t.nights+' đêm lưu trú':'Đi về trong ngày','Bữa ăn theo lịch'];
 }
})();
