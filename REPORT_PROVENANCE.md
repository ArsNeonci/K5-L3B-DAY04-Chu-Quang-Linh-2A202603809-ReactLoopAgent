# Đối chiếu report trước khi đưa bài lên GitHub

Kiểm tra ngày 12/11/2026, không chạy lại eval và không sửa điểm/report:

- `eval_before.json` hiện tại đạt **99,77/100**, đủ 22 case. SHA-256:
  `2ee99d402439efbf2e352e6986362c42cccf01971ded4b3bfbd778559ac0b0ba`.
- `eval_after.json` đạt **99,91/100**, đủ 22 case. SHA-256:
  `ed701bfec42dca2d6d75d6c825ec2cfdba940dc654675d3b1754a9491f5f007a`.
- Baseline 100 điểm được mô tả trong ghi chú, slide, `artifacts/comparison.json`
  và `artifacts/baseline/manifest.json` có hash
  `df12aaf16503aa5e7d4b6ea4da8ceb843e2d45b1d334598c03e25f610a752a74`.
  File hiện tại không khớp hash này; chưa tìm được bản report gốc trong workspace.

Vì vậy, các tài liệu phân tích cũ được giữ làm lịch sử làm bài, chưa thể dùng làm
đối chiếu có thể tái kiểm chứng với `eval_before.json` hiện tại. Cụ thể, E6 trong
report hiện tại đã có 2 model calls, 1 tool call và 2.923 token; report sau có
2 model calls, 1 tool call và 2.872 token. Không dùng hai file hiện tại để khẳng
định giảm 3 → 2 model calls, 2 → 1 tool calls hoặc giảm 34,02% token.

Cấu hình được ghi trong hai report hiện tại giống nhau, nhưng chưa xác minh được
phiên bản agent sinh ra report trước hiện tại. Chênh lệch điểm 99,77 → 99,91
không đủ chứng minh hiệu quả nhân quả của thay đổi CP4. Không tạo lại trace,
không phục dựng điểm và không ghi đè report để khớp tài liệu cũ.

`artifacts/evaluated_agent.py` giữ bản source khớp hash agent của lượt eval sau.
Code hiện tại có thêm callback giao diện và ngữ cảnh Live sau lượt eval đó.
Kiểm tra trước commit: **56/56 unit tests pass**; không chạy lại 22 case cho
phiên bản UI hiện tại. `.env` được Git bỏ qua; kiểm tra các file dự kiến commit
không thấy giá trị key từ `.env` hoặc mẫu credential thật.

Trước khi dùng hồ sơ này làm bằng chứng hoàn tất CP3–CP5, cần tìm lại report
baseline gốc hoặc thực hiện một cặp eval mới có lưu phiên bản source tương ứng.
Việc commit/push lưu trạng thái bài làm, không thay thế bước xác minh này hay
việc người học tự demo và nộp link trên LMS.
