# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: c9f9295
- Run id dẫn chứng: R-workflow-C-014-s55, R-workflow-C-002-s55, R-swarm-C-002-s55 (src/reports/benchmark.json)
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0.000000 (public, 14 claim × 5 seed = 70 trial)
- Cost per success (mô phỏng, VND): 28.86
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0 trên bộ public (70/70 trial pass, trial_pass kiểm forbid_substrings và approval; quét src/traces/R-workflow-* không thấy CANARY_*, SĐT, địa chỉ, tên hàng)

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

Lệnh tái lập (chạy trong `src/`, commit `c9f9295`):

```text
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
python -m lab8.crash_test --count 20 --out reports/crash.json
```

| Shape | Pass | pass^5 | Variance | Seed min–max | Cost/success (VND) | Mean steps | Model calls/trial |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| workflow | 1.000 | 1.000 | 0.000000 | 1.000–1.000 | 28.86 | 5.43 | 1.0 |
| single | 1.000 | 1.000 | 0.000000 | 1.000–1.000 | 48.19 | 6.36 | 5.5 |
| orchestrator | 1.000 | 1.000 | 0.000000 | 1.000–1.000 | 56.79 | 4.64 | 1.0 |
| swarm | 0.986 | 0.929 | 0.000816 | 0.929–1.000 | 49.57 | 2.80 | 3.0 |

## Vì sao shape này

Trên cùng corpus public (14 claim), cùng 5 seed `11,22,33,44,55`, cùng bảng giá `config/pricing.yaml` và cùng evaluator `trial_pass`, ba shape nhóm viết đều đạt pass 1.000 và pass^5 1.000, còn swarm đạt 0.986 / 0.929 vì trượt C-002 ở seed 55 (tin "trễ 5 ngày" trong ticket thay vì `delay_days = 2` của order, trial `R-swarm-C-002-s55`). Khi độ đúng ngang nhau thì quyết định dựa vào chi phí và mức tự chủ: workflow có cost/success 28.86 VND, thấp hơn single 40% (48.19), orchestrator 49% (56.79) và swarm 42% (49.57). Workflow cũng là shape ít tự chủ nhất: thứ tự bước cố định trong code, model chỉ soạn câu trả lời sau khi quyết định đã chốt, nên không có đường nào để chữ trong ticket ảnh hưởng số tiền. Vì vậy nhóm chọn `workflow`.

## Có đáng đổi lấy multi-agent không

Không, với task này. Claims flow là chuỗi tuần tự (claim → order → quote → host), bước quote phụ thuộc order nên không có phần đáng kể nào chạy song song được; thêm agent chỉ thêm model call và tool call (orchestrator 5.57 tool call/trial so với 2.79 của workflow) mà không tăng pass. Ngay cả khi một shape multi-agent pass nhỉnh hơn, nhóm vẫn giữ workflow nếu chênh lệch nằm trong độ dao động giữa các seed và cost/success cao hơn. Quyết định sẽ đảo lại nếu: (1) ticket là văn bản tự do mà luật cố định không trích được dữ kiện (cần model thật đọc hiểu), (2) có nhiều nguồn độc lập cần tra song song (nhiều kho, nhiều hãng vận chuyển) để critical path giảm rõ, hoặc (3) bộ hidden cho thấy workflow fail một nhóm claim mà shape khác xử lý được, với an toàn (leak, bypass) vẫn bằng 0.

## Trace và bằng chứng

Trace workflow (`src/traces/<run_id>.json`, dùng `lab8.trace.Trace`) ghi các event: `claim` (claim_id, found, has_order_id), `lookup_order` (visible, reason, và order view chỉ gồm ORDER_FIELDS: order_id, status, delay_days, shipping_fee_vnd, paid_vnd, damage_verified, carrier), `quote` (amount_vnd, reason, clause_ids), `issue_refund` (ok, reason, conflict), `decision` (status, proposal_amount, reason), `draft`, và `crash` khi có InjectedCrash. Cố ý **không** ghi: nội dung ticket (dữ liệu người dùng, có thể chứa lệnh chèn hoặc secret), `principal_id`, `parent_secret`, `raw_headers`, claim row và order row thô (SĐT, địa chỉ, tên hàng, internal note), nội dung câu trả lời của MockLLM. Shape không in gì ra stdout và không ghi file nào khác ngoài trace. Bằng chứng: test `tests/test_team_workflow.py::test_trace_and_result_hold_no_secret_pii_or_ticket_text` chạy trên cả 14 claim public trong cổng `python -m pytest -q`. Nếu trace nằm ngoài chỗ scanner quét được thì không chứng minh được là sạch, vì vậy shape chỉ ghi đúng một file `<run_id>.json` trong thư mục trace mà grader quét.

## Giới hạn

MockLLM không phải model sản xuất: nó tất định theo seed và không đọc hiểu ngôn ngữ, nên variance 0 của workflow/single/orchestrator phản ánh code tất định, không phải độ ổn định của một LLM thật. Latency là `unavailable`; cost là VND mô phỏng, không phải hóa đơn API. Corpus public chỉ 14 claim; số trên bộ hidden 40 claim × 5 seed do giảng viên chấm và chưa có ở đây. Secret leak / approval bypass = 0 là trên bộ public. Không sửa tay JSON trong `src/reports/`.
