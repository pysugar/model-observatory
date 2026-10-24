# 模型档案页签 · 本地验收

2026-10-24，基线 `d8ae6c3`（PR18 合并后的 main），分支 `claude/nice-euler-cj5s04`。本记录对应提交前的工作树；CI 与预览以后续 PR 检查为准，不代表正式部署。

## 结果

- 单元测试 53 项通过：原有 46 项 + `tests/test_model_profiles.py` 7 项（构建嵌入、24 款覆盖与 GPT 5.6 系列、AA 拐点与概览矩阵一致、已知拐点、证据来源标记、Grok medium 待核验不改目录、建议任务映射）。
- 完整浏览器 smoke 通过（[smoke.json](smoke.json)）：7 个页签；模型档案 24 款 × 省钱 / 均衡 / 性能优先逐行拐点与 Python 参考一致；深链 `#profiles?m=…`、快捷按钮、选档速查与档位建议的跳转；1440 / 390 / 320 无整页横向溢出；无 JS 错误或外部请求；新增 CSV 导出通过术语检查。
- `node --check report.js`、`git diff --check` 通过；`python3 build_report.py` 后生成物与源文件一致。

## 环境说明

云端容器内运行。仓库锁定的 Python Playwright 1.58.0 装在临时 venv，驱动预装的 Chrome for Testing 153.0.8010.12；容器以 root 运行，所以本地包装脚本关闭了 Chromium 沙箱，仓库脚本未改。会话网络只放行搜索，研究条目的核验方式见 [本期研究记录](../../research/2026-10-24/README.md)。

## 截图

- [桌面 · Opus 5.5](desktop-opus55.png)
- [桌面 · GPT 6.1 Sol（含 OSWorld 逐档）](desktop-gpt61sol.png)
- [桌面 · Grok 4.7（medium 待核验）](desktop-grok47.png)
- [深色 · Sonnet 5.5](dark-sonnet55.png)
- [390px · GPT 5.6 Luna](mobile-390-gpt56luna.png)
- [320px · Gemini 4 Argon（仅单点）](mobile-320-argon.png)

截图参数与溢出检查见 [screenshots.json](screenshots.json)，源文件哈希见 [validation.json](validation.json)。
