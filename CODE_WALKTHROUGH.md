# Hướng dẫn đọc code và phần cải tiến

> **Cập nhật 12/11/2026:** tài liệu có các vị trí dòng và trạng thái Git ở thời
> điểm trước bổ sung UI. Người học hiện đã yêu cầu commit/push. Chỉ xem diff CP4
> bằng `git diff --no-index -- artifacts/baseline/agent.py artifacts/evaluated_agent.py`.
> Report trước hiện không khớp baseline lịch sử; xem [REPORT_PROVENANCE.md](REPORT_PROVENANCE.md).

## 1. Đọc theo thứ tự nào

1. `run.py`: xem cách chương trình tạo provider, chọn bộ tools và gọi `run_agent`.
2. `status_tools.py`: đọc schemas và hai hàm `get_status`, `get_incident_details`.
3. `providers.py`: hiểu interface `complete(messages, schemas)` trả về gì.
4. `agent.py`: đọc vòng điều phối theo bảng dưới đây.
5. `eval_before.json`, `eval_after.json`: đối chiếu hành vi thực tế.
6. `NOTES.md`, `DEMO.md`: hiểu thay đổi, kết quả và cách trình bày.

Phần repo cung cấp sẵn là provider adapter, status tools, fixtures và bộ eval.
Phần triển khai chính là vòng lặp trong `agent.py`. Không dùng framework agent.

## 2. Các đoạn trong agent.py

Số dòng áp dụng cho phiên bản hiện tại; có thể tìm theo tên biến/hàm nếu sau này sửa file.

| Vị trí bắt đầu | Đoạn code | Vai trò |
|---|---|---|
| Dòng 9 | `_connection_failure` | Phân biệt lỗi kết nối LLM có thể thử lại với lỗi HTTP không tự retry. |
| Dòng 19 | `SYSTEM_PROMPT` | Quy định cách điều tra, dẫn nguồn, giới hạn bằng chứng và xử lý dữ liệu độc hại. |
| Dòng 59 | Chính sách `TimeoutError` của tool | Phần cải tiến CP4: không đổi/bỏ bộ lọc để chữa lỗi kết nối. |
| Dòng 71 | `run_agent` | Nhận câu hỏi, provider, tools và budget; trả status, answer, trace, usage. |
| Dòng 85 | `messages` | Tạo context ban đầu gồm system prompt và câu hỏi người dùng. |
| Dòng 89 | `schemas` | Mô tả tools cho LLM; ưu tiên schemas của bộ tools nếu có. |
| Dòng 92 | `for step` | Mỗi lần gọi model tiêu thụ một step; giới hạn vòng lặp bằng `max_steps`. |
| Dòng 94 | `provider.complete` | LLM trả assistant message, danh sách calls, finish và usage. |
| Dòng 105 | Lưu assistant message | Giữ nguyên message trước khi đưa các tool results vào context. |
| Dòng 113 | Retry lỗi kết nối LLM | Tối đa hai lần trong cả run; mỗi lần vẫn tiêu thụ một step. |
| Dòng 128 | Xử lý `calls` | Duyệt mọi call trong response, không chỉ call đầu tiên. |
| Dòng 133 | `json.loads` | Chuyển arguments JSON string thành dict; JSON sai trở thành observation lỗi. |
| Dòng 141 | `tools.execute` | Python thực thi tool được chọn; lỗi trở thành kết quả để model quan sát. |
| Dòng 152 | Thêm tool result | Gắn đúng `tool_call_id`, serialize kết quả vào `content`. |
| Dòng 164 | `validation_missing_source` | Khi đã đọc incident thành công mà thiếu URL, yêu cầu sửa trong cùng budget. |
| Dòng 172 | `completed` | Trả câu trả lời text hoàn chỉnh sau khi qua kiểm tra nguồn. |
| Dòng 175 | `max_steps` | Hết lượt mà chưa hoàn tất thì trả trạng thái giới hạn. |

## 3. Hiểu một vòng lặp

Ví dụ minh họa cấu trúc, không phải trace được dùng để chấm:

```text
Step 1: LLM yêu cầu get_status(provider="github", component="Actions")
        Python gọi tool, đưa kết quả vào messages với đúng tool_call_id.
Step 2: LLM đọc kết quả và yêu cầu get_incident_details với ID đã thấy.
        Python gọi tool, đưa chi tiết incident vào messages.
Step 3: LLM trả câu trả lời, finish="stop", không còn calls.
        Agent kiểm tra nguồn rồi trả completed.
```

Model chọn tool và arguments. Python quyết định cách thực thi, ghi trace và kiểm
soát giới hạn. Tool không tự gọi LLM; LLM không trực tiếp chạy hàm Python.

