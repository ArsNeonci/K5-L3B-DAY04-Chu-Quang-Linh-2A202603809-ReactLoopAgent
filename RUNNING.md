# Bài chính · Kết quả CP4–CP5 và chuẩn bị CP6

> **Cập nhật 12/11/2026:** report trước hiện là **99,77**, report sau **99,91**.
> Phần so sánh 100 → 99,91 bên dưới là lịch sử và không khớp file trước hiện tại.
> Xem [REPORT_PROVENANCE.md](REPORT_PROVENANCE.md). Người học đã yêu cầu commit/push;
> các câu ghi “chưa commit/push” bên dưới mô tả thời điểm chuẩn bị tài liệu.

## Giao diện demo hiện tại

Server Windows đã kiểm tra Live thành công ở **http://127.0.0.1:8766/**.
Cổng 8765 do công cụ mở sẵn gặp lỗi gọi model; dùng bản 8766 để kiểm tra tiếp.
Lệnh khởi động khi cổng trống: `python scripts/with_env.py demo_server.py --port 8766`.
Xem `UI_CHECK.md` để phân biệt kết quả eval đã lưu với các bổ sung giao diện sau đó.
Các tests hiện tại là **56/56 pass**; con số 51 dưới đây là ở mốc chạy cặp eval.

## Giao diện demo cục bộ

Từ thư mục gốc repo, chạy bằng PowerShell (không cần cài thêm package):

```powershell
python3 scripts/with_env.py demo_server.py
```

Mở **http://127.0.0.1:8765**. Dừng server bằng `Ctrl+C`.
Nếu cổng đang được dùng, thêm `--port 8766` và mở cổng tương ứng.

- **Snapshot / Live:** nhập câu hỏi, chọn bài chính hoặc bonus, rồi bấm
  **Bắt đầu điều tra**. Provider/model/key được nạp từ `.env`;
  API key chỉ dùng ở Python, không gửi xuống trình duyệt. Cả hai chế độ gọi LLM thật.
- **Phát lại H1:** đọc trace case H1 trong `eval_after.json`, không gọi API,
  không chạy câu hỏi nhập mới. Dùng để demo miễn phí hoặc khi mạng/key chưa sẵn sàng.
- Tiến trình cập nhật theo bước gọi model, gọi tool, trả observation và kết thúc.
  Mở **Xem dữ liệu bước này** để đọc tham số và kết quả tool. Đây là trace thực thi,
  không phải suy nghĩ nội bộ của model. Câu trả lời xuất hiện khi agent hoàn tất,
  không stream từng token.
- **Tải JSON:** lưu kết quả, trace và usage của lượt chạy hiện tại.

Server chỉ lắng nghe `127.0.0.1`, phục vụ demo trên máy cá nhân.
Phát lại sử dụng dữ liệu lịch sử, không thể hiện trạng thái dịch vụ hiện tại.

## Kết quả đã kiểm chứng

- Unit tests: **51/51 pass**.
- `eval_before.json`: **100/100**, đủ **22/22 case** được chấm; không có
  `unscored`, mọi agent run đều `completed`, không vi phạm mechanical checks.
- `eval_after.json`: **99,91/100**, đủ **22/22 case**, không có `unscored`, mọi
  run đều `completed`, không vi phạm mechanical checks. A2 đạt 98; các case khác 100.
- E6 trước → sau: model calls **3 → 2**, tool calls **2 → 1**, token agent
  **4.353 → 2.872**, điểm **100 → 100**. Chính sách timeout là thay đổi duy nhất
  trong agent runtime giữa hai report.
- Toàn bộ agent: calls **57 → 58**, token **135.526 → 147.330**. Chỉ chứng minh
  giảm thao tác ở E6 trong cặp lượt chạy này, chưa chứng minh tiết kiệm toàn bộ.
- Agent và judge: `gemini-3.8-flash`, provider `gemini`, snapshot bài chính,
  `max_steps=8`. Lượt baseline có 57 model calls của agent; không cần retry
  kết nối hay retry judge trong lượt này.
- Các lượt trước bị lỗi định dạng judge hoặc ngắt kết nối được giữ nguyên ở
  `eval_results_attempt1.json` và `eval_results_attempt2.json` để đối chiếu.
