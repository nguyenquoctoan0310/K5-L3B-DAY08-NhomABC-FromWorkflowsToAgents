# Báo cáo cá nhân — Vũ Trọng Thắng

## 1. Thông tin thành viên

- Họ tên: Vũ Trọng Thắng
- MSSV: 2A202604022
- Email: mailto:tvu6483@gmail.com
- GitHub: https://github.com/Thangvipsv4

## 2. Phần việc phụ trách

- Phụ trách Shape B - Single Agent sử dụng mô hình ReAct.
- Triển khai và kiểm thử logic agent trong `src/lab8/shapes/single.py`.
- Kiểm tra cách agent sử dụng tool đọc, giới hạn số bước và phối hợp với host khi xử lý hoàn tiền.

## 3. Đóng góp cụ thể

- Triển khai vòng lặp ReAct thông qua `run_react` với giới hạn tối đa 8 bước.
- Xây dựng hàm `decide` để lựa chọn các tool đọc thông tin; agent không trực tiếp gọi thao tác ghi hoàn tiền.
- Lưu kết quả tool qua closure để sử dụng trong các bước suy luận tiếp theo.
- Tuân thủ ranh giới trách nhiệm: agent thu thập thông tin và đề xuất; host kiểm tra, thực hiện thao tác ghi và áp dụng các ràng buộc nghiệp vụ.
- Không thực hiện bonus B7 theo phạm vi công việc đã chọn.

## 4. Bằng chứng

- File phụ trách: `src/lab8/shapes/single.py`.
- Lệnh kiểm thử (chạy từ thư mục `src`):

  ```powershell
  python -m pytest -q -m student -o addopts= -k "single and not workflow and not orchestrator and not swarm"
  ```

- Kết quả do thành viên chạy trên máy cá nhân: **62 passed, 240 deselected in 3.93s**.
- Kết quả trên xác nhận toàn bộ 62 test được chọn trong lần chạy này đều đạt. Các test bị deselect không được tính là đã kiểm thử trong lần chạy đó.
- Commit hash và link commit: bổ sung sau khi commit phần triển khai Shape B lên repository nhóm.

## 5. Công cụ AI đã dùng

- ChatGPT: hỗ trợ phân tích yêu cầu Shape B, giải thích luồng ReAct, gợi ý cách triển khai và hỗ trợ đọc kết quả kiểm thử.
- Thành viên tự đối chiếu phần triển khai với yêu cầu của bài lab và trực tiếp chạy pytest trên máy cá nhân để kiểm tra.
- Lab sử dụng MockLLM theo seed; không sử dụng API của model thật trong quá trình chạy kiểm thử.

## 6. Tự đánh giá

- Hoàn thành phần triển khai Shape B theo phạm vi được phân công và đạt 62/62 test trong lần kiểm thử riêng đã thực hiện.

