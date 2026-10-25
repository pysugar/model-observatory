# 模型观测站改版 · 本地验收

研究核验日 2026-10-23；浏览器验收完成于台北时间 2026-10-24。基线 `f34421104d89d517a44be685a1338ec8845365cb`，分支 `feat/observatory-refresh-2026-10-23`。本记录对应提交前的本地工作树，保留当时的状态和源文件哈希；后续 CI 与独立预览以 PR 检查及机器人评论为准。本记录不证明正式部署或独立复核。

## 结果

- 单元测试 46 项通过，覆盖原始记录保真、数据对应、缺失值、导出、价格阈值、既有选档规则与发布产物边界。
- `scripts/publish.py build` / `check` 通过；169 条原基准、24 款目录模型、50 条来源，最新选录另存 87 条。`report-data.csv` 保持原记录。
- Chrome 156.0.8078.48 完整 smoke 通过，覆盖桌面 1440、手机 390 / 320，以及键盘和真实触屏输入模拟。所有六个维度无整页横向溢出，没有 JavaScript 错误或页面外部网络请求。
- 新增检查覆盖五站切换、搜索、空状态、厂商筛选、费用排序、展开、来源日期与核验日期分离、CSV 原始精度和缺失值、主题持久化；Grok 阶梯边界覆盖 199999 / 200000 / 200001。
- 原有逐档曲线、选档矩阵、缺档和单点、模型聚焦、Computer Use 协议、28 条任务建议、预算及导出检查继续通过。
- `node --check report.js`、`git diff --check` 通过。构建以本地 dirty 标记保存，未执行生产 headers / 部署后 probe。

机器结果见 [smoke.json](smoke.json)，源文件与生成物的 SHA256 见 [validation.json](validation.json)。截图经人工查看；手机最新榜单采用卡片显示，使模型、成绩和费用直接可见。

## 截图

- [桌面首页](desktop.png)
- [深色首页](dark.png)
- [榜单与价格日期提醒](leaderboards.png)
- [390px 手机首页](mobile-hero-390.png)
- [390px 手机榜单](mobile-market-390.png)
- [320px 手机榜单](mobile-market-320.png)

## 复跑

在仓库根目录、已配置 Python 环境下运行：

```sh
uv run --no-project python build_report.py
uv run --no-project python -m unittest discover -s tests
uv run --no-project python scripts/publish.py build
uv run --no-project python scripts/publish.py check
uv run --no-project python scripts/smoke.py --browser-channel chrome
node --check report.js
git diff --check
```

本次 Mac 验收通过 `uv` 使用已配置的共享 Python 环境；复跑时按当前机器的 `LOCAL_CONTEXT.md` 选择解释器和执行前缀。浏览器 smoke 自行启动临时本地服务器和隔离浏览器配置，不需要个人浏览器资料；由 Codex 在 macOS 启动 Chrome 的命令须从第一次起获得 `require_escalated` 批准。未安装新依赖或创建持久虚拟环境。
