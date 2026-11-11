# Trạng thái hồ sơ bài chính

> **Cập nhật trước commit ngày 12/11/2026:** người học đã yêu cầu commit và push
> lên `main`; quyết định giữ bài ở workspace bên dưới đã được thay thế.
> **Chưa thể xác nhận hoàn tất bằng chứng CP3–CP5:** report trước hiện đạt
> **99,77**, không khớp baseline 100 trong checklist lịch sử.
> Xem [REPORT_PROVENANCE.md](REPORT_PROVENANCE.md). 56/56 tests đã chạy lại và pass.

## Đã kiểm chứng tại workspace

- [x] `agent.py` hoàn thiện; CP4 chỉ thêm một chính sách tool timeout so với baseline.
- [x] `eval_before.json`: 100/100, đủ 22 case được chấm.
- [x] `eval_after.json`: 99,91/100, đủ 22 case được chấm.
- [x] Hai lần dùng cùng model agent/judge, snapshot, max steps, dataset và runner.
- [x] 56 unit tests hiện tại pass, gồm đầy đủ `EvidenceGateTests` và tests demo.
- [x] `NOTES.md` đủ 5 mục, dẫn trace trước/sau và nêu cả kết quả chưa thuận lợi.
- [x] `DEMO.md` có trace H1 nhiều bước và E6 để học viên tự trình bày CP6.
- [x] `CODE_WALKTHROUGH.md` giải thích vòng lặp, phần thay đổi CP4 và cách xem diff.
- [x] Baseline và dữ liệu/rubric không thay đổi; có SHA-256 để kiểm tra.
- [x] Kiểm tra không thấy API key trong các file thay đổi và report; `.env` không được git track.
- [x] Repo origin là public, truy cập được bằng GitHub API không đăng nhập.
- [x] Kiểm tra Live qua giao diện/API trên server Windows cổng 8766 hoàn tất.

Hai report eval thuộc phiên bản đã lưu trước các bổ sung giao diện. Bản tương
ứng chính xác được bảo toàn ở `artifacts/evaluated_agent.py`. Code hiện tại có
thêm callback và ngữ cảnh Live, đã kiểm tra unit tests và một lượt Live, chưa
chạy lại bộ 22 case cho bản UI mới. Chi tiết ở `UI_CHECK.md`.

Kết quả cục bộ E6: model calls 3 → 2, tool calls 2 → 1, token 4.353 → 2.872,
điểm 100 → 100. Toàn bộ agent lại tăng token 135.526 → 147.330; chưa chứng minh
tiết kiệm toàn bộ. Chi tiết và giới hạn nằm trong `NOTES.md`.

## Quyết định hiện tại của người học

Repo hiện tại:
[K5-L3B-DAY04-Chu-Quang-Linh-2A202603809-ReactLoopAgent](https://github.com/ArsNeonci/K5-L3B-DAY04-Chu-Quang-Linh-2A202603809-ReactLoopAgent)

Người học đã đổi tên trên GitHub thành `DAY04`. Trang repo mới đã được kiểm tra
truy cập thành công; remote `origin` tại máy được cập nhật theo URL mới.

**Chưa commit/push**, để người học quan sát và học code. Hồ sơ tại workspace đã
có đủ các file bắt buộc; các thay đổi mới chưa được đưa lên GitHub. Tên thư mục
workspace tại máy giữ nguyên để không ảnh hưởng phiên làm việc đang mở.

## Công việc người học còn thực hiện

- [x] Chuẩn hóa tên repo GitHub thành `DAY04` và cập nhật remote tại máy.
- [ ] Đọc và tự giải thích code theo `CODE_WALKTHROUGH.md`.
- [ ] Quyết định thời điểm commit/push sau khi đã xem code.
- [ ] Tự trình bày demo CP6 và trả lời câu hỏi của giảng viên.
- [ ] Kiểm tra phiên bản trên GitHub có đủ hồ sơ sau khi push.
- [ ] Tự nộp link repo trên LMS đúng lớp L3B; việc nộp LMS chưa được thực hiện.
- [ ] Xác nhận deadline với coach nếu cần: slide và tài liệu repo có khác biệt
  ở mốc ca chiều; không tự suy ra hạn nộp từ một trong hai nguồn.

Bonus không thuộc vòng cải tiến bài chính này và chưa được triển khai.
