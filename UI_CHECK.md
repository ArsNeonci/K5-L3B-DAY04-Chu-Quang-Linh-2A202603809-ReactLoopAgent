# Kiểm tra giao diện và mức sẵn sàng nộp bài

> **Cập nhật 12/11/2026:** report trước hiện là **99,77**, không còn khớp baseline
> 100 được nhắc bên dưới. Xem [REPORT_PROVENANCE.md](REPORT_PROVENANCE.md).
> Kết quả Live là lượt kiểm tra đã lưu, không bảo đảm server vẫn đang chạy.
> Người học đã cho phép commit/push trạng thái hiện tại.

## Kết quả kiểm tra Live

- Cổng `8765` do công cụ/agent mở sẵn trả `PROVIDER_ERROR: RuntimeError` sau
  ba lần thử gọi model. Chưa tới bước gọi status tool. Phát lại H1 vẫn hoạt động.
- Cùng cấu hình và key, Gemini hoạt động khi kiểm tra ngoài môi trường đó.
- Server Windows được khởi động riêng ở **http://127.0.0.1:8766/**. Không dừng
  hoặc thay thế server cũ không thuộc tiến trình vừa tạo.
- Lượt Live xác nhận cuối: `completed`, **2 model calls**, **1 tool call** thành
  công; câu trả lời nêu đúng thời điểm lấy dữ liệu từ API thật. Trace lưu ở
  `artifacts/demo_live_verified.json`.
- Kiểm tra qua endpoint và luồng NDJSON của giao diện, không phải kiểm tra trực
  quan bằng trình duyệt. Cấu hình không đưa API key xuống frontend.

Không đủ bằng chứng để quy lỗi server cũ cho một firewall hoặc proxy cụ thể.
Kết quả đối chiếu xác nhận lỗi nằm ở đường gọi model của môi trường server cũ,
không phải hai status API và không phải key cấu hình hiện tại bị thiếu.

## Các lỗi đã sửa

1. Agent nhận thêm ngữ cảnh khi `tools.mode == 'live'`, để gọi `captured_at` là
   thời điểm lấy dữ liệu thay vì nhầm với snapshot lưu sẵn. Prompt Snapshot giữ
   nguyên, có regression test xác nhận.
2. Frontend loại dấu đóng Markdown và dấu câu ở cuối URL khỏi thuộc tính `href`.
   Nội dung model vẫn hiển thị bằng text nodes để không thực thi HTML.
3. **56/56 unit tests pass**. Kiểm tra renderer bằng Node cũng xác nhận URL đúng
   và nội dung HTML từ model vẫn là text.

## Cách dùng lại

Server kiểm tra đang phục vụ ở cổng `8766`; mở URL đó và chọn **Live**. Nếu khởi
động lại trong terminal Windows khi cổng đã trống, dùng:

```powershell
python scripts/with_env.py demo_server.py --port 8766
```

Snapshot và Live đều gọi LLM thật. Phát lại H1 chỉ đọc kết quả đã lưu và không
điều tra câu hỏi mới. Budget giao diện có thể khác `max_steps=8` của bộ eval.

## Trạng thái nộp bài

- Hồ sơ bắt buộc đã có: `agent.py`, `eval_before.json`, `eval_after.json`,
  `NOTES.md`. Hai report đủ 22 case, điểm lần lượt 100 và 99,91.
- Code giao diện có thêm callback theo dõi event và nhánh ngữ cảnh Live sau khi
  chốt cặp report. Điểm hai report là của phiên bản đã đánh giá, không phải một
  lần chấm mới cho mọi thay đổi UI. Chưa chạy lại 22 case cho bản UI mới.
- `artifacts/evaluated_agent.py` lưu đúng bản agent đã dùng cho eval sau, được
  kiểm chứng SHA-256 khớp `artifacts/comparison.json`. Không thay thế code hiện tại.
- Chưa commit/push theo yêu cầu người học. Cần chốt phiên bản nộp, tự demo CP6,
  cập nhật GitHub và nộp link trên LMS khi sẵn sàng. Bonus không bắt buộc.
