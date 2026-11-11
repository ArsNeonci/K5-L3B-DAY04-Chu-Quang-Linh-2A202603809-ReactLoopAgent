# CP6 · Kịch bản demo với trace thật

> **Cập nhật 12/11/2026:** số liệu baseline 100 và trace E6 trước cải tiến bên dưới
> thuộc phân tích lịch sử. `eval_before.json` hiện là 99,77 và E6 đã có 1 tool call.
> Chưa dùng kịch bản này để khẳng định cải tiến CP4; xem [REPORT_PROVENANCE.md](REPORT_PROVENANCE.md).

## 1. Mở bằng kết quả và phạm vi

Bài chính có hai report đủ 22 case: trước **100/100**, sau **99,91/100**.
51 unit tests pass. Một thay đổi trong `agent.py` là chính sách dừng khi tool
timeout mà không có tín hiệu phục hồi. Đây là kết quả eval snapshot, không phải
chứng nhận hệ thống live hay điểm lab.

## 2. Trace nhiều bước: H1 sau cải tiến

Mở `eval_after.json`, tìm `"id": "H1"` (case index 14), rồi mở `result.trace`.
Không cần gọi lại API để trình bày trace đã lưu.

Câu hỏi thực tế:

> Điều tra incident GitHub h02n9572mx9y. Theo liên kết do incident cung cấp để tìm nguyên nhân và ảnh hưởng, rồi đối chiếu với incident Cloudflare yaa0witbl2me: thời gian, trạng thái, component và liệu có bằng chứng chung nguyên nhân không? Dẫn nguồn cho từng bên.

| Vị trí trong H1 | Model step | Tool | Provider / incident | Kết quả |
|---|---:|---|---|---|
| `result.trace[1]` | 1 | `get_incident_details` | `github` / `h02n9572mx9y` | `resolved`, URL `https://stspg.io/7pwv28hvkmz8` |
| `result.trace[2]` | 1 | `get_incident_details` | `cloudflare` / `yaa0witbl2me` | `resolved`, URL `https://www.cloudflarestatus.com/incidents/yaa0witbl2me` |
| `result.trace[4]` | 2 | `get_incident_details` | `github` / `xr3myzj7ms51` | `resolved`, URL `https://stspg.io/pjgptg3cfc6n` |

Những điểm cần chỉ vào bằng chứng:

1. Trong incident GitHub đầu tiên, `updates[].body` dẫn sang incident tổng hợp
   `xr3myzj7ms51`. Lời gọi tiếp theo sử dụng đúng ID đã quan sát.
2. Incident tổng hợp có `updates_total=9`, tool trả 3 updates và có
   `truncated=true`. Chỉ diễn giải phần nguyên nhân nhìn thấy; không khẳng định
   đã đọc toàn bộ postmortem hoặc timeline.
3. Đối chiếu timestamp, component, trạng thái và URL từng provider. Dữ liệu đã đọc
   không cung cấp bằng chứng để kết luận hai incident có chung nguyên nhân.
4. Mở `result.answer` để đối chiếu các nhận định với tool result; điểm judge cao
   không thay thế việc này.
5. Event cuối là `completed` ở step 3: agent dừng bình thường, không đồng nghĩa
   câu trả lời chắc chắn đúng tuyệt đối.

## 3. Một hạn chế và cách xử lý: E6

- Trước: step 1 lọc Actions bị timeout; step 2 bỏ `component` vẫn timeout;
  step 3 trả lời. Câu trả lời đúng ranh giới nhưng lần thử thêm không cung cấp dữ liệu.
- Mở 4 dòng mới trong `SYSTEM_PROMPT`, phần “Lỗi và ranh giới” của `agent.py`.
- Sau: một tool timeout ở step 1, câu trả lời ở step 2.
- Kết quả: điểm **100 → 100**; model calls **3 → 2**; tool calls **2 → 1**;
  token agent **4.353 → 2.872**, giảm **34,02%**.
- Đánh đổi: dừng sớm có thể bỏ lỡ phục hồi khi timeout thực sự chỉ tạm thời.
  Đây là chính sách prompt, không phải khóa cứng mọi lời gọi. Retry kết nối LLM
  vẫn là cơ chế riêng và được giới hạn.

## 4. Trình bày cả kết quả chưa thuận lợi

- Tổng điểm **100 → 99,91**; A2 **100 → 98**. Mở `grade.reason`: cần bổ sung
  rằng không chịu tác động từ incident này không loại trừ nguyên nhân cache khác.
- Toàn bộ agent: model calls **57 → 58**; token **135.526 → 147.330**.
  Chưa chứng minh giảm chi phí toàn bộ; mới quan sát được cải thiện cục bộ E6.
- E2 có một output judge thiếu trường bắt buộc và được retry. Điểm hợp lệ được
  chấp nhận ngay; không chọn lại điểm cao hơn.
- Chỉ có một lần chạy mỗi phiên bản; không khẳng định độ ổn định từ cặp kết quả này.

## 5. Tự giải thích trước khi trình bày

- Vì sao một model step có thể chứa nhiều tool calls và phải trả đủ IDs?
- Tool timeout khác outage thế nào; vì sao đổi bộ lọc không sửa lỗi kết nối?
- Vì sao incident `resolved` không chứng minh dịch vụ hiện tại vẫn bình thường?
- Vì sao URL hiện diện chưa đủ chứng minh mọi nhận định đều đúng?
- Vì sao điểm judge không tự động là điểm lab?

Đọc `CODE_WALKTHROUGH.md` để đối chiếu từng phần code. Tài liệu này hỗ trợ chuẩn
bị; học viên vẫn phải tự trình bày và trả lời coach.
