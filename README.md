# Chatbot Phân tích Phản hồi Sinh viên

Dự án này là một ứng dụng Web tương tác được xây dựng bằng **Streamlit**, tập trung vào việc áp dụng Xử lý ngôn ngữ tự nhiên (NLP) để phân tích cảm xúc và trích xuất từ khóa từ các luồng đánh giá/phản hồi của sinh viên. 

| STT | Mã Số Sinh Viên | Họ và Tên |
| :--- | :--- | :--- |
| 1 | 123000882 | Trần Trọng Khang |
| 2 | | |

## Danh sách 15 Yêu cầu (TODOs) Đã Hoàn Thành

Dưới đây là nội dung toàn bộ 15 yêu cầu kỹ thuật (TODO items) đã được triển khai đầy đủ và tích hợp trên phiên bản hiện tại:

1. **TODO 1:** Mở rộng danh sách STOPWORDS tiếng Việt (hiện chỉ ~40 từ, nên dùng file ngoài hoặc thư viện chuẩn). Dữ liệu được lưu tại `stopwords_vi.txt`.
2. **TODO 2:** Thêm caching (`@st.cache_resource` / `@st.cache_data`) cho model `underthesea` để tránh load lại mỗi lần rerun trang.
3. **TODO 3:** Hỗ trợ upload file CSV/Excel phản hồi bên cạnh nhập tay trực tiếp qua khung chat.
4. **TODO 4:** Thêm chức năng xuất lịch sử phân tích ra CSV/Excel (sử dụng nút download được đặt ở khu vực Sidebar).
5. **TODO 5:** Hiển thị Word Cloud (đám mây từ khóa) trực quan dựa trên thư viện `wordcloud` thay vì chỉ sử dụng list/bảng top 10 thông thường.
6. **TODO 6:** Thêm biểu đồ xu hướng cảm xúc theo thời gian (timeline) khi có nhiều phản hồi.
7. **TODO 7:** Cho phép người dùng chỉnh sửa / xóa từng phản hồi đã gửi trong danh sách lịch sử chat (Quản lý log).
8. **TODO 8:** Thêm confidence score (độ tin cậy) cho kết quả phân tích cảm xúc định lượng (nếu model/hệ thống hỗ trợ).
9. **TODO 9:** Hỗ trợ phân tích đa ngôn ngữ (sử dụng `langdetect`) để phát hiện loại ngôn ngữ trước khi chọn pipeline phân tích.
10. **TODO 10:** Thêm phần trang "Hướng dẫn sử dụng" (Expander) ở Sidebar giải thích chi tiết ý nghĩa của từng chỉ báo từ hệ thống.
11. **TODO 11:** Persist (lưu trữ dài hạn) lịch sử chat vào tệp `history.csv` / `history.json` để bảo toàn dữ liệu khi tải lại cửa sổ duyệt web.
12. **TODO 12:** Thêm chế độ so sánh: cho phép so sánh cảm xúc của 2 nửa dữ liệu (VD: trước/sau cải tiến).
13. **TODO 13:** Xử lý và bắt lỗi Edge case: Phản hồi quá ngắn (dưới 3 ký tự), chỉ chứa mỗi Emoji, hoặc chỉ có ký tự đặc biệt không ý nghĩa.
14. **TODO 14:** Thêm file `test_chatbot.py` phục vụ cho việc chạy Unit test (xây dựng bằng `unittest`) cho các hàm tính toán lõi bao gồm `analyze_feedback` và `render_analysis`.
15. **TODO 15:** Tách logic Model AI và NLP riêng ra module hệ thống (`analyzer.py`) để dễ dàng làm việc, test và tái sử dụng cho các nền tảng/file khác mà không bị lệ thuộc vào Streamlit UI.

---

## Cách cài đặt và Chạy ứng dụng

1. Đảm bảo bạn đã cài đặt các thư viện thiết lập môi trường:
   ```bash
   pip install streamlit pandas underthesea wordcloud matplotlib plotly langdetect
   ```

2. Chạy ứng dụng Chatbot qua lệnh:
   ```bash
   streamlit run app_chatbot_todo.py
   ```

3. Chạy môi trường kiểm thử (Unit test):
   ```bash
   python -m unittest test_chatbot.py -v
   ```
