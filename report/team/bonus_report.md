# Bonus report: B7

- Topic + nguồn (tên, năm, slide): B7 · Kiểm toán grader — *Rethinking Evaluation of MAS Efficiency*, EMNLP 2026, slide 44, 59.
- CLAIM của nguồn (1 câu): kết luận về hiệu năng của hệ multi-agent có thể đến từ cách đo chứ không từ kiến trúc; thước đo sai thì mọi so sánh shape sai theo, kể cả khi shape đúng.
- BOUNDARY (model / dataset / setup): nguồn đo trên benchmark MAS dùng LLM thật và các chỉ số hiệu năng/chi phí của họ; ở LogiX chỉ có 3 bản `summarize` do giảng viên cấp, 3 fixture metamorphic nhỏ (12–24 trial, 1 shape `workflow`, 6–8 claim, 2 seed) và MockLLM.
- HYPOTHESIS trên LogiX: ít nhất một trong ba bản `summarize` vi phạm một quan hệ metamorphic mà không test hiện có nào kêu; nếu dùng bản đó để chấm, pass rate hoặc cost/success của shape sẽ lệch dù shape không đổi.
- Biến cố định / biến thay đổi: cố định fixture (`grader_audit/fixtures/*.json`, sha256 `5fd46fdca677`), `lab8.compensation.quote`, `lab8.metrics`; biến thay đổi duy nhất là phép biến đổi input (thêm trial hạ tầng, nhân đôi danh sách, hoán vị thứ tự) và bản grader.
- Lệnh tái lập (copy-paste được, chạy trong `src/`):

  ```text
  python -m pytest -q tests/test_bonus_grader_audit.py -rxX
  python -m bonus.grader_audit --out reports/bonus_grader_audit.json
  ```

- File report + run id: `src/reports/bonus_grader_audit.json`, run id `B7-grader-audit-5fd46fdca677`. Code: `src/bonus/grader_audit.py`. Test: `src/tests/test_bonus_grader_audit.py` (15 passed, 5 xfail strict).

## Kết quả

Bảng bản × quan hệ, lấy từ `summary` trong `reports/bonus_grader_audit.json` (số lệch lấy từ `matrix.*.deviations`):

| Quan hệ | grader_a | grader_b | grader_c |
| --- | --- | --- | --- |
| R1 delay 2 → 3 ngày (quyết định lật đúng luật) | đạt | đạt | đạt |
| R2 thêm trial `infra_error` (metric đã chấm không đổi) | đạt | đạt | **lệch ×12**: pass_rate 0.75 → 0.5625, pass_5 0.667 → 0.5, graded_trials 12 → 16 |
| R3 nhân đôi danh sách (tỉ lệ giữ, tổng ×2) | **lệch ×3**: total cost 473.0 ≠ 2×283.5, cost/success 31.5 → 26.28, pass_5 0.667 → 0 | lệch ×1: pass_5 0.667 → 0 | lệch ×1: pass_5 0.667 → 0 |
| R4 hoán vị thứ tự trial (mới, của nhóm) | **lệch ×8**: đảo ngược → total 283.5 → 285.0, cost/success 31.5 → 31.67 | đạt | đạt |

Gọi tên lỗi theo hành vi:

- **grader_c — đếm trial hạ tầng vào mẫu số như quyết định sai.** Nó gán `passed=False` cho trial `infra_error`, nên 4 trial timeout/crash hạ tầng kéo pass rate từ 0.75 xuống 0.5625. Quan hệ R2 đáng ra phải đúng vì trial hạ tầng không phải quyết định của shape.
- **grader_a — cộng thêm chi phí của trial đầu tiên mỗi claim (đếm chi phí hai lần).** Trên fixture infra, total cost 283.5 so với 189.5 của grader_b (+94). Vì khoản cộng thêm tính một lần mỗi claim chứ không theo trial, nhân đôi danh sách không nhân đôi nó (R3 lệch), và vì lấy *trial đầu tiên gặp*, chỉ đổi thứ tự trial cũng đổi chi phí (R4 lệch).
- **Cả ba (lỗi chung của `lab8.metrics.summarize`) — pass^5 đếm số dòng mỗi claim thay vì số seed phân biệt.** Điều kiện `len(claim_rows) == len(seeds)` sai khi một (claim, seed) bị ghi hai lần, nên pass_5 rơi về 0 dù không trial nào đổi kết quả. Test `test_r3_pass5_defect_lives_in_official_metrics` chứng minh lỗi nằm ở bản chính thức. Benchmark của nhóm không bị ảnh hưởng (đúng 1 trial mỗi claim × seed, `isolation: fresh_sqlite_per_trial`), và nhóm không sửa `metrics.py` vì đó là file thước đo.
- **grader_b** đạt R1, R2, R4; chỉ lệch R3 ở pass_5 do lỗi chung ở trên. Đây là bản đúng nhất trong ba.

Quan hệ mới R4 (hoán vị): danh sách trial là một multiset, nên mọi thứ tự phải cho cùng báo cáo. R4 bắt lỗi *phụ thuộc thứ tự* mà R2, R3 không bắt được: test `test_r4_catches_an_order_bug_that_r2_and_r3_miss` dựng một mutant (seed_min lấy theo seed xuất hiện đầu tiên) qua sạch R2 và R3 (trừ lỗi pass_5 chung) nhưng R4 phát hiện ngay. R4 đã chạy trên cả ba bản.

## Kết luận

**Ủng hộ** hypothesis: hai trên ba bản grader làm lệch số mà không có test nào kêu (smoke test chỉ kiểm import và kiểu `dict`). Với grader_c, một shape có nhiều trial timeout sẽ trông tệ hơn thực tế; với grader_a, shape có chi phí trial đầu cao bị phạt cost/success và kết quả còn phụ thuộc thứ tự chạy. Nếu chấm bằng một trong hai bản này, quyết định kiến trúc trong ADR có thể đổi mà shape không đổi.

Quan hệ metamorphic hữu ích vì không cần đáp án tuyệt đối cho pass rate hay chi phí: chỉ cần biết output phải đổi (hoặc không đổi) thế nào khi input đổi. Một lỗi thước đo vẫn có thể lọt qua mọi quan hệ nhóm đã viết, ví dụ một hằng số sai trong bảng giá (cost nhân hệ số k) làm mọi shape lệch cùng tỉ lệ: các quan hệ bất biến không bắt được, cần thêm quan hệ "đổi giá ×k thì cost ×k, pass không đổi" và một ca có số tính tay.

Kết luận đảo ngược nếu: fixture được chọn sao cho các trial của một claim có cùng chi phí (R4 không còn thấy grader_a), không có trial hạ tầng (grader_c trùng grader_b), hoặc grader dedupe (claim, seed) trước khi tính (khi đó R3 không áp dụng cho pass_5 theo cách đã viết).

## Giới hạn

MockLLM nên chi phí là VND mô phỏng, không có latency. Fixture rất nhỏ (1 shape, 6–8 claim, 2 seed) và do giảng viên cấp; nhóm không tự sinh nhãn bằng `compensation.quote` (R1 chỉ dùng `quote` làm đối tượng bị kiểm, không làm nhãn). Bonus chỉ tính khi shape chọn (`workflow`) qua 3 must-pass và đạt hidden ≥ 0.80; số hidden do giảng viên chấm, nhóm chưa có. Bản `check_submission` trong starter chỉ nhận tiêu đề `B1`–`B6`, trong khi `docs/bonus_topics.md` có B7.
