'use strict';
// Editorial seed data. Prices and departure schedules are proposals, not supplier offers.
globalThis.TRA_CATALOG = (() => {
  const sources = {
    tea:{title:'Cổng du lịch Thái Nguyên — Điểm du lịch cộng đồng Tân Cương',url:'https://mythainguyen.vn/vi/tancuong11'},
    lake:{title:'Cổng du lịch Thái Nguyên — Hồ Núi Cốc',url:'https://mythainguyen.vn/vi/honuicoc'},
    regional:{title:'Báo Thái Nguyên — Thái Nguyên vào mùa du lịch',url:'https://baothainguyen.vn/van-hoa/du-lich-thai-nguyen/202604/thai-nguyen-vao-mua-du-lich-d15161d'},
    heritage:{title:'Cổng du lịch Thái Nguyên — Chương trình tham quan',url:'https://mythainguyen.vn/vi/detailnews/?id=news_187&t=chuong-trinh-tham-quan-du-lich-thai-nguyen'},
    waterfall:{title:'Thái Nguyên 360 — Thác Khuôn Tát',url:'https://thainguyen360.com.vn/648cB6Hc987938E'},
    phoenix:{title:'Báo Thái Nguyên — Phụ nữ Mỏ Gà làm du lịch cộng đồng, 25/10/2023',url:'https://baothainguyen.vn/file/e7837c027f6ecd14017ffa4e5f2a0e34/upload/xdata/202310/20231025064953trang_1-2_25-10-2023chuan.pdf'},
    pagoda:{title:'Thông tin tham khảo Chùa Hang — Kim Sơn Tự',url:'https://www.hagiangtrekkingtours.com/hang-pagoda-chua-hang.asp'},
    stream:{title:'Cổng tỉnh Thái Nguyên — Cửa Tử, điểm du lịch trải nghiệm',url:'https://cms.thainguyen.vn/web/guest/tin-du-lich-noi-bat/-/asset_publisher/lVjDI9uKhOvh/content/cua-tu-iem-du-lich-trai-nghiem-hap-dan-tai-thai-nguyen'},
    babe:{title:'Cục Du lịch Quốc gia Việt Nam — Ba Be Lake',url:'https://vietnamtourism.gov.vn/en/printer/14483?type=1'},
    bamboo:{title:'Cục Du lịch Quốc gia Việt Nam — Du lịch cộng đồng Ba Bể, Phiêng Phàng',url:'https://nongthon.vietnamtourism.gov.vn/huyen-ba-be-tinh-bac-kan-khai-thac-tiem-nang-phat-trien-du-lich/'},
    prairie:{title:'Báo Thái Nguyên — Có một thảo nguyên Sam Chiêm tại Thái Nguyên',url:'https://baothainguyen.vn/van-hoa/202507/co-mot-thao-nguyen-sam-chiem-tai-thai-nguyen-3b80404'},
    chang:{title:'TravelViet — Hồ Bản Chang',url:'https://travelviet.net/vn/travel/bac-kan/ho-ban-chang'},
    cave:{title:'Umove Adventure — Thông tin tham khảo đặc điểm hang Thẳm Phầy',url:'https://www.umoveadventure.com/vi/sup-caving-ba-be-ky-thu.html'}
  };
  const places = [
    {id:'tan-cuong',name:'Đồi chè Tân Cương',region:'Tân Cương',lat:21.5270,lng:105.7540,sourceIds:['tea']},
    {id:'atk',name:'ATK Định Hóa',region:'Định Hóa',lat:21.8906,lng:105.6322,sourceIds:['heritage']},
    {id:'nui-coc',name:'Hồ Núi Cốc',region:'Khu vực Đại Từ',lat:21.5710,lng:105.6815,sourceIds:['lake']},
    {id:'phuong-hoang',name:'Hang Phượng Hoàng - Suối Mỏ Gà',region:'Khu vực Võ Nhai',lat:21.7225,lng:105.9928,sourceIds:['phoenix']},
    {id:'khuon-tat',name:'Thác Khuôn Tát',region:'Khu vực Định Hóa',lat:21.8967,lng:105.6178,sourceIds:['waterfall']},
    {id:'ghenh-che',name:'Hồ Ghềnh Chè',region:'Khu vực Sông Công',lat:21.4678,lng:105.7958,sourceIds:['regional']},
    {id:'chua-hang',name:'Chùa Hang',region:'Kim Sơn Tự, khu vực trung tâm Thái Nguyên',lat:21.6094,lng:105.8572,sourceIds:['pagoda']},
    {id:'cua-tu',name:'Suối Cửa Tử',region:'Khu vực Đại Từ',lat:21.6231,lng:105.5722,sourceIds:['stream']},
    {id:'ba-be',name:'Hồ Ba Bể',region:'Khu vực Ba Bể',lat:22.4083,lng:105.6167,sourceIds:['babe']},
    {id:'sam-chiem',name:'Thảo nguyên Sam Chiêm',region:'Hiệp Lực, khu vực Ngân Sơn',lat:22.4667,lng:105.9833,sourceIds:['prairie']},
    {id:'ban-chang',name:'Hồ Bản Chang',region:'Khu vực Đức Vân cũ, Ngân Sơn',lat:22.4417,lng:105.9333,sourceIds:['chang']},
    {id:'yen-duong',name:'Rừng trúc Yến Dương',aliases:['Rừng trúc Yên Dương','Rừng trúc Pù Lầu','Rừng trúc Phiêng Phàng'],region:'Phiêng Phàng, khu vực Ba Bể',lat:22.3850,lng:105.7500,sourceIds:['bamboo']},
    {id:'tham-phay',name:'Hang Thẳm Phầy',aliases:['Hang Thẩm Phầy'],region:'Khu vực Ba Bể',lat:22.3556,lng:105.6583,sourceIds:['cave']}
  ];
  const common = {
    status:'draft_itinerary',statusLabel:'Lịch trình đề xuất · Chưa mở bán',currency:'VND',reviewCount:0,rating:null,
    departure:'Đón và trả tại điểm hẹn trong khu vực trung tâm Thái Nguyên. Địa chỉ cụ thể được xác nhận khi chốt đoàn.',
    departureSchedule:'Theo yêu cầu đoàn riêng; chưa công bố ngày khởi hành cố định hoặc số chỗ còn trống.',
    pricingNote:'Khoảng giá biên tập để lập kế hoạch, tính cho 1 người lớn trong đoàn 10 khách, đi ngày thường, xe riêng và lưu trú tiêu chuẩn địa phương. Chưa có báo giá xác nhận từ nhà cung cấp; chưa bao gồm VAT nếu phát sinh. Đoàn ít người, dịp lễ và phòng riêng cần báo lại giá.',
    timingNote:'Giờ trong lịch trình là khung dự kiến, đã dành khoảng đệm cho đón khách và nghỉ dọc đường; chưa phải thời gian dẫn đường đã đo thực địa. Thứ tự có thể đổi theo giao thông, thời tiết và lịch tiếp đón.',
    geographyNote:'Dùng tên khu vực quen thuộc Đại Từ, Võ Nhai, Sông Công, Định Hóa, Ba Bể, Ngân Sơn để nhận diện tuyến; không coi đây là địa chỉ hành chính hiện hành đầy đủ. Yên Dương được chuẩn hóa thành Yến Dương; Chùa Hang được hiểu là Kim Sơn Tự gần trung tâm Thái Nguyên.',
    included:['Xe riêng đưa đón và di chuyển theo lịch trình, phân bổ trên đoàn 10 người.','Hướng dẫn viên tiếng Việt theo chương trình; thuyết minh tại điểm khi đặt được dịch vụ.','Các bữa ăn ghi trong từng ngày; nước uống cơ bản trên xe.','Ngân sách vé vào điểm có thu phí trong tuyến cơ bản; danh mục và mức phí cần xác nhận trước khi bán.'],
    excluded:['Di chuyển từ nơi cư trú đến điểm đón Thái Nguyên và chiều về.','Bữa sáng ngày đầu; đồ uống gọi thêm, mua sắm, tiền tip tự nguyện và chi tiêu riêng.','VAT nếu phát sinh; phụ thu ngày lễ, phòng đơn, nâng hạng dịch vụ.','Hoạt động tự chọn không ghi trong phần bao gồm; chương trình văn nghệ, SUP/kayak và hoạt động mạo hiểm bổ sung.'],
    children:'Chưa áp dụng biểu giá trẻ em cố định. Báo giá theo tuổi, chiều cao, ghế xe, suất ăn và nhu cầu giường. Tour trekking/hang nước cần đơn vị chuyên môn xác nhận điều kiện tham gia; không mặc định phù hợp trẻ nhỏ.',
    cancellation:'Chính sách đặt cọc, hủy/đổi và hoàn tiền sẽ được thống nhất bằng văn bản với đơn vị vận hành trước khi thanh toán; website chưa thu cọc. Nếu phải thay hoạt động vì thời tiết, cần thông báo phương án và chênh lệch dịch vụ để khách đồng ý.',
    insurance:'Trước khi mở bán phải xác nhận bảo hiểm phù hợp phạm vi hoạt động; tour trekking và hang nước cần kiểm tra riêng điều khoản và loại trừ. Bộ dữ liệu không khẳng định đã mua bảo hiểm.',
    packing:['Giày đế bám, trang phục gọn, mũ và áo khoác nhẹ.','Bình nước cá nhân, vật dụng vệ sinh, thuốc đang dùng và túi đựng rác.','Giấy tờ tùy thân phục vụ lưu trú; báo trước nhu cầu ăn chay, dị ứng và khả năng vận động.'],
    operationChecklist:['Khảo sát lại đường đi và điểm đón/trả, thời gian xe, khả năng tiếp cận của loại xe dự kiến.','Xác nhận quyền tiếp cận, giờ mở cửa, dịch vụ, giá vé, suất ăn và nơi lưu trú.','Chốt nhà cung cấp, hướng dẫn viên, điều kiện thời tiết, phương án thay thế và liên hệ hỗ trợ.','Thay ảnh minh họa bằng ảnh đúng điểm đến có quyền sử dụng; không tạo đánh giá giả.']
  };
  const day=(title,meals,stay,blocks)=>({title,meals,stay,activities:blocks.map(([time,title,description])=>({time,title,description}))});
  const list=[
    {id:101,code:'TJ01',slug:'huong-tra-sac-ho',name:'Hương trà, sắc hồ — Một ngày chạm miền xanh',destinationIds:['tan-cuong','nui-coc'],days:1,price:790000,priceMax:990000,tags:['Thiên nhiên','Văn hóa','Gia đình','Trải nghiệm Trà'],label:'LẦN ĐẦU ĐẾN MIỀN TRÀ',image:'tea.jpg',imageCaption:'Đồi chè Tân Cương · Ảnh nguồn cổng du lịch Thái Nguyên',
      summary:'Hòa mình vào đồi chè Tân Cương xanh ngát, trải nghiệm hái chè cùng nghệ nhân và thả hồn thư thái trên du thuyền thưởng ngoạn hồ Núi Cốc thơ mộng.',
      description:'Một ngày vừa đủ để làm quen với hai sắc thái của miền trà: gần gũi trong câu chuyện người làm chè và khoáng đạt giữa không gian mặt hồ. Chuyến đi ưu tiên thưởng thức, trò chuyện và những khoảng nghỉ, phù hợp để mở đầu bộ sưu tập kỷ niệm Thái Nguyên của bạn.',
      audience:'Khách lần đầu đến Thái Nguyên, cặp đôi, gia đình có khả năng đi bộ nhẹ; nhóm bạn muốn đi về trong ngày.',difficulty:'Nhẹ — đi bộ trên lối tham quan và đồi chè; có đoạn dốc ngắn.',group:'10–20 khách; đoàn nhỏ báo giá riêng.',season:'Ưu tiên ngày khô ráo, thời tiết dịu. Trải nghiệm hái chè tùy lứa chè và lịch của cơ sở, không cam kết có quanh năm.',transport:'Xe riêng; trung tâm → Tân Cương dự trù 30–60 phút, Tân Cương → hồ Núi Cốc 45–75 phút, về trung tâm 45–75 phút.',
      highlights:['Tìm hiểu từ búp chè đến chén trà cùng cơ sở địa phương.','Khoảng thời gian chụp ảnh trên lối đi được phép giữa đồi chè.','Một buổi chiều ven hồ, có lựa chọn đi thuyền nếu điều kiện phù hợp.'],
      itinerary:[day('Từ đồi chè đến mặt hồ',['Trưa'],'Không lưu trú',[
        ['07:30–08:30','Đón khách, về Tân Cương','Gặp hướng dẫn viên tại trung tâm, kiểm tra danh sách đoàn và di chuyển về vùng chè; giới thiệu câu chuyện của hành trình.'],
        ['08:30–11:15','Chậm lại giữa hương trà','Dạo lối giữa đồi chè, chụp ảnh theo hướng dẫn, gặp cơ sở làm trà và tìm hiểu các bước chế biến. Thưởng trà; hoạt động hái hoặc sao chè chỉ thực hiện khi cơ sở xác nhận.'],
        ['11:15–12:30','Bữa trưa miền trà','Dùng bữa tại cơ sở đã đặt, thực đơn gợi ý cơm, rau theo mùa và món mặn địa phương; dành thời gian nghỉ.'],
        ['12:30–15:45','Chiều bên hồ Núi Cốc','Di chuyển sang hồ, đi bộ tại khu vực mở cửa, tìm góc ngắm cảnh. Có khoảng 45–60 phút cho chuyến thuyền tự chọn; khách không đi thuyền nghỉ tại điểm hẹn ven hồ.'],
        ['15:45–17:00','Trở về','Tập trung đoàn, về điểm đón tại trung tâm; kết thúc chương trình sau khi kiểm tra tư trang.']
      ])],includedExtra:['Một buổi thưởng trà cơ bản tại cơ sở được đặt trước.'],excludedExtra:['Vé thuyền hồ Núi Cốc, trò chơi và trải nghiệm trà chuyên sâu nếu có phụ thu.'],lodging:'Không có đêm nghỉ; có thời gian nghỉ trưa tại nhà hàng.',food:'01 bữa trưa; thực đơn theo mùa và nhu cầu ăn kiêng đã báo trước.',notes:['Không hái chè hoặc đi vào khu sản xuất khi chưa được đồng ý.','Nếu đi thuyền: mặc áo phao, tuân thủ sức chứa và hướng dẫn của người vận hành.'],weatherPlan:'Nếu mưa, ưu tiên không gian thưởng trà trong nhà, giảm phần đi đồi; bỏ thuyền khi thời tiết không phù hợp, điều chỉnh thời gian ven hồ.'},
    {id:102,code:'TJ02',slug:'tra-som-ho-chieu',name:'Trà sớm, hồ chiều — Picnic bên Ghềnh Chè',destinationIds:['tan-cuong','ghenh-che'],days:1,price:850000,priceMax:1090000,tags:['Gia đình','Nghỉ dưỡng','Thiên nhiên','Dã ngoại & Picnic'],label:'MỘT NGÀY BÊN NHAU',image:'tea.jpg',imageCaption:'Ảnh Tân Cương, điểm dừng buổi sáng của tour; chưa có ảnh Hồ Ghềnh Chè.',
      summary:'Thưởng thức ấm trà sớm tinh khôi giữa triền đồi Tân Cương, thảnh thơi picnic ven hồ Ghềnh Chè lộng gió và tận hưởng không gian gắn kết gia đình trọn vẹn.',
      description:'Không đặt mục tiêu đi thật nhiều, hành trình này dành phần lớn buổi chiều cho cả nhóm ở cạnh nhau. Sau sắc xanh của đồi chè là một điểm dã ngoại ven Ghềnh Chè, nơi bạn có thể đọc sách, chụp ảnh gia đình hoặc đơn giản ngồi nghe gió. Picnic được tổ chức tại khu vực có dịch vụ và được phép đón khách.',
      audience:'Gia đình, nhóm bạn và nhóm đồng nghiệp thích thư giãn; không yêu cầu kinh nghiệm trekking.',difficulty:'Nhẹ — tản bộ ngắn; cần giám sát trẻ ở khu vực ven nước.',group:'10–20 khách; ưu tiên nhóm riêng.',season:'Ngày khô ráo, không có cảnh báo dông. Không hứa hẹn hoàng hôn vì chương trình kết thúc trước tối.',transport:'Xe riêng; dành 45–60 phút từ trung tâm đến Tân Cương, 60–90 phút chuyển sang Ghềnh Chè và 45–75 phút trở về, cần khảo sát lại cung đường.',
      highlights:['Một chén trà mở đầu ngày nghỉ bên người thân.','Picnic nhẹ với chỗ ngồi, mái che dự kiến tại cơ sở dịch vụ.','Thời gian tự do thực sự thay vì liên tục lên xuống xe.'],
      itinerary:[day('Một ngày sống chậm',['Trưa'],'Không lưu trú',[
        ['08:00–09:00','Khởi hành về vùng trà','Đón tại trung tâm, lên xe về Tân Cương; thống nhất điểm hẹn và nhịp đi phù hợp cho gia đình.'],
        ['09:00–11:00','Thưởng trà và dạo đồi','Tìm hiểu cách pha trà, đi bộ nhẹ trên lối mở và chụp ảnh; trẻ em tham gia cùng người giám hộ.'],
        ['11:00–12:30','Về Ghềnh Chè','Chuyển xe sang khu vực hồ, có thời gian đệm cho đường địa phương; nhận bàn tại cơ sở đặt trước.'],
        ['12:30–14:00','Bữa trưa và nghỉ ngơi','Ăn trưa, nghỉ dưới mái che; hướng dẫn viên giới thiệu khu vực được phép đi lại và ranh giới ven nước.'],
        ['14:00–16:00','Picnic ven hồ','Thưởng thức đồ ăn nhẹ đã chuẩn bị, chơi trò kết nối nhẹ, đọc sách hoặc chụp ảnh. Không mặc định bao gồm chèo thuyền, bơi hay đốt lửa.'],
        ['16:00–17:15','Gói lại một ngày bình yên','Thu gom rác, kiểm tra trẻ nhỏ và tư trang, trả khách tại trung tâm.']
      ])],includedExtra:['Một buổi thưởng trà cơ bản.','Khu ngồi picnic dùng chung và phần đồ ăn nhẹ theo set của đoàn, cần đặt trước.'],excludedExtra:['Thuyền, SUP/kayak, câu cá, lều ngủ qua đêm và dịch vụ ngoài set picnic.'],lodging:'Không nghỉ đêm, không cắm trại tự phát.',food:'01 bữa trưa và 01 phần ăn nhẹ; đồ uống ngoài nước cơ bản tính riêng.',notes:['Không đưa trẻ xuống hồ hoặc đến mép nước thiếu rào chắn.','Chỉ sử dụng khu picnic khi chủ điểm đồng ý; không đốt lửa trên thảm cỏ.'],weatherPlan:'Chuyển picnic sang khu có mái che nếu cơ sở đáp ứng. Dông gió mạnh: chuyển sang trải nghiệm trà trong nhà hoặc đổi ngày sau khi thống nhất với khách.'},
    {id:103,code:'TJ03',slug:'ve-nguon-giua-tieng-thac',name:'Về nguồn giữa tiếng thác — ATK & Khuôn Tát',destinationIds:['atk','khuon-tat'],days:1,price:790000,priceMax:990000,tags:['Văn hóa','Thiên nhiên','Lịch sử & Về nguồn'],label:'DẤU ẤN LỊCH SỬ',image:'heritage.svg',imageCaption:'Minh họa chủ đề về nguồn; không phải ảnh di tích.',
      summary:'Lắng nghe trang sử hào hùng của chiến khu ATK Định Hóa, thưởng thức cơm lam nướng thơm lừng và đắm mình trong thanh âm trong trẻo của thác Khuôn Tát.',
      description:'Hành trình có nhịp đi trang trọng vào buổi sáng và nhẹ nhàng vào buổi chiều. Thay vì chạy qua nhiều di tích, đoàn tập trung một số điểm trong cụm ATK để nghe thuyết minh, đặt câu hỏi và kết nối kiến thức; phần thác là điểm thư giãn, không tổ chức leo các tầng cao hay tắm thác.',
      audience:'Nhóm yêu lịch sử, gia đình có trẻ lớn, đoàn học tập trải nghiệm; chương trình học sinh cần điều chỉnh quản lý và giá riêng.',difficulty:'Nhẹ đến vừa — có bậc thang, lối dốc và đường ẩm tại thác.',group:'10–20 khách; đoàn học sinh cần kế hoạch riêng.',season:'Có thể xây dựng nhiều thời điểm trong năm; chọn ngày khô và kiểm tra đường vào thác trước chuyến đi.',transport:'Xe riêng từ trung tâm đi Định Hóa, dự trù 1,5–2 giờ mỗi chiều; di chuyển trong cụm điểm 20–45 phút tùy tuyến.',
      highlights:['Thuyết minh tại cụm di tích ATK, ưu tiên hiểu sâu hơn đi nhiều.','Bữa trưa với món địa phương, gợi ý cơm lam nếu đặt được.','Ngắm thác Khuôn Tát từ khu vực tiếp cận phù hợp.'],
      itinerary:[day('Ký ức miền gió ngàn',['Trưa'],'Không lưu trú',[
        ['07:00–09:00','Lên đường về Định Hóa','Đón đoàn tại trung tâm, nghỉ ngắn dọc đường và nghe giới thiệu bối cảnh lịch sử.'],
        ['09:00–11:30','Tìm hiểu ATK','Tham quan theo tuyến được ban quản lý xác nhận, dự kiến khu trưng bày và một điểm di tích tiêu biểu như Tỉn Keo. Có thời gian nghe thuyết minh và trao đổi; không cam kết toàn bộ cụm đều mở cửa.'],
        ['11:30–13:00','Ăn trưa, nghỉ chân','Dùng bữa tại Định Hóa; có thể đặt cơm lam và món theo mùa, thay thế tương đương nếu không có nguyên liệu.'],
        ['13:00–15:00','Khoảng xanh Khuôn Tát','Di chuyển đến khu vực thác, đi bộ trên đoạn được hướng dẫn cho phép, ngắm cảnh và chụp ảnh từ vị trí an toàn; không vượt dòng nước hay leo đá trơn.'],
        ['15:00–17:30','Trở về trung tâm','Dành thời gian dự phòng trên đường về. Kết thúc bằng phần chia sẻ ngắn về điều đáng nhớ của chuyến đi.']
      ])],includedExtra:['Dự toán thuyết minh chuyên đề cơ bản tại cụm ATK, cần đặt lịch.'],excludedExtra:['Lễ vật, công đức, chương trình dâng hương nghi thức riêng và hoạt động ngoài tuyến cơ bản.'],lodging:'Không nghỉ đêm.',food:'01 bữa trưa tại Định Hóa; suất ăn theo thực đơn chốt trước.',notes:['Trang phục lịch sự, giữ yên lặng tại không gian tưởng niệm.','Không xuống nước hoặc trèo lên các tầng thác.'],weatherPlan:'Nếu đường vào thác trơn hoặc nước lớn, bỏ điểm thác và kéo dài nội dung tại không gian trưng bày ATK nếu mở cửa; thông báo thay đổi trước khi di chuyển.'},
    {id:104,code:'TJ04',slug:'mien-da-va-tieng-suoi',name:'Miền đá và tiếng suối — Chùa Hang & Võ Nhai',destinationIds:['chua-hang','phuong-hoang'],days:2,price:1890000,priceMax:2390000,tags:['Văn hóa','Khám phá','Thiên nhiên','Hang động kỳ vĩ'],label:'CÂU CHUYỆN TRONG LÒNG NÚI',image:'cave.svg',imageCaption:'Minh họa chủ đề hang động; không phải ảnh hang Phượng Hoàng.',
      summary:'Chiêm bái Chùa Hang cổ kính, chinh phục hang Phượng Hoàng kỳ vĩ với thạch nhũ lung linh, ngắm suối ngầm Mỏ Gà và ngủ đêm nhà sàn ấm áp bản Tày.',
      description:'Chuyến đi kết hợp văn hóa và vận động vừa phải, với khoảng đệm đủ dài cho đường lên hang. Buổi tối nghỉ tại cơ sở địa phương mang lại thời gian cảm nhận nhịp sống vùng núi. Các hoạt động giao lưu chỉ tổ chức khi chủ nhà và cộng đồng đồng ý, không xem sinh hoạt của người dân là một tiết mục mặc định.',
      audience:'Nhóm bạn, cặp đôi thích hang động và văn hóa; khách có thể đi bộ lên xuống dốc.',difficulty:'Vừa — đường lên hang có độ dốc và bậc đá; không phù hợp người hạn chế vận động nếu chưa có phương án riêng.',group:'10–16 khách, chia nhóm nhỏ khi vào hang.',season:'Ưu tiên thời tiết khô, đường lên hang không trơn và khu tham quan được phép mở.',transport:'Xe riêng; trung tâm → Chùa Hang khoảng 20–40 phút, Chùa Hang → Võ Nhai khoảng 1,5–2,5 giờ; xe dừng theo điều kiện đường vào cơ sở.',
      highlights:['Vãn cảnh Chùa Hang — Kim Sơn Tự.','Đêm nghỉ tại Võ Nhai và bữa cơm theo hương vị địa phương.','Buổi sáng dành riêng cho hang Phượng Hoàng, chiều ngắm suối Mỏ Gà.'],
      itinerary:[day('Từ không gian tĩnh đến bản làng',['Trưa','Tối'],'01 đêm tại nhà nghỉ/homestay Võ Nhai, phòng tiêu chuẩn hoặc phòng cộng đồng đã thống nhất',[
        ['08:00–10:00','Chùa Hang buổi sáng','Đón đoàn và đến Kim Sơn Tự, tham quan khuôn viên mở cửa, tìm hiểu không gian chùa trong cảnh quan đá vôi; ăn mặc lịch sự.'],
        ['10:00–12:30','Di chuyển đến Võ Nhai','Đi xe theo tuyến đã khảo sát, có một điểm dừng nghỉ; đến cơ sở dùng bữa trưa.'],
        ['12:30–14:30','Nhận phòng, nghỉ trưa','Dùng bữa, nhận chỗ nghỉ và chuẩn bị giày, nước cho ngày đi hang tiếp theo.'],
        ['14:30–17:00','Gặp gỡ vùng Mỏ Gà','Dạo làng trên lối được phép, tìm hiểu sinh hoạt địa phương với người dẫn đường; hoạt động làm bánh hoặc giao lưu có thể đặt thêm, không bao gồm mặc định.'],
        ['18:00–20:00','Bữa tối và câu chuyện hành trình','Ăn tối, nghe phổ biến tuyến hang, giờ tập trung và phương án theo thể lực; nghỉ sớm.']
      ]),day('Phượng Hoàng và dòng suối Mỏ Gà',['Sáng','Trưa'],'Không lưu trú',[
        ['07:00–08:00','Ăn sáng, chuẩn bị','Kiểm tra giày, đèn và nước; thống nhất nhóm tham quan hang và nhóm nghỉ tại khu dịch vụ nếu không leo.'],
        ['08:00–11:30','Khám phá hang Phượng Hoàng','Lên xuống chậm theo hướng dẫn địa phương, chỉ đi tuyến được phép; dừng quan sát cảnh quan hang, không chạm hoặc lấy nhũ đá. Thời lượng điều chỉnh theo thể lực và lối mở.'],
        ['11:30–13:00','Bữa trưa phục hồi','Về khu dịch vụ, nghỉ và ăn trưa; thay áo khô nếu cần.'],
        ['13:00–14:30','Ngắm suối Mỏ Gà','Tản bộ và chụp ảnh ở khu vực được phép tiếp cận; không tự bơi vào cửa hang nước.'],
        ['14:30–17:00','Về Thái Nguyên','Trả phòng theo thỏa thuận từ buổi sáng, kiểm tra đủ khách và di chuyển về điểm đón.']
      ])],includedExtra:['01 đêm lưu trú theo loại phòng đã thống nhất, không cam kết cơ sở cụ thể khi chưa đặt.','Người dẫn đường địa phương cho tuyến hang được phép; đèn chiếu sáng phù hợp cần xác nhận nhà cung cấp.'],excludedExtra:['Phòng đơn, giao lưu văn nghệ, trải nghiệm làm bánh riêng và các dịch vụ vui chơi tại khu du lịch.'],lodging:'01 đêm Võ Nhai; ưu tiên cơ sở sạch, có khu vệ sinh phù hợp quy mô đoàn; phòng riêng hay cộng đồng chốt trước.',food:'01 bữa sáng, 03 bữa chính; gợi ý rau theo mùa và món Tày do cơ sở chế biến, thực đơn xác nhận trước.',notes:['Mang giày bám tốt, không tách nhóm trong hang.','Không đồng nhất tham quan hang Phượng Hoàng với tự thám hiểm hang nước Mỏ Gà.'],weatherPlan:'Nếu hang đóng hoặc đường trơn, thay bằng trải nghiệm tại cơ sở cộng đồng và không gian tham quan được phép; thông báo trước và đối soát phần dịch vụ thay đổi.'},
    {id:105,code:'TJ05',slug:'theo-dong-cua-tu',name:'Theo dòng Cửa Tử — Rừng, hồ và hương trà',destinationIds:['cua-tu','nui-coc','tan-cuong'],days:2,price:2490000,priceMax:2990000,tags:['Trekking','Thiên nhiên','Khám phá','Vượt suối mạo hiểm'],label:'BƯỚC CHÂN VỀ RỪNG',image:'lake.jpg',imageCaption:'Hồ Núi Cốc · Điểm dừng ngày thứ hai của tour.',
      summary:'Chinh phục cung trekking Cửa Tử nguyên sơ vượt ghềnh đá ngọc bích cùng người dẫn đường, tái tạo năng lượng bên hồ Núi Cốc và đồi chè Tân Cương.',
      description:'Hành trình dành cho người muốn vận động nhưng vẫn có một ngày cuối thật thư thả. Cửa Tử được bố trí riêng một ngày để kiểm tra điều kiện, đi theo nhịp đoàn và quay về sớm. Tour không hứa chinh phục bảy cửa, không mặc định có nhảy thác, trượt máng hay vượt dây; giới hạn tuyến do người hướng dẫn chuyên môn quyết định.',
      audience:'Người lớn có thể lực phù hợp, quen đi bộ ngoài trời; người mới cần trao đổi khả năng vận động với đơn vị tổ chức.',difficulty:'Vừa đến cao tùy mực nước và đường đi — có đá ẩm và địa hình ven suối. Cần sàng lọc thể lực trước khi nhận khách.',group:'8–12 khách; báo giá hiển thị theo đoàn 10 khách, bố trí người dẫn đường theo yêu cầu tuyến.',season:'Chỉ tổ chức khi đơn vị địa phương xác nhận thời tiết và lưu lượng nước phù hợp; không suy ra an toàn chỉ từ thời tiết tại điểm đón.',transport:'Xe riêng, dự trù 1,5–2 giờ từ trung tâm đến điểm tập kết Đại Từ; ngày hai chuyển khu vực hồ và Tân Cương theo lộ trình khảo sát.',
      highlights:['Một ngày trekking có người dẫn đường và thời gian dự phòng.','Đêm nghỉ tại Đại Từ sau ngày vận động.','Ngày thứ hai thư giãn ven hồ Núi Cốc và thưởng trà Tân Cương.'],
      itinerary:[day('Một ngày cùng rừng và suối',['Trưa','Tối'],'01 đêm nhà nghỉ/homestay khu vực Đại Từ',[
        ['06:30–08:30','Đến điểm tập kết','Đón đoàn và đi Đại Từ, dừng vệ sinh; kiểm tra tình hình tuyến với người dẫn đường trước khi bắt đầu.'],
        ['08:30–09:15','Kiểm tra trang bị và nhịp đi','Phổ biến quy tắc, kiểm tra giày bám, áo phao khi tuyến có đoạn nước được phép, đánh giá sức khỏe tự khai và thống nhất điểm quay đầu.'],
        ['09:15–12:00','Trekking tuyến cơ bản','Đi theo tuyến địa phương cho phép, ưu tiên khu vực Cửa Tử 1 phù hợp điều kiện ngày đi; không tự tách nhóm hoặc mở rộng sang các tầng cao.'],
        ['12:00–13:00','Ăn trưa dã ngoại','Dùng suất ăn mang theo tại nơi hướng dẫn viên chọn, bổ sung nước, thu gom toàn bộ rác.'],
        ['13:00–15:30','Quay về trước chiều muộn','Trở về điểm tập kết theo tốc độ của nhóm, có đệm thời gian cho đường trơn; thay đồ và kiểm tra quân số.'],
        ['16:00–19:00','Nghỉ tại Đại Từ','Nhận phòng, tắm rửa, dùng bữa tối; để cơ thể nghỉ sau ngày vận động.']
      ]),day('Từ mặt hồ đến chén trà',['Sáng','Trưa'],'Không lưu trú',[
        ['07:30–09:00','Ăn sáng, trả phòng','Khởi hành thong thả, di chuyển về khu vực hồ Núi Cốc.'],
        ['09:00–11:30','Một buổi sáng ven hồ','Đi bộ nhẹ, nghỉ và ngắm cảnh; chuyến thuyền ngắn là tùy chọn khi có dịch vụ phù hợp, không bắt buộc.'],
        ['11:30–13:00','Ăn trưa và nghỉ','Dùng bữa tại cơ sở ven tuyến, ưu tiên suất ăn dễ dùng sau ngày trekking.'],
        ['13:00–15:30','Tân Cương và hương trà','Chuyển xe đến vùng chè, thưởng trà, trò chuyện cùng người làm chè và chụp ảnh trên lối tham quan.'],
        ['15:30–17:00','Kết thúc hành trình','Về trung tâm Thái Nguyên, dành thời gian đệm và trả khách.']
      ])],includedExtra:['01 đêm tại Đại Từ.','Người dẫn đường chuyên môn cho tuyến Cửa Tử cơ bản và bộ trang bị an toàn cần thiết theo đánh giá tuyến; danh mục phải xác nhận trước khi bán.','Suất ăn trekking ngày đầu và buổi thưởng trà cơ bản ngày hai.'],excludedExtra:['Vé thuyền hồ Núi Cốc; tuyến nâng cao, vượt thác hoặc hoạt động kỹ thuật ngoài chương trình.'],lodging:'01 đêm phòng tiêu chuẩn Đại Từ; không ngủ trong rừng.',food:'01 bữa sáng, 03 bữa chính, trong đó 01 bữa trưa mang theo.',packingExtra:['Giày trekking bám ướt, quần áo nhanh khô, bộ đồ thay và túi chống nước.'],notes:['Hoạt động dưới nước chỉ khi nằm trong tuyến được phép và có giám sát; không tự nhảy, trượt thác.','Không khởi hành khi có cảnh báo mưa lớn/lũ hoặc khi người dẫn đường đánh giá tuyến không phù hợp.'],weatherPlan:'Hoãn phần trekking hoặc chuyển toàn chương trình sang hồ–trà và hoạt động trong nhà sau khi khách đồng ý; không cố thay bằng một suối khác cùng điều kiện nguy hiểm.'},
    {id:106,code:'TJ06',slug:'ba-be-mien-truc-xanh',name:'Ba Bể, miền trúc xanh — Ba ngày sống chậm',destinationIds:['yen-duong','ba-be'],days:3,price:3290000,priceMax:3890000,tags:['Nghỉ dưỡng','Thiên nhiên','Văn hóa','Sinh thái Rừng Trúc'],label:'Ở LẠI GIỮA MIỀN XANH',image:'lake-art.svg',imageCaption:'Minh họa chủ đề hồ và rừng; không phải ảnh Hồ Ba Bể.',
      summary:'Rảo bước giữa rừng trúc Yến Dương xanh ngút ngàn, du thuyền lướt nhẹ trên mặt hồ Ba Bể huyền ảo và tận hưởng hai đêm homestay an yên bản làng.',
      description:'Một hành trình ưu tiên chiều sâu và khoảng nghỉ: không vừa chạy đường dài vừa nhồi thêm hang động trong ngày. Ba Bể có riêng một ngày để đi thuyền, ngắm núi và nghỉ ở homestay. Rừng trúc là trải nghiệm đi bộ có độ dốc, được tổ chức theo sức của đoàn chứ không mặc định là lối dạo bằng phẳng.',
      audience:'Cặp đôi, nhóm bạn yêu thiên nhiên; gia đình có thành viên đi bộ dốc được, muốn nghỉ hai đêm cùng một nơi.',difficulty:'Nhẹ đến vừa — rừng trúc có lối dốc; tuyến thuyền cần lên xuống bến.',group:'10–16 khách.',season:'Ưu tiên ngày ít mưa và điều kiện hồ cho phép tàu hoạt động; không cam kết sương hoặc cảnh lúa theo mùa.',transport:'Xe riêng; ngày đầu dự trù 4–5 giờ gồm dừng nghỉ đến khu vực Yến Dương, sau đó 1–2 giờ chuyển về nơi nghỉ Ba Bể tùy đường; ngày cuối dành khoảng 5 giờ về trung tâm.',
      highlights:['Dạo rừng trúc Phiêng Phàng với người hướng dẫn địa phương.','Một chuyến thuyền ngắm hồ trong ngày riêng, có áo phao.','Hai đêm cùng một homestay giúp giảm việc chuyển phòng.'],
      itinerary:[day('Đường đến miền trúc',['Trưa','Tối'],'Đêm 1 tại homestay khu vực Ba Bể',[
        ['06:30–11:30','Từ Thái Nguyên lên vùng Ba Bể','Đón khách, di chuyển về khu vực Yến Dương, nghỉ dọc đường; chừa thời gian cho đường địa phương.'],
        ['11:30–12:45','Bữa trưa và chuẩn bị đi bộ','Ăn trưa tại cơ sở đặt trước, thay giày và mang nước vừa đủ.'],
        ['12:45–15:00','Rừng trúc Yến Dương','Theo lối được phép ở Phiêng Phàng, dừng nghe câu chuyện về trúc và chụp ảnh. Không gộp thêm leo đỉnh Pù Lầu hoặc đi thác vào tuyến cơ bản.'],
        ['15:00–17:30','Về nơi nghỉ Ba Bể','Di chuyển về homestay, nhận phòng và nghỉ; thời gian dư để bù cho đoạn đường miền núi.'],
        ['18:30–20:00','Bữa tối đầu tiên ở bản','Ăn tối với thực đơn địa phương đã thống nhất, làm quen không gian sinh hoạt và giờ yên tĩnh.']
      ]),day('Một ngày dành cho hồ',['Sáng','Trưa','Tối'],'Đêm 2 tại cùng homestay Ba Bể',[
        ['07:00–08:30','Bữa sáng thong thả','Ăn sáng, chuẩn bị mũ và nước, di chuyển đến bến theo giờ tàu đã đặt.'],
        ['08:30–11:30','Du ngoạn Ba Bể','Đi thuyền theo tuyến ngắm hồ được xác nhận, mặc áo phao; dừng ngắm núi và chụp ảnh, không cam kết thêm các điểm ngoài danh sách.'],
        ['11:30–14:00','Ăn trưa và nghỉ','Về điểm dùng bữa trên tuyến hoặc homestay theo điều phối, tránh di chuyển liên tục giữa trưa.'],
        ['14:00–16:30','Nhịp sống ven hồ','Đi bộ đoạn ngắn quanh nơi lưu trú, trò chuyện khi người dân đồng ý; hoặc nghỉ tại homestay. SUP/kayak là hoạt động đặt riêng, không bao gồm.'],
        ['18:00–20:00','Bữa cơm và câu chuyện vùng hồ','Dùng bữa tối; có thể đặt thêm giao lưu văn hóa theo thỏa thuận, không tự động có trong tour.']
      ]),day('Mang bình yên trở về',['Sáng','Trưa'],'Không lưu trú',[
        ['07:00–09:30','Buổi sáng không vội','Ăn sáng, tự do ngắm cảnh tại khu vực gần nơi nghỉ và thu xếp hành lý.'],
        ['09:30–11:30','Trả phòng, khởi hành','Kiểm tra đồ dùng, chào chủ nhà; bắt đầu chặng về theo giờ xe.'],
        ['11:30–12:30','Bữa trưa dọc đường','Nghỉ và ăn trưa tại cơ sở đặt trước trên tuyến.'],
        ['12:30–17:00','Về Thái Nguyên','Tiếp tục chặng về, có điểm nghỉ; khung giờ kết thúc gồm thời gian đệm cho giao thông.']
      ])],includedExtra:['02 đêm homestay Ba Bể, cùng cơ sở nếu còn phòng.','01 chuyến thuyền ngắm hồ dùng chung cho đoàn, tuyến cơ bản và áo phao; người vận hành xác nhận điều kiện.','Dẫn đường địa phương cho rừng trúc khi cần theo tuyến thực tế.'],excludedExtra:['Kayak/SUP, đêm văn nghệ riêng, phòng đơn và tuyến thuyền bổ sung.'],lodging:'02 đêm homestay; báo rõ phòng riêng/phòng cộng đồng và loại vệ sinh trước khi đặt.',food:'02 bữa sáng, 05 bữa chính; thực đơn gợi ý món địa phương với rau theo mùa, không cam kết món đặc sản hiếm.',notes:['Không chặt trúc, bẻ măng hoặc đi vào đất canh tác chưa xin phép.','Mặc áo phao suốt chuyến thuyền; không tự bơi giữa hồ.'],weatherPlan:'Nếu không thể đi rừng trúc, ưu tiên hoạt động tại nơi nghỉ; nếu tàu dừng do thời tiết, thay bằng nội dung văn hóa trong nhà hoặc đổi ngày, không bảo đảm vẫn thực hiện đủ tuyến.'},
    {id:107,code:'TJ07',slug:'sam-chiem-ban-chang',name:'Gió trên thảo nguyên — Sam Chiêm & Bản Chang',destinationIds:['sam-chiem','ban-chang'],days:2,price:2590000,priceMax:3190000,tags:['Thiên nhiên','Nhiếp ảnh','Khám phá','Check-in Thảo nguyên'],label:'HẸN VỚI KHOẢNG TRỜI RỘNG',image:'prairie.svg',imageCaption:'Minh họa chủ đề thảo nguyên và mặt hồ; không phải ảnh điểm đến.',
      summary:'Đón gió lộng trên thảo nguyên Sam Chiêm bao la với thảm cỏ uốn lượn, thỏa sức săn ảnh vùng cao và dạo bước ngắm hồ Bản Chang tĩnh lặng, thơ mộng.',
      description:'Tour dành cho những người thích mang về một bộ ảnh và cảm giác thoáng đãng. Sam Chiêm được ghép với Bản Chang theo khu vực Ngân Sơn, tránh kéo thêm chặng Ba Bể trong chuyến hai ngày. Đoàn nghỉ tại cơ sở lưu trú, không mặc định cắm trại qua đêm ở nơi chưa xác nhận dịch vụ và quyền tiếp cận.',
      audience:'Nhóm bạn, người thích ảnh phong cảnh và đi bộ ngoài trời; không phù hợp lịch trình cần tiếp cận hoàn toàn bằng xe lớn.',difficulty:'Vừa — đi bộ trên cỏ, có dốc và đoạn đường tiếp cận cần phương tiện phù hợp.',group:'8–12 khách; có thể cần xe trung chuyển theo khảo sát.',season:'Chọn đợt trời khô, ít gió; sắc cỏ, mây và tầm nhìn thay đổi theo mùa, không cam kết săn mây.',transport:'Xe riêng từ trung tâm lên Ngân Sơn khoảng 4–5 giờ gồm dừng nghỉ; đường cuối đến Sam Chiêm cần khảo sát riêng và tính phương án trung chuyển.',
      highlights:['Khoảng thời gian dài chụp ảnh tại Sam Chiêm, không đuổi theo nhiều điểm.','Dã ngoại có kiểm soát tại khu được phép.','Ngắm hồ Bản Chang từ bờ, kết thúc trước chặng xe về.'],
      itinerary:[day('Một buổi chiều trên triền cỏ',['Trưa','Tối'],'01 đêm nhà nghỉ/homestay khu vực Ngân Sơn',[
        ['06:30–11:30','Lên Ngân Sơn','Khởi hành sớm từ trung tâm, nghỉ giữa chặng; đến điểm ăn trưa trước khi vào đường địa phương.'],
        ['11:30–13:30','Ăn trưa, chuẩn bị lên Sam Chiêm','Dùng bữa, kiểm tra thời tiết và đổi phương tiện nếu tuyến yêu cầu; trung chuyển chỉ thực hiện khi đã xác nhận an toàn.'],
        ['13:30–16:00','Thảo nguyên Sam Chiêm','Đi bộ ngắn trên tuyến được phép, chụp ảnh các lớp đồi, dùng đồ ăn nhẹ và nghỉ. Không lái xe tự do trên cỏ, không dựng lều hoặc đốt lửa khi chưa được cho phép.'],
        ['16:00–18:00','Xuống núi, nhận phòng','Rời khu vực trước tối, có thời gian đệm cho trung chuyển và đường dốc; nhận chỗ nghỉ.'],
        ['18:30–20:00','Bữa tối ở Ngân Sơn','Ăn tối và xem lại những bức ảnh của ngày; nghỉ để chuẩn bị đi hồ buổi sáng.']
      ]),day('Bản Chang trong ánh sáng sớm',['Sáng','Trưa'],'Không lưu trú',[
        ['07:00–08:30','Ăn sáng, trả phòng','Thu xếp hành lý, di chuyển đến khu vực hồ Bản Chang theo tuyến đã khảo sát.'],
        ['08:30–10:30','Dạo bên hồ','Ngắm mặt nước và cảnh quan xung quanh từ vị trí được phép, chụp ảnh theo nhóm nhỏ; không bao gồm bơi, chèo thuyền hoặc câu cá.'],
        ['10:30–12:30','Rời hồ, dùng bữa trưa','Lên xe trở về, ăn trưa tại điểm đặt trước trên tuyến.'],
        ['12:30–18:00','Hành trình về trung tâm','Nghỉ dọc đường, trả khách tại Thái Nguyên; dành đệm cho giao thông và đường miền núi.']
      ])],includedExtra:['01 đêm lưu trú Ngân Sơn.','Phần ăn nhẹ picnic và dẫn đường địa phương tại Sam Chiêm; trung chuyển tiêu chuẩn cần được báo giá xác nhận trước khi bán.'],excludedExtra:['Chụp ảnh chuyên nghiệp, thuê trang phục, lều qua đêm và các hoạt động dưới nước.'],lodging:'01 đêm cơ sở lưu trú Ngân Sơn; không cam kết resort hoặc dịch vụ cao cấp.',food:'01 bữa sáng, 03 bữa chính và 01 phần ăn nhẹ.',notes:['Dừng tham quan khi sương dày, dông hoặc đường cỏ trơn.','Bản Chang là hồ thủy lợi; không mặc định có dịch vụ vui chơi dưới nước.'],weatherPlan:'Nếu đường Sam Chiêm không tiếp cận được, đổi ngày là ưu tiên; có thể giữ tuyến Bản Chang và chương trình nghỉ tại cơ sở khi khách đồng ý, không thay bằng cung đường chưa khảo sát.'},
    {id:108,code:'TJ08',slug:'ba-be-tham-phay',name:'Từ mặt hồ đến lòng núi — Ba Bể & Thẳm Phầy',destinationIds:['ba-be','tham-phay'],days:3,price:4590000,priceMax:5590000,tags:['Khám phá','Trekking','Thiên nhiên','Hang động kỳ vĩ'],label:'HÀNH TRÌNH CÓ CHUYÊN GIA',image:'cave.svg',imageCaption:'Minh họa chủ đề hang nước; không phải ảnh Hang Thẳm Phầy.',
      summary:'Thám hiểm hang nước Thẳm Phầy kỳ bí tựa Sơn Đoòng phương Bắc cùng chuyên gia, kết hợp du ngoạn hồ Ba Bể tuyệt sắc và nghỉ ngơi homestay bản địa.',
      description:'Đây là tour khám phá chuyên biệt, không phải một điểm tham quan thêm vào lịch nghỉ dưỡng. Hoạt động hang chỉ đưa vào vận hành khi đơn vị chuyên môn xác nhận được phép khai thác, điều kiện nước, trang bị và nhân sự. Khung ngày hai dành riêng cho hành trình vào–ra, thời gian cụ thể phụ thuộc tuyến được duyệt; không cam kết đi hết chiều dài hang.',
      audience:'Người lớn có thể lực tốt và đáp ứng yêu cầu của đơn vị khai thác hang; cần trao đổi trước về khả năng đi địa hình ướt và vận động kéo dài.',difficulty:'Cao — đi rừng, đá ướt, không gian tối và có thể có đoạn nước; không dành mặc định cho trẻ nhỏ hoặc khách chỉ muốn tham quan nhẹ.',group:'6–10 khách; giá dự kiến theo 10 khách, tỷ lệ hướng dẫn do đơn vị chuyên môn xác định.',season:'Chỉ khi tuyến hang được phép hoạt động và đánh giá thủy văn/thời tiết phù hợp; có thể hoãn dù ngày khởi hành trời nắng.',transport:'Xe riêng trung tâm → Ba Bể dự trù 4–5,5 giờ gồm nghỉ; trung chuyển đến điểm tập kết hang do đơn vị chuyên môn xác nhận.',
      highlights:['Thuyền ngắm Ba Bể nhẹ nhàng trước ngày vận động.','Ngày khám phá hang có phổ biến quy trình, trang bị và điểm quay đầu.','Hai đêm cùng nơi nghỉ, không đổi phòng sau ngày đi hang.'],
      itinerary:[day('Làm quen với miền hồ',['Trưa','Tối'],'Đêm 1 tại Ba Bể',[
        ['06:00–11:30','Đến Ba Bể','Đón khách và di chuyển, nghỉ dọc đường; ưu tiên đến nơi đủ sớm để không vội phần thuyền.'],
        ['11:30–14:00','Ăn trưa, nhận phòng','Dùng bữa, nhận phòng và nghỉ; kiểm tra tư trang cho hôm sau.'],
        ['14:00–16:30','Ngắm hồ bằng thuyền','Chuyến ngắn theo tuyến mở, mặc áo phao và hạn chế hoạt động gắng sức; nếu đến muộn hoặc thời tiết xấu, bỏ hoạt động thay vì kéo đến tối.'],
        ['17:00–18:00','Gặp đội hướng dẫn hang','Trao đổi sức khỏe, điều kiện tham gia, kiểm tra cỡ trang bị; đơn vị chuyên môn quyết định tiếp nhận và cung đi.'],
        ['18:30–20:00','Ăn tối, nghỉ sớm','Dùng bữa và chuẩn bị quần áo khô, vật dụng cá nhân cần thiết.']
      ]),day('Ngày khám phá Thẳm Phầy',['Sáng','Trưa','Tối'],'Đêm 2 tại cùng cơ sở Ba Bể',[
        ['06:30–08:00','Ăn sáng, đến điểm tập kết','Kiểm tra lại thời tiết và điều kiện hang; chỉ di chuyển vào tuyến khi trưởng nhóm chuyên môn cho phép.'],
        ['08:00–09:00','Phổ biến và kiểm tra trang bị','Nhận mũ bảo hộ, đèn, đồ hỗ trợ phù hợp tuyến từ đơn vị vận hành; thực hành quy tắc di chuyển và thống nhất tín hiệu quay đầu.'],
        ['09:00–12:00','Tiếp cận và khám phá phần tuyến cho phép','Theo đội hướng dẫn qua đoạn rừng và hang đã duyệt. Nhịp đi và phạm vi do điều kiện thực tế quyết định; không rời nhóm, không chạm nhũ đá.'],
        ['12:00–13:00','Bữa trưa theo điều phối','Ăn suất mang theo tại vị trí do đội chuyên môn chọn, thu gom rác; thời điểm có thể thay đổi theo tuyến.'],
        ['13:00–16:00','Rời hang và trở về điểm tập kết','Quay lại theo giới hạn giờ đã thống nhất, dành thời gian đệm; kiểm đếm người và trang bị khi kết thúc.'],
        ['16:00–19:30','Hồi phục tại nơi nghỉ','Trung chuyển về homestay, thay đồ, nghỉ và ăn tối; không ghép thêm điểm tham quan.']
      ]),day('Một buổi sáng để nghỉ',['Sáng','Trưa'],'Không lưu trú',[
        ['07:30–09:30','Ăn sáng và nghỉ','Tận hưởng buổi sáng tại nơi lưu trú, không bố trí trekking thêm.'],
        ['09:30–11:30','Trả phòng, khởi hành','Thu xếp đồ khô và đồ ướt riêng, kiểm tra hành lý trước khi lên xe.'],
        ['11:30–12:30','Ăn trưa dọc tuyến','Nghỉ tại cơ sở đã hẹn để cả đoàn hồi phục trước chặng cuối.'],
        ['12:30–17:30','Trở về Thái Nguyên','Dành thời gian dừng nghỉ và đệm đường; kết thúc tại điểm đón.']
      ])],includedExtra:['02 đêm lưu trú Ba Bể.','01 chuyến thuyền ngắm hồ cơ bản cho đoàn, có áo phao.','Dự toán gói hang có tổ chức: dẫn đường chuyên môn, trung chuyển, mũ/đèn và trang bị theo tuyến; tất cả phải xác nhận khả dụng, quyền khai thác và giá trước khi mở bán.'],excludedExtra:['Tuyến hang mở rộng, quay phim chuyên nghiệp, hoạt động kỹ thuật ngoài gói chuyên môn đã xác nhận.'],lodging:'02 đêm cùng cơ sở Ba Bể, ưu tiên chỗ phơi đồ và tắm thay sau trekking.',food:'02 bữa sáng, 05 bữa chính; bữa trưa ngày hai là suất mang theo được đội vận hành thống nhất.',packingExtra:['Giày phù hợp địa hình ướt, quần áo nhanh khô, túi chống nước và bộ đồ thay.','Trang bị kỹ thuật không tự thay thế bằng đồ gia dụng; dùng theo hướng dẫn của đơn vị chuyên môn.'],notes:['Chưa có xác nhận tuyến mở thì tour giữ trạng thái đề xuất, không nhận cọc.','Không tự vào hang nước; thực hiện sàng lọc, yêu cầu bảo hiểm và cứu hộ theo đơn vị vận hành.'],weatherPlan:'Hủy/hoãn phần hang khi điều kiện không phù hợp. Khách chọn đổi ngày hoặc chương trình nghỉ dưỡng Ba Bể được báo lại giá; không quảng cáo một tuyến hang khác là thay thế tương đương khi chưa đánh giá.'},
    {id:109,code:'TJ09',slug:'mien-tra-ve-nguon-ba-be',name:'Miền trà về nguồn — Từ ATK đến Ba Bể',destinationIds:['tan-cuong','atk','khuon-tat','ba-be','yen-duong'],days:4,price:4690000,priceMax:5590000,tags:['Văn hóa','Thiên nhiên','Nghỉ dưỡng','Hành trình Di sản'],label:'MỘT DẢI KÝ ỨC XANH',image:'tea.jpg',imageCaption:'Đồi chè Tân Cương · Điểm mở đầu hành trình.',
      summary:'Hành trình bốn ngày nối liền hương trà Tân Cương, di tích ATK Định Hóa, thác Khuôn Tát hoang sơ cùng vẻ đẹp hồ Ba Bể và rừng trúc xanh ngút ngàn.',
      description:'Tour dành cho người muốn cảm nhận nhiều lớp của Thái Nguyên nhưng không muốn mỗi ngày thay một chỗ ngủ. Tuyến nghỉ một đêm tại Định Hóa và hai đêm ở Ba Bể; ngày chuyển vùng có buổi sáng ngắn và phần đường dài được dành riêng. Lịch trình cân bằng câu chuyện lịch sử với những khoảng xanh để nghỉ ngơi.',
      audience:'Nhóm gia đình có thể đi bộ dốc nhẹ, nhóm bạn thích văn hóa và thiên nhiên; phù hợp khách có bốn ngày trọn vẹn.',difficulty:'Vừa — nhiều chặng xe miền núi, bậc thang tại di tích và lối dốc rừng trúc.',group:'10–16 khách.',season:'Ưu tiên chuỗi ngày thời tiết ổn định; dự phòng thay điểm thác và rừng trúc khi đường ẩm trơn.',transport:'Xe riêng; ngày đầu nối Tân Cương–Định Hóa, ngày hai dành buổi chiều chuyển đến Ba Bể khoảng 4–5 giờ kể cả nghỉ, ngày cuối từ Yến Dương về trung tâm theo tuyến khảo sát.',
      highlights:['Trải nghiệm trà trước khi lên miền gió ngàn.','Tách ATK và Khuôn Tát thành hai buổi để tránh lịch quá dày.','Một ngày hồ Ba Bể và điểm kết rừng trúc Yến Dương.'],
      itinerary:[day('Hương trà và dấu ấn ATK',['Trưa','Tối'],'01 đêm Định Hóa',[
        ['07:00–10:00','Khởi hành và Tân Cương','Từ trung tâm về đồi chè, dạo lối tham quan và thưởng trà tại cơ sở hẹn trước.'],
        ['10:00–13:30','Lên Định Hóa, ăn trưa','Dành 2–2,5 giờ cho xe và nghỉ, dùng bữa trưa trước phần tham quan lịch sử.'],
        ['13:30–16:30','Tìm hiểu ATK','Theo tuyến ban quản lý xác nhận, nghe thuyết minh tại cụm di tích; dừng nghỉ giữa các đoạn bậc thang.'],
        ['16:30–19:30','Nhận phòng và bữa tối','Nghỉ ở Định Hóa, dùng bữa địa phương; không ghép thêm thác vào cuối chiều.']
      ]),day('Khuôn Tát và con đường lên miền hồ',['Sáng','Trưa','Tối'],'Đêm 1 tại Ba Bể',[
        ['07:00–08:30','Ăn sáng, trả phòng','Chuẩn bị hành lý gọn, khởi hành đến khu vực thác Khuôn Tát.'],
        ['08:30–10:30','Khoảng xanh bên thác','Đi bộ đoạn được phép, ngắm cảnh từ vị trí phù hợp; không leo tầng cao.'],
        ['10:30–12:00','Bữa trưa sớm','Dùng bữa trước chặng xe dài, vệ sinh và nghỉ ngắn.'],
        ['12:00–17:00','Di chuyển đến Ba Bể','Dành trọn buổi chiều cho đường miền núi và một điểm nghỉ; không chèn thêm điểm tham quan giữa chặng.'],
        ['17:00–19:30','Nhận phòng và ăn tối','Ổn định chỗ nghỉ, dùng bữa và nghỉ sớm sau ngày chuyển vùng.']
      ]),day('Ba Bể thong thả',['Sáng','Trưa','Tối'],'Đêm 2 tại cùng cơ sở Ba Bể',[
        ['07:00–08:30','Ăn sáng và ra bến','Chuẩn bị tư trang gọn, nghe quy tắc lên xuống thuyền.'],
        ['08:30–11:30','Thuyền ngắm hồ','Dạo hồ theo tuyến cơ bản được phép, dừng ngắm cảnh; mặc áo phao suốt hành trình.'],
        ['11:30–14:30','Bữa trưa và khoảng nghỉ','Ăn trưa, về homestay nghỉ; không ép khách hoạt động liên tục.'],
        ['14:30–16:30','Tự do ven bản','Đi bộ gần nơi lưu trú hoặc trò chuyện với chủ nhà nếu thuận tiện; không tự xuống nước.'],
        ['18:00–20:00','Bữa tối miền hồ','Dùng bữa, chuẩn bị đồ để trả phòng sớm hôm sau.']
      ]),day('Qua miền trúc, về miền trà',['Sáng','Trưa'],'Không lưu trú',[
        ['06:30–08:30','Ăn sáng, về Yến Dương','Trả phòng sớm, di chuyển đến khu vực Phiêng Phàng theo cung đường được khảo sát.'],
        ['08:30–10:30','Dạo rừng trúc','Chọn đoạn phù hợp thể lực, chụp ảnh và nghe giới thiệu về đời sống địa phương; không nối thêm tuyến lên đỉnh.'],
        ['10:30–12:00','Ăn trưa, nghỉ trước chặng về','Dùng bữa tại cơ sở đặt trước, kiểm tra hành lý.'],
        ['12:00–18:00','Trở về Thái Nguyên','Chặng về có dừng nghỉ và thời gian đệm; kết thúc tại điểm đón.']
      ])],includedExtra:['03 đêm lưu trú: 01 đêm Định Hóa, 02 đêm Ba Bể.','Thưởng trà cơ bản, thuyết minh ATK, 01 chuyến thuyền hồ và dẫn đường rừng trúc khi tuyến yêu cầu.'],excludedExtra:['Hoạt động hang Thẳm Phầy, kayak/SUP, chương trình văn nghệ và các điểm ngoài danh sách.'],lodging:'01 đêm cơ sở tiêu chuẩn Định Hóa và 02 đêm homestay Ba Bể; loại phòng xác nhận theo đoàn.',food:'03 bữa sáng, 07 bữa chính; thực đơn luân phiên theo địa phương và nguyên liệu sẵn có.',notes:['Đây là tuyến nhiều ngày, không khuyến nghị rút xuống hai ngày vì tăng thời gian ngồi xe và giảm chất lượng trải nghiệm.','Ngày cuối cần xuất phát sớm; khách cần chuyến bay/tàu nối tiếp nên dành đệm riêng.'],weatherPlan:'Bỏ thác/rừng trúc khi không phù hợp, thay bằng thời gian nghỉ và nội dung trong nhà có thể xác nhận. Chuyến thuyền chỉ thực hiện khi được phép hoạt động.'},
    {id:110,code:'TJ10',slug:'vong-cung-mien-xanh',name:'Vòng cung miền xanh — Trà, thảo nguyên và Ba Bể',destinationIds:['tan-cuong','sam-chiem','ban-chang','yen-duong','ba-be'],days:5,price:5990000,priceMax:7190000,tags:['Thiên nhiên','Nhiếp ảnh','Khám phá','Vòng cung Đông Bắc'],label:'CHUYẾN ĐI ĐỂ NHỚ',image:'prairie.svg',imageCaption:'Minh họa chủ đề vòng cung miền xanh; không phải ảnh điểm đến.',
      summary:'Đại hành trình năm ngày khám phá Đông Bắc: đắm chìm giữa đồi chè Tân Cương, thảo nguyên Sam Chiêm, hồ Bản Chang, rừng trúc và du ngoạn hồ Ba Bể.',
      description:'Đây là tour dài nhất trong bộ sưu tập, phù hợp người muốn khám phá không gian du lịch mở rộng của Thái Nguyên. Tuyến đi lần lượt từ vùng trà lên Ngân Sơn rồi chuyển sang Ba Bể, hạn chế quay lại cùng một đường chỉ để thêm điểm. Không ghép Thẳm Phầy vào lịch này để giữ nhịp trải nghiệm vừa phải và đủ khoảng nghỉ.',
      audience:'Nhóm bạn, người yêu ảnh phong cảnh, khách có năm ngày trọn vẹn và chấp nhận nhiều chặng xe đường núi.',difficulty:'Vừa — đường dốc ở Sam Chiêm/rừng trúc và nhiều lần di chuyển; không phải tour nghỉ dưỡng tiếp cận hoàn toàn bằng xe.',group:'8–12 khách; giá tính theo 10 khách.',season:'Ưu tiên chuỗi ngày khô, dự phòng một hoạt động ngoài trời bị thay đổi; cảnh mây, cỏ và nắng không được bảo đảm.',transport:'Xe riêng; ngày một chuyển từ Tân Cương lên Ngân Sơn, ngày ba dành khoảng 3–4 giờ chuyển vùng Ngân Sơn–Yến Dương, ngày năm khoảng 5 giờ về trung tâm; toàn bộ là quỹ giờ cần khảo sát, không phải cam kết quãng đường.',
      highlights:['Năm sắc thái cảnh quan trong một tuyến kết hợp.','Hai đêm Ngân Sơn, hai đêm Ba Bể: giảm số lần đổi nơi nghỉ.','Có ngày riêng cho Sam Chiêm–Bản Chang và ngày riêng cho mặt hồ Ba Bể.'],
      itinerary:[day('Hương trà mở lối',['Trưa','Tối'],'Đêm 1 khu vực Ngân Sơn',[
        ['07:00–10:00','Đón khách và trải nghiệm Tân Cương','Đi từ trung tâm về vùng chè, thưởng trà và dạo đồi trên lối cho phép; mở đầu chuyến đi bằng nhịp thật chậm.'],
        ['10:00–12:00','Khởi hành về phía Bắc','Lên xe, dành một điểm nghỉ trước bữa trưa trên tuyến.'],
        ['12:00–13:00','Dùng bữa trưa','Ăn tại cơ sở đặt trước, bổ sung nước và nghỉ.'],
        ['13:00–17:00','Tiếp tục lên Ngân Sơn','Đi xe với khoảng đệm cho giao thông và đường núi; nhận phòng khi đến.'],
        ['18:00–20:00','Ăn tối, nghỉ ngơi','Thống nhất kế hoạch thời tiết ngày hai, không tổ chức thêm hoạt động đêm bắt buộc.']
      ]),day('Triền cỏ và mặt hồ vùng cao',['Sáng','Trưa','Tối'],'Đêm 2 tại cùng cơ sở Ngân Sơn',[
        ['06:30–08:30','Đến Sam Chiêm','Ăn sáng, đi xe và trung chuyển theo tuyến được kiểm tra; không cam kết lên thảo nguyên bằng xe lớn.'],
        ['08:30–11:00','Chạm vào khoảng trời rộng','Đi bộ trên triền cỏ được phép, chụp ảnh và nghỉ; không săn bình minh bằng cách đi đêm trên tuyến chưa xác nhận.'],
        ['11:00–13:30','Xuống điểm dịch vụ, ăn trưa','Rời thảo nguyên, ăn trưa và nghỉ trước khi đến hồ.'],
        ['13:30–16:30','Hồ Bản Chang','Di chuyển, đi bộ ven bờ tại khu được phép và chụp ảnh; phần còn lại dành nghỉ chân, không bao gồm hoạt động dưới nước.'],
        ['16:30–19:30','Về lại nơi nghỉ','Trở về cơ sở, dùng bữa tối, chuẩn bị hành lý cho ngày chuyển vùng.']
      ]),day('Qua miền trúc đến Ba Bể',['Sáng','Trưa','Tối'],'Đêm 1 tại Ba Bể',[
        ['07:00–11:30','Ngân Sơn đến Yến Dương','Ăn sáng, trả phòng và di chuyển; có thời gian đệm cho tuyến miền núi và dừng nghỉ.'],
        ['11:30–13:00','Bữa trưa ở khu vực Phiêng Phàng','Dùng bữa đã đặt, chuẩn bị giày và nước cho đoạn đi bộ.'],
        ['13:00–15:00','Đi giữa rừng trúc','Tham quan đoạn lối mở, chụp ảnh dưới tán trúc; không ghép leo núi Pù Lầu hoặc đi thác vào cùng buổi.'],
        ['15:00–17:30','Chuyển về homestay Ba Bể','Dành đủ thời gian xe, nhận phòng và nghỉ; không cố đi thuyền khi đã muộn.'],
        ['18:30–20:00','Bữa tối đầu tiên ở miền hồ','Ăn tối, nghe hướng dẫn sinh hoạt tại cơ sở lưu trú.']
      ]),day('Ở lại cùng Ba Bể',['Sáng','Trưa','Tối'],'Đêm 2 tại cùng cơ sở Ba Bể',[
        ['07:00–08:30','Bữa sáng và chuẩn bị','Tập trung theo giờ bến, kiểm tra áo phao và sức chứa tàu cùng người vận hành.'],
        ['08:30–11:30','Du ngoạn mặt hồ','Theo tuyến thuyền cơ bản đã đặt; ngắm cảnh núi, mặt nước và chụp ảnh từ vị trí ổn định.'],
        ['11:30–14:30','Ăn trưa và nghỉ','Về điểm dùng bữa, nghỉ trưa dài sau ba ngày di chuyển.'],
        ['14:30–16:30','Thời gian của riêng bạn','Nghỉ ở homestay hoặc đi bộ gần bản theo hướng dẫn; các trải nghiệm bổ sung cần đặt riêng và xem điều kiện.'],
        ['18:00–20:00','Bữa tối khép lại vòng cung','Cả nhóm chia sẻ những bức ảnh và kỷ niệm của chuyến đi; không mặc định có biểu diễn nghệ thuật.']
      ]),day('Mang miền xanh về nhà',['Sáng','Trưa'],'Không lưu trú',[
        ['07:00–09:00','Buổi sáng thư thả','Ăn sáng, thu xếp hành lý và kiểm tra đồ dùng trước giờ trả phòng.'],
        ['09:00–11:30','Khởi hành về Thái Nguyên','Dành thời gian cho chặng đầu và một điểm nghỉ nếu cần.'],
        ['11:30–12:30','Ăn trưa dọc đường','Bữa trưa cuối của đoàn tại cơ sở trên tuyến.'],
        ['12:30–17:00','Trở về điểm hẹn','Tiếp tục chặng về với quỹ thời gian đệm; kết thúc vòng cung tại trung tâm Thái Nguyên.']
      ])],includedExtra:['04 đêm lưu trú: 02 Ngân Sơn, 02 Ba Bể.','Buổi thưởng trà, dẫn đường Sam Chiêm/rừng trúc và trung chuyển tiêu chuẩn theo tuyến được xác nhận.','01 chuyến thuyền hồ Ba Bể cơ bản cho đoàn, có áo phao.'],excludedExtra:['Hang Thẳm Phầy, camping qua đêm, SUP/kayak, hoạt động kỹ thuật, dịch vụ chụp ảnh riêng.'],lodging:'Hai cơ sở lưu trú, mỗi nơi 02 đêm; loại phòng và tiện nghi cần chốt bằng văn bản trước khi bán.',food:'04 bữa sáng và 09 bữa chính; đổi thực đơn giữa các ngày, báo trước ăn chay/dị ứng.',notes:['Không ghép toàn bộ 13 điểm vào một chuyến năm ngày; ưu tiên chất lượng thời gian tại từng cụm.','Chặng cuối có thể kết thúc muộn do điều kiện đường; không hẹn chuyến bay sát giờ trả khách.'],weatherPlan:'Nếu Sam Chiêm/rừng trúc không tiếp cận được, lùi giờ hoặc bỏ điểm sau khi trao đổi với đoàn; lịch nghỉ và thuyền cũng điều chỉnh theo điều kiện thực tế, đối soát dịch vụ thay thế.'}
  ];
  const photo=(file,caption)=>({image:'tours/'+file,caption});
  const photos={
    tea:photo('doi-che-tan-cuong.jpg','Ảnh minh họa đồi chè cho hành trình Tân Cương · Bộ ảnh chủ website cung cấp.'),
    atk:photo('atk-dinh-hoa.jpg','ATK Định Hóa · Bộ ảnh chủ website cung cấp.'),
    nuiCoc:photo('ho-nui-coc.jpg','Ảnh minh họa cảnh hồ cho hành trình Núi Cốc · Bộ ảnh chủ website cung cấp.'),
    baBe:photo('ho-ba-be.jpg','Hồ Ba Bể · Bộ ảnh chủ website cung cấp.'),
    stream:photo('suoi-cua-tu.jpg','Ảnh minh họa trải nghiệm suối cho hành trình Cửa Tử · Bộ ảnh chủ website cung cấp.'),
    waterfall:photo('thac-khuon-tat.jpg','Thác Khuôn Tát · Bộ ảnh chủ website cung cấp.'),
    prairie:photo('thao-nguyen-sam-chiem.jpg','Thảo nguyên Sam Chiêm · Bộ ảnh chủ website cung cấp.'),
    stay:photo('nha-san-minh-hoa.png','Ảnh minh họa không gian nhà sàn, chưa xác định địa điểm; không phải cơ sở lưu trú đã xác nhận trong tour.')
  };
  const tourPhotos={TJ01:['tea','nuiCoc'],TJ02:['tea'],TJ03:['atk','waterfall'],TJ04:['stay'],TJ05:['stream','nuiCoc','tea'],TJ06:['baBe'],TJ07:['prairie'],TJ08:['baBe'],TJ09:['waterfall','atk','tea','baBe'],TJ10:['prairie','tea','baBe']};
  const tours=list.map(t=>{const gallery=tourPhotos[t.code].map(key=>photos[key]);const stops=t.destinationIds.map(id=>places.find(p=>p.id===id));return {...common,...t,image:gallery[0].image,imageCaption:gallery[0].caption,gallery,nights:t.days-1,tag:t.tags[0],places:stops.map(p=>p.name),stops,itinerary:t.itinerary.map((d,i)=>({...d,day:i+1})),included:[...common.included,...t.includedExtra],excluded:[...common.excluded,...t.excludedExtra],packing:[...common.packing,...(t.packingExtra||[])],sourceIds:[...new Set(t.destinationIds.flatMap(id=>places.find(p=>p.id===id).sourceIds))]};});
  return {schemaVersion:1,updatedAt:'2026-10-14',editorialNote:'10 tour do Trà Journey biên soạn. Nguồn dùng để đối chiếu điểm đến; tên tour, giờ, giá, dịch vụ và phối tuyến là đề xuất biên tập, chưa được nhà cung cấp xác nhận.',sources,places,common,tours};
})();
