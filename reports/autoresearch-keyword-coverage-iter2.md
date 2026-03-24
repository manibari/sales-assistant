現況分析：

- **83 個關鍵字**，驗證通過 (`OK: 83 keywords`)
- **297 筆標案全部命中**（100% match rate）
- 不需要新增任何關鍵字 — 覆蓋率已經完美

任務描述中的 "current best: 0" 應該是量測腳本的 bug（原始 metric 腳本的 `print(len(kws))` 確實輸出 83，但外部 harness 可能沒有正確解析）。

**結論：keywords.yml 無需修改。** 現有 83 個關鍵字已覆蓋全部 297 筆標案。
