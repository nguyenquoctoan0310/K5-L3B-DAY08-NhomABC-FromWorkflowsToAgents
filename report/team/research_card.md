# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R1 · Scaling |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Google Research 2026, *Towards a Science of Scaling Agent Systems* (bài N8, slide 15, 24, 33, 41; URL trong thư viện tham khảo slide 68–69). Loại bằng chứng: benchmark có kiểm soát trên nhiều kiến trúc agent |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Multi-agent chỉ có lợi khi task chia song song được; với task tuần tự, các biến thể multi-agent trong nghiên cứu giảm hiệu năng 39–70% |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | LLM thật, các task benchmark của nghiên cứu, đo hiệu năng và chi phí ở quy mô của họ. Không nói gì về task có cổng ghi tiền do host kiểm như LogiX, và không dùng model tất định như MockLLM |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Claims flow là chuỗi tuần tự (claim → order → quote → host, quote phụ thuộc order). Đổi A `workflow` → C `orchestrator` (thêm lớp investigator) sẽ không tăng pass rate (giữ 1.000 trên public) nhưng tăng cost/success khoảng +50–100% vì thêm tool call qua handoff |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Cố định: MockLLM, bộ tool `lab8.tools`, seed 11,22,33,44,55, corpus `data/public_claims.jsonl` (14 claim), giá `config/pricing.yaml`, evaluator `lab8.metrics.trial_pass`, SQLite mới mỗi trial. Biến duy nhất thay đổi: topology (có/không lớp investigator chỉ đọc). Ablation phụ: tắt bước MockLLM draft của workflow |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: lớp investigator thêm tool call mà không thêm thông tin (order view giống hệt), làm cost/success tăng; nếu handoff làm rơi field thì pass rate giảm. Đo bằng pass rate, pass^5, seed variance, cost/success, mean tool calls; leak và bypass phải bằng 0 |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn):
  - `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
  - `python -m lab8.benchmark --shapes workflow,workflow_nodraft --extra-shape workflow_nodraft=bonus.ablation_workflow_nodraft:run_claim --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/bonus_ablation_nodraft.json`
- Run id / file report: `src/reports/benchmark.json` (ví dụ `R-workflow-C-014-s55`, `R-orchestrator-C-014-s55`); `src/reports/bonus_ablation_nodraft.json` (ví dụ `R-workflow_nodraft-C-014-s55`).
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: **Đúng.** A → C: pass rate 1.000 → 1.000, pass^5 1.000 → 1.000, variance 0 → 0, nhưng cost/success 28.86 → 56.79 VND (+96.8%) và mean tool calls 2.79 → 5.57 (gấp đôi); số model call bằng nhau (1.0). Lớp investigator không thêm thông tin vì nó đọc đúng order view mà workflow tự đọc. Ablation phụ (tắt draft): pass giữ 1.000, cost/success 28.86 → 27.86 (−3.5%), mean steps 5.43 → 4.43: bước draft chỉ là chữ cho khách, không ảnh hưởng quyết định, và chi phí chủ yếu đến từ tool call chứ không từ model call. Không kết luận được phần "giảm 39–70%" của nguồn: trên LogiX pass không giảm vì tiền do code tính và host chặn mọi ghi sai, nên topology chỉ làm đổi chi phí.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`. Corpus public chỉ 14 claim; variance 0 phản ánh code tất định chứ không phải độ ổn định của LLM thật. Với model thật đọc ticket tự do, investigator có thể thêm giá trị (hoặc thêm lỗi) mà ablation này không đo được.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
