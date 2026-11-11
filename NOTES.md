# Ghi chú phân tích · Day 04

> **Cập nhật 12/11/2026:** `eval_before.json` hiện là **99,77**, không khớp
> baseline 100 trong phân tích lịch sử dưới đây. Đọc [REPORT_PROVENANCE.md](REPORT_PROVENANCE.md)
> trước khi sử dụng số liệu hoặc trích trace; chưa xác minh lại được cặp CP3–CP5.

Họ và tên: Chu Quang Linh (viết theo tên repo)
MSSV: 2A202603809

## 1. Case được chọn

- ID case: **E6**.
- Câu hỏi: “GitHub Actions hiện có hoạt động bình thường không?”
- Điểm lần đầu: **100/100**.
- Vấn đề: hiệu quả xử lý tool timeout. Câu trả lời ban đầu đúng ranh giới bằng
  chứng, nhưng agent gọi lại cùng provider bằng cách bỏ bộ lọc `component`, không
  có tín hiệu cho thấy kết nối đã phục hồi.
- Giả thuyết: phân biệt rõ lỗi kết nối với kết quả tìm kiếm rỗng sẽ giúp tránh lần
  gọi này. Mục tiêu E6 là model calls 3 → 2, tool calls 2 → 1, giữ chất lượng trả lời.

Trích câu trả lời thực tế trước cải tiến, từ `eval_before.json`, case E6:

> Hiện tại, hệ thống không thể kiểm tra trạng thái của **GitHub Actions** do gặp lỗi gián đoạn kết nối (Timeout) khi truy vấn dữ liệu từ GitHub Status.

> **Lưu ý:** Lỗi truy vấn này chỉ đồng nghĩa với việc không lấy được dữ liệu trạng thái ở thời điểm hiện tại, không phải là bằng chứng cho thấy GitHub Actions đang gặp sự cố (outage) hay đang hoạt động bình thường.

## 2. Bằng chứng trong trace

Nguồn: `eval_before.json`, case E6, `result.trace`. Dưới đây trích các trường cần
thiết của hai tool events; report gốc giữ nguyên cả `tool_call_id` và các events khác.

```json
[
  {
    "event": "tool", "step": 1, "name": "get_status",
    "arguments": {"provider": "github", "component": "Actions"},
    "result": {"ok": false, "error": "TimeoutError", "message": "Không thể lấy dữ liệu status (timeout giả lập)."}
  },
  {
    "event": "tool", "step": 2, "name": "get_status",
    "arguments": {"provider": "github"},
    "result": {"ok": false, "error": "TimeoutError", "message": "Không thể lấy dữ liệu status (timeout giả lập)."}
  }
]
```

Step 1 timeout; step 2 bỏ `component` nhưng vẫn timeout. Lần thử thứ hai không bổ
sung bằng chứng trong lượt chạy này. Trace không chứng minh mọi retry timeout
ngoài thực tế đều vô ích. Giả thuyết nguyên nhân: prompt cũ hướng dẫn mở rộng bộ
lọc khi tìm kiếm rỗng, nhưng chưa phân biệt đủ rõ với lỗi kết nối.

## 3. Thay đổi đã thực hiện

Chỉ thêm **một chính sách xử lý tool timeout**, gồm 4 dòng trong `SYSTEM_PROMPT`
của `agent.py`:

```text
- Khi tool trả TimeoutError, mặc định báo chưa kiểm tra được provider đó và tiếp tục
  các provider khác nếu có. Không gọi lại chỉ bằng cách đổi/bỏ component: bộ lọc
  không khắc phục lỗi kết nối. Chỉ retry khi có tín hiệu phục hồi rõ từ tool;
  không có tín hiệu đó thì dùng bằng chứng hiện có và nêu giới hạn.
```

- Áp dụng chung, không hard-code E6, câu hỏi hoặc incident ID.
- Không thay đổi loop, retry lỗi kết nối LLM, kiểm tra URL nguồn hoặc `max_steps`.
- Runner hiện có, provider, tools, fixtures, dataset và rubric giữ nguyên giữa
  hai lần eval. Bản trước cải tiến: `artifacts/baseline/agent.py`; SHA-256 các
  đầu vào: `artifacts/baseline/manifest.json`.
- Đánh đổi: dừng sớm có thể bỏ lỡ phục hồi sau timeout tạm thời khi tool không
  cung cấp tín hiệu phục hồi. Chính sách prompt không phải khóa cứng mọi retry.

## 4. So sánh hai lần chạy

### Điều kiện so sánh

- Agent và judge: provider `gemini`, model `gemini-3.8-flash`.
- Cùng snapshot và 22 case chính; `max_steps=8`, `judge_retries=2`, 3 workers.
- SHA-256 xác nhận baseline report và các đầu vào được bảo toàn. Chỉ `agent.py`
  thay đổi trong phần thực thi; ghi chú/demo không tham gia agent runtime.
- Sau sửa, **51/51 unit tests pass**, gồm cả ba `EvidenceGateTests`. Tests chạy
  ngoài sandbox để các test ghi thư mục tạm không bị lỗi quyền; không sửa tests.
