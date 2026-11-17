# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: NhomABC
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`): xem dòng `- Commit hash:` trong `report/team/decision_adr.md`

## 2. Mục tiêu và cách tiếp cận

Bài toán: xử lý claim hoàn phí vận chuyển của LogiX-VN bằng bốn kiến trúc (A workflow, B single agent, C orchestrator, D swarm có sẵn), cùng chữ ký `run_claim`, rồi chọn kiến trúc ít tự chủ nhất mà vẫn làm được việc dựa trên số đo. Nhóm coi ba điều là bất biến ở mọi shape: tiền do `compute_compensation` tính từ dòng order và policy hiện hành; chỉ host (`durability.issue_refund`) được ghi ledger; chữ trong ticket là dữ liệu người dùng, không phải lệnh hay dữ kiện để tính tiền.

Chia việc (chi tiết ở `TEAM.md`, mục Phân công):

- TV1: shape A `workflow` (viết trước để làm khuôn), crash suite, benchmark, ADR, tích hợp và nộp bài.
- TV2: shape B `single` (ReAct có giới hạn 8 bước).
- TV3: shape C `orchestrator` + handoff, rà trace/secret.
- Bonus B7 (kiểm toán grader), research card và báo cáo được làm sau khi ba shape đã merge.

Thứ tự: đọc contract và `swarm_reference.py` (CP1) → ba shape làm song song trên ba nhánh riêng, mỗi shape tự qua 62 test student (CP2–CP3) → merge vào `main`, chạy crash suite, benchmark 4 shape × 5 seed (CP4–CP5) → ADR, research card, bonus.

## 3. Giải pháp

Ranh giới code / model chung cho cả ba shape: model (MockLLM) chỉ chọn tool đọc (shape B) hoặc soạn chữ; không shape nào để model quyết số tiền hay gọi tool ghi. Shape luôn truyền **quote đầy đủ** vào `issue_refund`; host tự kiểm approval của chính claim, trừ phần đã hoàn của cùng đơn (T13, T14) và chống ghi trùng bằng khóa `refund:{claim_id}`. Shape truyền `crash_at` cho host và không nuốt `InjectedCrash` (ghi trace rồi raise lại). Mọi nhánh return đi qua `lab8.shapes.common.finish()`.

| Shape | Đọc gì | Quyết định gì | Gọi host |
| --- | --- | --- | --- |
| A `workflow` (`src/lab8/shapes/workflow.py`) | `get_claim_view` → `lookup_order` (theo principal) → `compute_compensation` | Các bước cố định trong Python: không có claim → `failed`; thiếu `order_id` → `needs_info`; không thấy đơn → `escalated`; quote 0 → `denied` không gọi host | Quote > 0 → `issue_refund(full quote)`; host từ chối → `denied` (proposal = quote), conflict → `failed`, chấp nhận → `resolved`. MockLLM chỉ soạn một câu trả lời sau khi quyết định đã chốt |
| B `single` (`src/lab8/shapes/single.py`) | Vòng `run_react(max_steps=8)`; `decide` chọn lần lượt `get_claim_view`, `lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation` | `decide` giữ kết quả các bước trước trong state (vì `run_react` chỉ trả lại kết quả tool cuối); prompt cho MockLLM không chứa ticket hay dữ liệu riêng | Sau vòng lặp, code của shape (không phải model) gọi `issue_refund` với quote đầy đủ |
| C `orchestrator` (`src/lab8/shapes/orchestrator.py`) | Handoff `make_handoff(facts={}, allowed_tools=[get_claim_view, lookup_order, lookup_policy, lookup_refund_history])`; `run_readonly_investigators` chạy tool với `worker=True` | Orchestrator tự quote từ order view của investigator | Orchestrator là writer duy nhất; investigator không có tool ghi |

Handoff được sanitize bằng allowlist của `lab8.handoff` (không bằng tóm tắt LLM): `facts` để trống, không mang `parent_secret`, header hay claim row. Trace orchestrator ghi `handoff_sanitized` và bản handoff đã sanitize, không ghi parent context.

Trace (`lab8.trace.Trace`, file `src/traces/<run_id>.json`): workflow ghi `claim` (claim_id, found, has_order_id), `lookup_order` (chỉ ORDER_FIELDS), `quote`, `issue_refund` (ok, reason, conflict), `decision`, `draft`, `crash`. Cố ý không ghi: nội dung ticket, `principal_id`, `parent_secret`, `raw_headers`, SĐT, địa chỉ, tên hàng, internal note, chữ MockLLM sinh ra. Không shape nào in ra stdout.

Test nhóm thêm (chạy trong cổng `python -m pytest -q`): `tests/test_team_workflow.py` (T13/T14, approval của claim khác, crash–resume qua shape, seed-invariance, quét secret/PII/ticket trên cả 14 claim), `tests/test_orchestrator_safety.py` (allowlist handoff, worker không gọi được tool ghi, trace orchestrator đúng contract và sạch), `tests/test_bonus_grader_audit.py` (B7).

## 4. Kết quả

Bộ public, 14 claim × seed `11,22,33,44,55` (70 trial mỗi shape), từ `src/reports/benchmark.json`:

| Shape | Pass | pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean steps | p95 steps | Tool calls/trial | Model calls/trial |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| workflow | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 28.86 | 5.43 | 6 | 2.79 | 1.0 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 48.19 | 6.36 | 7 | 4.50 | 5.5 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 56.79 | 4.64 | 5 | 5.57 | 1.0 |
| swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 | 3 | 4.66 | 3.0 |

- Swarm trượt đúng một trial: C-002 seed 55 (`status resolved != denied`), vì tin "trễ 5 ngày" trong ticket thay cho `delay_days = 2` của order.
- Crash safety: `20/20` (`src/reports/crash.json`). T11 (gọi lại) và T12 (crash rồi resume) xanh trên cả ba shape nhóm viết; ma trận student 248 passed.
- Quét toàn bộ trace của 4 shape trong `src/traces/` không thấy `CANARY_SECRET_*`, `CANARY_INTERNAL_*`, SĐT, địa chỉ hay tên hàng.
- Ablation (research card): bỏ bước MockLLM draft của workflow giữ pass 1.000, cost/success 28.86 → 27.86 (`src/reports/bonus_ablation_nodraft.json`).
- Tự kiểm trên `student_drop/`: chưa chạy vì nhóm chưa nhận thư mục này (lệnh ở `src/README.md`, mục Tự kiểm trên bộ hidden).

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

- **`run_react` không giữ lịch sử quan sát.** Sau mỗi tool, observation chỉ còn `last_tool`/`last_result`, nên `decide` ngây thơ sẽ quên order đã đọc. Shape B lưu kết quả từng tool vào một dict `state` trong closure.
- **Mạng chập chờn khi tích hợp.** `git pull` báo `Failed to connect to github.com port 443`; nhóm dùng bản `origin/main` đã `git fetch` trước đó và `git merge --ff-only origin/main`, sau đó chạy lại toàn bộ test và benchmark trên `main`.
- **Thứ tự commit hash.** `check_submission` cảnh báo khi còn thay đổi chưa commit; nhóm commit `src/reports/` trước, lấy `git rev-parse --short HEAD` rồi mới ghi hash vào ADR.
- **Checker chưa nhận B7.** `lab8.check_submission` chỉ chấp nhận tiêu đề `Bonus report: B1`–`B6`, trong khi `docs/bonus_topics.md` có B7. Nhóm giữ tiêu đề đúng là B7 và báo giảng viên thay vì đổi nhãn cho qua checker.
- **Lỗi thước đo phát hiện khi làm B7.** `lab8.metrics.summarize` tính pass^5 theo số dòng mỗi claim chứ không theo số seed phân biệt, nên một trial bị ghi hai lần làm pass^5 rơi về 0. Không ảnh hưởng benchmark của nhóm (đúng 1 trial mỗi claim × seed); nhóm không sửa `metrics.py` vì đó là file thước đo, chỉ ghi lại trong `report/team/bonus_report.md`.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Ngoài ra:

- Variance 0 của ba shape nhóm viết đến từ code tất định, không chứng minh độ ổn định của một LLM thật; với model thật, shape B và C có thể dao động theo seed như swarm.
- Corpus public chỉ 14 claim. Kết quả trên 40 claim hidden do giảng viên chấm; nhóm chưa có số đó.
- Chi phí là VND mô phỏng, chủ yếu đến từ tool call (10 VND/lần), nên thứ hạng cost/success nhạy với bảng giá: nếu tool call rẻ hơn nhiều so với token, khoảng cách giữa workflow và orchestrator sẽ thu hẹp.
- Kết luận "workflow đủ tốt" sẽ đổi nếu ticket là văn bản tự do mà luật cố định không trích được dữ kiện, nếu cần tra nhiều nguồn độc lập song song, hoặc nếu hidden cho thấy workflow fail một nhóm claim mà shape khác xử lý được với leak/bypass vẫn bằng 0.
- Hướng cải thiện: chạy B1 (investigator song song + mô hình latency) để đo critical path thay vì chỉ cost; thêm claim đối kháng tự viết nhãn tay.

## 8. Tài liệu tham khảo

- Google Research 2026, *Towards a Science of Scaling Agent Systems* (bài N8, slide 15, 24, 33, 41).
- *Rethinking Evaluation of MAS Efficiency*, EMNLP 2026 (slide 44, 59).
- MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* (slide 35, 45).
- AgentArch, AACL 2026 (slide 43).
- Tài liệu repo: `docs/business_rules.md`, `docs/contracts.md`, `docs/architecture.md`, `docs/metrics.md`, `docs/bonus_topics.md`.
