# CEM_Test 專案工具包

## 1) 專案定位
- 專案根目錄：`D:\Code\CEM_Test`
- 核心目標：以 `LabCEM` 進行波導/幾何生成，支援 `Label9 CLI` 與 `ATH/Tritonia-M` 參數化流程。

## 2) 啟動與入口
- 啟動 LabCEM GUI：
  - `D:\Code\CEM_Test\Run-LabCEM-GUI.bat`
- 啟動 Label9 GUI（本地 runtime）：
  - `D:\Code\CEM_Test\Launch-Label9-GUI.ps1`
- 建立桌面捷徑：
  - `D:\Code\CEM_Test\Create-Desktop-Shortcut.ps1`

## 3) 核心程式模組
- 應用入口：
  - `src/labcem/gui.py`（桌面 GUI）
  - `src/labcem/cli.py`（CLI）
  - `src/labcem/orchestrator.py`（主流程編排）
- L1 幾何與SDF：
  - `src/labcem/l1/`
  - `src/labcem/l1_geometry_kernel/`
- L2 智能規劃與波導參數：
  - `src/labcem/l2/planner.py`
  - `src/labcem/l2/requirement_parser.py`
  - `src/labcem/l2/design_optimizer.py`
  - `src/labcem/l2/ath_formula.py`
  - `src/labcem/l2/label9_adapter.py`
- L3 知識層：
  - `src/labcem/l3/knowledge.py`
  - `knowledge/domains/`

## 4) ATH/Tritonia-M 工具鏈
- 外部 ATH 工具：
  - `external/ATH-Waveguide-Designer/`
- 主要檔案：
  - `external/ATH-Waveguide-Designer/cfg_generator.py`（ATH cfg 生成）
  - `external/ATH-Waveguide-Designer/ath_runner.py`（ATH 執行器）
- 當前整合策略：
  - `LLM 解析提示詞 -> 產生 Tritonia-M 參數 -> 匯入 CEM 生成`

## 5) Label9/Codex 串接重點
- Label9 介接器：
  - `src/labcem/l2/label9_adapter.py`
- Runtime 資料夾：
  - `D:\Code\CEM_Test\Label9_runtime`
- 常見埠口（若衝突需檢查）：
  - `3000`, `3082`, `8789`

## 6) 輸入與輸出
- 輸入：
  - GUI prompt / CLI spec
  - 可附知識檔（pdf/docx/txt/json）
- 輸出：
  - `D:\Code\CEM_Test\outputs\`
  - 常見內容：`geometry.json`, `build_report.json`, `validation_report.json`, `*.stl`, `*.obj`

## 7) 常用操作
- 安裝與開發模式：
  - `cd D:\Code\CEM_Test`
  - `.\venv\Scripts\activate`
  - `python -m pip install -e .`
- CLI 快速測試：
  - `python -m labcem.cli --spec "Generate a simple cylindrical part" --domain general`

## 8) 故障排查
- 現象：CLI 狀態 unknown 或退回 fallback
  - 檢查 `Label9_runtime/logs` 與 `codex_runtime.log`
- 現象：無法啟動或偶發失敗
  - 檢查是否多開造成埠口衝突（`EADDRINUSE`）
- 現象：波導型式被覆蓋
  - 檢查 `planner.py` / `design_optimizer.py` 的 `waveguide_type` 最終值

## 9) 建議維護規範
- 新增波導公式時，至少同步修改：
  - `requirement_parser.py`（語意解析）
  - `planner.py`（參數落表）
  - `sdf_primitives.py`（實際曲線/半徑規則）
  - `orchestrator.py`（參數貫通）
  - `design_optimizer.py`（避免候選覆蓋指定模式）