- Cả hai report đủ 22 case, mọi run `completed`, không có mechanical violations.
- Lượt sau có một lần retry judge ở E2 vì output thiếu trường giải thích/đề xuất.
  Điểm hợp lệ được chấp nhận ngay, không chấm lại để chọn điểm cao hơn.

### Kết quả tổng hợp

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---:|---:|
| Điểm tổng | 100 | 99,91 |
| Case được chấm | 22/22 | 22/22 |
| Điểm E6 | 100 | 100 |
| Model calls E6 | 3 | 2 |
| Tool calls E6 | 2 | 1 |
| Token agent E6 | 4.353 | 2.872 |
| Model calls toàn bộ agent | 57 | 58 |
| Tool calls toàn bộ agent | 48 | 51 |
| Token toàn bộ agent | 135.526 | 147.330 |
| Lần gọi judge, kể cả output lỗi | 22 | 23 |
| Token judge ghi nhận ở lượt hợp lệ | 56.646 | 59.254 |
| Chi phí tiền thực tế | Chưa có billing | Chưa có billing |

Token agent là tổng `usage.total_tokens` của các model calls, không gồm judge.
Token judge ghi nhận chưa bao gồm đầy đủ request trả output không hợp lệ, vì bộ
chấm không giữ usage của request đó. Không coi các số này là hóa đơn.

### Bằng chứng sau cải tiến ở E6

Nguồn: `eval_after.json`, case E6, `result.trace`. Tool event duy nhất:

```json
{
  "event": "tool", "step": 1, "name": "get_status",
  "arguments": {"provider": "github", "component": "Actions"},
  "result": {"ok": false, "error": "TimeoutError", "message": "Không thể lấy dữ liệu status (timeout giả lập)."}
}
```

Ở step 2 model trả lời và dừng `completed`. Trích câu trả lời thực tế:

> Do thiếu dữ liệu kiểm tra, tôi không thể xác nhận GitHub Actions có đang hoạt động bình thường hay không. Lỗi kết nối này chỉ phản ánh việc không truy vấn được thông tin trạng thái, không đồng nghĩa với việc GitHub Actions đang gặp sự cố hay hoàn toàn bình thường.

**Kết luận cục bộ:** E6 giảm một model call, một tool call và **1.481 token
(34,02%)**, giữ điểm 100 và không đánh đồng timeout với trạng thái dịch vụ.

**Kết quả toàn bộ:** model calls tăng 57 → 58, tool calls tăng 48 → 51, token
agent tăng **11.804 (8,71%)**. E1 tăng 4 → 5 model calls; A5 tăng 2 → 3. Prompt
dài hơn và hành vi model biến động đều có thể góp phần; chưa đủ dữ liệu để tách
riêng tác động nhân quả. **Chưa chứng minh tối ưu chi phí toàn bộ.**

**Hạn chế còn lại:** A2 giảm 100 → 98. Theo `grade.reason`, câu trả lời đúng về
phạm vi FedRAMP nhưng nên nói thêm: không chịu tác động từ incident này không
loại trừ các nguyên nhân cache khác của CLB. A2 không gặp timeout, nên không
tự kết luận chính sách mới gây giảm điểm. Không thực hiện thay đổi thứ hai hay
chạy lại để chọn một điểm thuận lợi hơn.

### Điểm từng case

| Case | Trước | Sau |
|---|---:|---:|
| E1 | 100 | 100 |
| E2 | 100 | 100 |
| E3 | 100 | 100 |
| E4 | 100 | 100 |
| E5 | 100 | 100 |
| E6 | 100 | 100 |
| A1 | 100 | 100 |
| A2 | 100 | 98 |
| A3 | 100 | 100 |
| A4 | 100 | 100 |
| A5 | 100 | 100 |
| A6 | 100 | 100 |
| A7 | 100 | 100 |
| A8 | 100 | 100 |
| H1 | 100 | 100 |
| H2 | 100 | 100 |
| H3 | 100 | 100 |
| H4 | 100 | 100 |
| H5 | 100 | 100 |
| H6 | 100 | 100 |
| H7 | 100 | 100 |
| H8 | 100 | 100 |

Số calls/token và chênh lệch từng case được trích từ hai report tại
`artifacts/comparison.json`.

## 5. Giới hạn

- LLM judge là đánh giá xấp xỉ; dùng cùng model với agent có thể gây thiên lệch.
- Mỗi phiên bản chỉ chạy một lần. Chênh lệch còn chịu ảnh hưởng ngẫu nhiên của
  model; không quy toàn bộ biến động điểm/token cho thay đổi prompt.
- Snapshot không chứng minh trạng thái hiện tại; timeout E6 là mô phỏng. Cần
  kiểm tra thêm trước khi áp dụng chính sách vào hệ thống live.
- URL hiện diện không tự chứng minh mọi nhận định đều có bằng chứng.
- Chưa có giá và billing nên không quy đổi token thành chi phí tiền thực tế.
- Sau khi chốt cặp eval có bổ sung callback theo dõi event và ngữ cảnh riêng
  cho Live để phục vụ giao diện. Prompt Snapshot giữ nguyên theo tests; chưa
  chạy lại bộ 22 case cho các bổ sung UI. Bản agent khớp chính xác lượt eval
  sau ở `artifacts/evaluated_agent.py`; thông tin kiểm tra mới ở `UI_CHECK.md`.
