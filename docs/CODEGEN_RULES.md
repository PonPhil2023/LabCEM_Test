# LabCEM LLM Codegen Rules

1. LLM 只能產生 proposed code。
2. LLM 不能直接修改 `labcem/core`。
3. LLM 不能直接覆蓋正式 `components`。
4. LLM 不能修改 GUI / CLI，除非人工允許。
5. LLM 產生的 `build()` 必須透過 backend。
6. LLM 不能直接 `mesh.export()`。
7. LLM 不能直接寫 STL / OBJ。
8. LLM proposed code 必須通過 static review。
9. LLM review 不能取代 static review。
10. LLM output 必須保留 `source_id` / `generated_from`。
11. 低 confidence 的公式不得直接實作為 solver，只能列入 implementation_hints。
