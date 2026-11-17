# Báo cáo cá nhân — 2A202604098_NguyenQuocToan

## 1. Thông tin thành viên

- Họ tên: Nguyễn Quốc Toàn
- MSSV: 2A202604098
- Email: nguyenquoctoan0310@gmail.com
- GitHub: nguyenquoctoan0310

## 2. Phần việc phụ trách

- TV1 — lead / integration: tạo repo nhóm, chia việc (`TEAM.md`), merge các nhánh, chạy kiểm tra cuối và nộp bài.
- Shape A `workflow` (`src/lab8/shapes/workflow.py`) — shape nhóm chọn để chấm hidden.
- Durability và đo đạc: crash suite, benchmark 4 shape × 5 seed, `report/team/decision_adr.md`.
- bonus B7 (`src/bonus/`, `report/team/bonus_report.md`), ablation và research card, group report.

## 3. Đóng góp cụ thể

- `cc91a28`: shape workflow và `src/tests/test_team_workflow.py`.
- `2de95d8`: `src/reports/crash.json`.
- Các commit sau khi merge (xem `git log`): benchmark chính thức, ADR, research card, group report, bonus B7, ablation `workflow_nodraft`.
- Quyết định kỹ thuật:
  - Workflow không đọc ticket để lấy số và không ghi ticket vào trace; trace chỉ ghi view đã qua allowlist (ORDER_FIELDS), quote và kết quả host.
  - Truyền quote đầy đủ vào `issue_refund`; `proposal_amount` luôn là quote, không phải số đã ghi.
  - Gặp `InjectedCrash` thì ghi trace rồi raise lại, không nuốt.
  - MockLLM chỉ được gọi một lần để soạn chữ, sau khi quyết định đã chốt.
  - Chọn `workflow` trong ADR vì pass ngang các shape khác (1.000) với cost/success thấp nhất (28.86 VND) và mức tự chủ thấp nhất.
  - B7: đánh dấu các ô lệch bằng `xfail(strict=True)` để test luôn xanh mà phát hiện vẫn hiện trong output; thêm quan hệ mới R4 (hoán vị).

## 4. Bằng chứng

- Test: `src/tests/test_team_workflow.py` (25 test), `src/tests/test_bonus_grader_audit.py` (15 passed, 5 xfail strict).
- Report: `src/reports/benchmark.json`, `src/reports/crash.json` (`20/20`), `src/reports/bonus_grader_audit.json` (run id `B7-grader-audit-5fd46fdca677`), `src/reports/bonus_ablation_nodraft.json`.
- Run id dẫn chứng: `R-workflow-C-014-s55` (T14, ledger 120000 với proposal 150000), `R-workflow-C-002-s55` (ticket nói trễ 5 ngày, vẫn `denied`), `R-swarm-C-002-s55` (swarm trượt cùng claim).

## 5. Công cụ AI đã dùng

- Claude Code (trong VS Code): đọc đề và code starter, gợi ý chia việc, viết nháp `workflow.py`, test, script B7 và các báo cáo.
- Cách tự kiểm tra:
  - Chạy `python -m pytest -q` (cổng host) và `python -m pytest -q -m student -o addopts=` sau mỗi thay đổi.
  - Chạy `python -m lab8.crash_test` và `python -m lab8.benchmark`, rồi đối chiếu mọi con số trong ADR và báo cáo với file JSON trong `src/reports/`.
  - Mở trace mẫu để xem trace ghi những field nào.
  - Quét `src/traces/` tìm `CANARY_*`, SĐT, địa chỉ.
  - Với B7, so tay output của ba grader trên từng fixture.
  - Chạy `python -m lab8.check_submission`.

## 6. Tự đánh giá

(Tự viết.)