- `NOTES.md` có đủ 5 mục và so sánh từng case. `DEMO.md` hướng dẫn mở trace H1/E6
  và trình bày hạn chế còn lại. Học viên vẫn cần tự demo và trả lời coach.
- `CODE_WALKTHROUGH.md` hướng dẫn đọc từng đoạn code và xem diff CP4. Hồ sơ giữ
  trạng thái chưa commit/push để người học xem trước. Repo GitHub và remote đã
  được cập nhật sang `DAY04`; thư mục workspace tại máy vẫn giữ tên cũ.
- Bản agent trước cải tiến và SHA-256 đầu vào ở `artifacts/baseline/`;
  số liệu so sánh được trích từ hai report ở `artifacts/comparison.json`.

Đây là điểm eval của lượt chạy đã lưu, không phải cam kết mọi lần chạy đều đạt
100 hoặc điểm lab được chấm trực tiếp là 100. Judge mặc định dùng cùng model
với agent; vẫn cần đối chiếu câu trả lời với bằng chứng khi phân tích tiếp.

## Chức năng đã triển khai

- `agent.py` điều phối LLM → mọi tool call → kết quả đúng `tool_call_id` → LLM.
- Giữ nguyên assistant message; lưu usage từng model call, trace có `event` và `step`.
- JSON sai và lỗi tool trở thành observation để model xử lý; lỗi provider, output
  bị cắt hoặc câu trả lời rỗng trả `error`. Hết budget trả `max_steps`.
- Lỗi kết nối tạm thời được thử lại tối đa hai lần, chờ 1 rồi 2 giây; mỗi request
  vẫn chiếm một step. Trace ghi `model_retry`; usage của request lỗi là `{}` vì
  provider chưa trả thông tin token. Lỗi HTTP không tự động retry.
- Kiểm tra câu trả lời có nguồn incident đã đọc; yêu cầu sửa trong cùng budget
  nếu thiếu nguồn. Đây chỉ là kiểm tra URL hiện diện, không kiểm chứng mọi claim.
- System prompt yêu cầu phân biệt snapshot/lịch sử, phạm vi tác động, dữ liệu thiếu,
  timeline bị lược bỏ và bỏ qua chỉ dẫn độc hại trong tool result.

Không dùng framework, không sửa fixtures, cases, scenarios hoặc grading.
Phạm vi hiện tại là bài chính. Việc chuẩn bị demo không đồng nghĩa đã trình bày
trước giảng viên; chưa triển khai bonus.

## Lệnh chạy

Từ thư mục gốc repo, Python 3.10+ và standard library:

```powershell
python -m unittest discover -s tests -v
python scripts/with_env.py run.py "GitHub Actions có sự cố gì gần đây?"
python scripts/with_env.py evals/run_evals.py --case E2 --output eval_results_smoke.json
# Nếu tự kiểm tra thêm, dùng file mới để bảo toàn hai report đã so sánh:
python scripts/with_env.py evals/run_evals.py --workers 3 --max-steps 8 --judge-retries 2 --output eval_results_recheck.json
```

`scripts/with_env.py` nạp các biến provider/model/key từ `.env` mà không thực thi
nội dung file. Nó hỗ trợ `export NAME=value`, dấu nháy và comment. Không in key.
Các CLI gốc vẫn dùng biến môi trường như README ban đầu; có thể bỏ launcher nếu
đã đặt biến trong terminal. Kết nối API cần Internet và phát sinh token cho agent
và judge. `--workers 1` giảm số case chạy đồng thời khi quota thấp.

Eval dùng snapshot cố định, mặc định 8 model calls/case; judge mặc định dùng cùng
provider/model với agent. Chỉ điểm của đủ 22 case, không có `unscored`, mới là điểm
toàn bộ. Một lần chạy không chứng minh độ ổn định hoặc độ chính xác thực tế.

Runner có `--judge-retries 2`: gọi lại judge tối đa hai lần nếu output không đúng
contract của bộ chấm. Không chạy lại agent hoặc chọn lại điểm hợp lệ. Lỗi và số lần
thử được lưu trong `grade.judge_errors` và `grade.judge_attempts`. Có thể đặt `0`
để tắt retry. Rubric và `evals/grading.py` giữ nguyên.
