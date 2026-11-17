# Team

## Thông tin nhóm

- Tên nhóm: NhomABC
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-NhomABC-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/nguyenquoctoan0310/K5-L3B-DAY08-NhomABC-FromWorkflowsToAgents, nhánh `main`, commit code + report `c9f9295` (xem `report/team/decision_adr.md`)

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 |    Nguyễn Quốc Toàn    |   2A202604098   |   nguyenquoctoan0310@gmail.com    |     nguyenquoctoan0310   | Lead/integration; shape A `workflow`; crash suite; benchmark; ADR; ablation + research card; group report |
|   2 | Vũ Trọng Thắng | 2A202604022 |       | Thangvipsv4 | Shape B `single` (ReAct); test single; research card (góp ý) |
|   3 |        |      |       | phamhanam | Shape C `orchestrator` + handoff; rà trace/secret; group report + research card |

## Phân công

Shape nhóm chọn để chấm hidden: `workflow` (ít tự chủ nhất, tất định theo seed). Nhóm không làm bonus.

### TV1 — Lead / integration, workflow, durability

| CP | Việc | File / bằng chứng |
| --- | --- | --- |
| CP1 | Tạo repo nhóm `K5-L3A-DAY08-NhomABC-FromWorkflowsToAgents`, điền `TEAM.md` | `TEAM.md` |
| CP2 | Viết shape A trước (khuôn mẫu cho TV2, TV3), đạt 62 test student `-k workflow` | `src/lab8/shapes/workflow.py` |
| CP3 | Truyền `crash_at`, không bắt `InjectedCrash`; T11, T12 xanh | `workflow.py` |
| CP4 | Chạy crash suite `20/20`, rà approval hỏng / sai claim / đơn đã hoàn đủ | `src/reports/crash.json` |
| CP5 | Chạy benchmark 4 shape × 5 seed, tự kiểm `student_drop/`, điền ADR (commit hash, run id, số liệu), chạy `check_submission` ra `0 FAIL`, push | `src/reports/benchmark.json`, `report/team/decision_adr.md` |
| Ablation + báo cáo | Ablation `workflow_nodraft`, research card, group report | `src/bonus/ablation_workflow_nodraft.py`, `report/team/research_card.md`, `report/team/group_report.md` |
| Test | Test workflow: đơn đã hoàn một phần (kiểu T14) và đơn đã hoàn đủ (kiểu T13) | `src/tests/test_team_workflow.py` |
| Báo cáo | Mục 4 "Kết quả" của group report; báo cáo cá nhân | `report/team/group_report.md`, `report/team/<MSSV>_<HoTen>.md` |

### TV2 — Single agent

| CP | Việc | File / bằng chứng |
| --- | --- | --- |
| CP2 | Viết shape B bằng `run_react` (≤ 8 bước), `decide` chỉ chọn tool đọc, nhớ kết quả qua closure; đạt 62 test `-k single` | `src/lab8/shapes/single.py` |
| CP3 | `crash_at` + T11, T12 xanh cho single | `single.py` |
| Test | Test single: không vượt 8 bước, không tin delay trong ticket, model không quyết số tiền | `src/tests/test_team_single.py` |
| Báo cáo | Research card R2 (MAST) và R4 (confounders); mục 7 "Hạn chế"; báo cáo cá nhân | `report/team/research_card.md`, `report/team/<MSSV>_<HoTen>.md` |

### TV3 — Orchestrator, handoff, bảo mật trace, báo cáo nhóm

| CP | Việc | File / bằng chứng |
| --- | --- | --- |
| CP2 | Viết shape C: `make_handoff` với tool chỉ đọc, `run_readonly_investigators`, orchestrator quote và gọi host; đạt 62 test `-k orchestrator` | `src/lab8/shapes/orchestrator.py` |
| CP3 | Trace ghi handoff đã sanitize, không ghi parent context; T11, T12 xanh | `orchestrator.py` |
| CP4 | Rà trace cả 3 shape trong `src/traces/` và stdout: không có `CANARY_SECRET_*`, `parent_secret`, SĐT, địa chỉ, tên hàng, internal note | `src/traces/` (không commit) |
| CP5 | Viết group report, research card R1 (scaling) và R3 (AgentArch) + bảng ablation | `report/team/group_report.md`, `report/team/research_card.md` |
| Test | Test trace/kết quả của orchestrator không chứa secret, handoff chỉ có field allowlist | `src/tests/test_team_orchestrator_trace.py` |
| Báo cáo | Mục 1–3, 5, 6, 8 của group report; báo cáo cá nhân | `report/team/group_report.md`, `report/team/<MSSV>_<HoTen>.md` |

### Việc chung

- Cả nhóm: mỗi máy chạy smoke pass (CP1); `python -m pytest -q` luôn xanh trước khi push.
- Mỗi người tự commit phần của mình (shape + test) để lịch sử commit chứng minh đóng góp (C8).
- Trước 17:00 cả nhóm đọc ADR, thống nhất lý do chọn `workflow` và trả lời được: ranh giới code / model, vì sao truyền quote đầy đủ, trace cố ý không ghi field nào.
- Mỗi người tự nộp link repo nhóm trên LMS trước deadline.
- Không sửa `metrics.py`, `durability.py`, `policy.py`, `config/`, `data/`; không sửa tay JSON trong `src/reports/`.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Nguyễn Quốc Toàn (nguyenquoctoan0310) | TV1 — Lead, shape A `workflow`, crash, benchmark, ADR, ablation, research card, group report | `cc91a28` (workflow + test), `2de95d8` (crash report), `0dbd5b9` (ablation, benchmark) | `src/tests/test_team_workflow.py` |
| Vũ Trọng Thắng (Thangvipsv4) | TV2 — shape B `single` | `7df5fc0` (single) | `src/tests/test_team_single.py` (nháp do TV1 commit trong `0dbd5b9`; TV2 cần tự commit một test) |
| phamhanam | TV3 — shape C `orchestrator`, handoff, trace | `dc80197` (orchestrator), `2a7c349` (test), `3a41839` (trace/secret audit) | `src/tests/test_orchestrator_safety.py` |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## MSSV_HoTen

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-