Một response có thể yêu cầu hai tools: vẫn là một model step nhưng có hai tool
events. Cả hai kết quả phải trở lại context trước lần gọi LLM tiếp theo.

## 4. Phân biệt hai loại timeout

| Tình huống | Ai gặp lỗi | Xử lý hiện tại |
|---|---|---|
| Lỗi kết nối đến Gemini/LLM | `provider.complete` | Retry có giới hạn, ghi `model_retry`, vẫn tính vào `max_steps`. |
| Tool không lấy được status | `tools.execute` trả `TimeoutError` | Đưa observation cho LLM; prompt hướng dẫn báo thiếu dữ liệu và tránh thử lại không có căn cứ. |

CP4 chỉ sửa dòng hướng dẫn cho tình huống thứ hai. Không thay thuật toán retry
kết nối LLM, không tạo thêm tools, không thay kiến trúc toàn bộ.

Đây là chính sách prompt nên hành vi phụ thuộc LLM. Không có đoạn Python khóa
cứng mọi lời gọi tool sau timeout. Trong lượt E6 sau cải tiến, model đã làm theo.

## 5. Phần thay đổi CP4 so với phần làm từ đầu

Repo Git hiện chưa có commit cho bài làm này, nên có hai mốc so sánh:

```powershell
# Toàn bộ thay đổi agent so với bản starter trong Git:
git diff -- agent.py

# Chỉ thay đổi CP4 so với baseline đã đạt 100:
git diff --no-index -- artifacts/baseline/agent.py agent.py
```

Lệnh `--no-index` trả exit code 1 khi tìm thấy khác biệt; đây là cách Git báo có
diff, không phải test thất bại. Hai lệnh trên chỉ đọc, không stage hoặc commit.

Diff CP4 giữa hai bản source lưu trong artifacts chỉ có 4 dòng bổ sung trong
system prompt. Code UI hiện tại có thêm thay đổi sau eval. Bản baseline source
vẫn ở `artifacts/baseline/agent.py`; report baseline gốc hiện chưa tìm lại được.

## 6. Cách đọc bằng chứng và kết quả

- Mở case E6 trước/sau: so sánh `result.trace`, `result.usage`, `result.answer`
  và `grade.reason`; đừng chỉ nhìn điểm 100.
- Trước: hai tool calls đều timeout; sau: một tool call timeout rồi model trả lời.
- E6 tiết kiệm 1.481 token trong cặp lượt chạy này. Toàn bộ bộ eval lại tăng
  11.804 token: không kết luận tối ưu toàn hệ thống.
- A2 giảm 2 điểm vì thiếu lưu ý về các nguyên nhân cache khác. Không tự quy mức
  giảm đó cho chính sách timeout; mỗi phiên bản mới chạy một lần.
- `usage` ghi token do provider trả. Request lỗi có thể không có usage; token
  không tự chuyển thành chi phí tiền khi chưa có giá và billing.

Unit tests dùng fake provider để kiểm tra hợp đồng kỹ thuật. Eval gọi model
thật và judge để đánh giá hành vi; tests pass không chứng minh mọi câu trả lời đúng.

## 7. Những điều cần tự giải thích được

1. Tại sao phải append nguyên assistant message trước tool result?
   Vì message đó chứa tool calls và ID mà các tool results phải tham chiếu.
2. `completed` có bảo đảm đúng không?
   Không; nó chỉ xác nhận đã dừng bình thường và qua các kiểm tra được triển khai.
3. Kiểm tra nguồn hiện tại bảo đảm đến đâu?
   Nó yêu cầu có ít nhất một URL incident đã quan sát nếu đã lấy incident thành
   công; không kiểm chứng mọi claim hoặc bảo đảm đủ nguồn cho mọi provider.
4. Tại sao không cố sửa để điểm lần hai cao hơn 100?
   Mục tiêu CP4 là cải tiến có bằng chứng. Phân tích cả mặt đạt và chưa đạt quan
   trọng hơn chọn lại một lần chạy có điểm thuận lợi.
5. Bonus nằm ở đâu?
   `bonus/` cung cấp bộ tools và cases riêng. Bài chính hiện tại chưa thực hiện
   vòng mở rộng và đánh giá bonus.

## 8. Trạng thái làm việc

Các thay đổi vẫn chưa commit/push theo yêu cầu người học. Repo GitHub đã đổi
thành `DAY04`, remote tại máy đã cập nhật; tên thư mục workspace vẫn giữ nguyên.
Có thể đọc, sửa và thảo luận code trước khi quyết định cập nhật GitHub.
Tài liệu này hỗ trợ học; người học vẫn cần tự giải thích code khi demo CP6.
