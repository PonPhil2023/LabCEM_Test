# LabCEM

LabCEM 保留 Core + Kernel 架構與既有 GUI/CLI，並新增 LLM Agent/Codegen 流程（支援 Labelnine/OpenAI-compatible）。

## LLM Agent / Codegen

新增 `src/labcem/agents/llm/`：
- `llm_config.py`, `llm_client.py`
- `llm_knowledge_agent.py`, `llm_schema_agent.py`, `llm_codegen_agent.py`, `llm_review_agent.py`
- `llm_agent_pipeline.py`

輸出遵循安全限制：僅寫入 `generated/proposed_*` 與 `*_schema.llm.json`。

## Rules / LLM / Hybrid Agent Mode

- `rules`: 只跑規則式 agent。
- `llm`: 只跑 LLM agent（仍會保留 static review）。
- `hybrid`: 先 rules 再 llm，保留兩者輸出；LLM 不可用時自動降級 rules。

## 設定 LLM API Key

可使用系統環境變數或 `.env`（若有安裝 `python-dotenv` 會自動讀）。

`.env` 參考：
- `LABCEM_LLM_ENABLED=true`
- `LABCEM_LLM_PROVIDER=openai`
- `LABCEM_LLM_MODEL=gpt-5.5-thinking`
- `LABCEM_LLM_API_KEY=...`
- `LABCEM_LLM_BASE_URL=`

Labelnine 可用 OpenAI-compatible 方式接入（設定 `LABCEM_LLM_BASE_URL` 指向 Labelnine gateway，provider 可用 `local_openai_compatible` 或 `labelnine` alias）。

## .env.example

專案提供 [`.env.example`](D:/Code/CEM_Test/.env.example)。

## CLI LLM 使用方式

```powershell
# 檢查 LLM 狀態
python -m labcem.cli agent llm-status

# 規則式
python -m labcem.cli ingest extract --kernel acoustic_kernel --source-id waveguide_design --component waveguide --agent-mode rules

# LLM
python -m labcem.cli ingest extract --kernel acoustic_kernel --source-id waveguide_design --component waveguide --agent-mode llm

# Hybrid
python -m labcem.cli ingest extract --kernel acoustic_kernel --source-id waveguide_design --component waveguide --agent-mode hybrid

# LLM schema
python -m labcem.cli kernel schema --kernel acoustic_kernel --component waveguide --agent-mode llm

# LLM proposed code
python -m labcem.cli agent propose-code --kernel acoustic_kernel --component waveguide --agent-mode llm

# LLM review
python -m labcem.cli agent review --kernel acoustic_kernel --component waveguide --agent-mode llm
```

## GUI LLM 使用方式

GUI Knowledge 區可設定：
- Agent Mode: `rules` / `llm` / `hybrid`
- LLM 狀態顯示（Enabled/Disabled, provider/model, API key found/missing）
- 「檢查 LLM 狀態」按鈕

若選 `llm` 但未啟用，GUI 會提示並不會 crash。

## 安全限制

- LLM 不可直接修改 `labcem/core`
- 不可覆蓋正式 component
- 不可直接輸出 STL/OBJ
- `build()` 必須透過 backend
- LLM review 不能取代 static review

## Generated Proposed Code 流程

1. ingest/add + extract
2. schema (`.json` / `.llm.json`)
3. propose-code (`generated/proposed_*`)
4. static review + llm review

## static review + llm review 差異

- static review：規則檢查、必跑、具阻擋效果
- llm review：語義與風險建議、不可取代 static review

## 不啟用 LLM 時 fallback

- `llm` mode 會回傳明確錯誤訊息
- `hybrid` mode 自動降級為 rules
- 既有 `run`/GUI/outputs/latest_run 不受影響
