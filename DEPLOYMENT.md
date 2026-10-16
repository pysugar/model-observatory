# 静态验证与发布

本阶段只增加静态发布能力，沿用冻结证据与 Python 构建，不改变研究结论。所有命令从仓库根目录执行；路径不依赖 `/opt`、机器名称或个人虚拟环境。后续可将仓库放在 Hermes 机器的同一路径，此阶段不迁移机器、不启用自动调研。

## 本地验证

需要 Python 3.11+、Node.js 24+。CI 固定 Python 3.13 / Node 24，Python 与 npm 依赖分别锁在 `requirements-test.txt`、`package-lock.json`。

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-test.txt
python -m playwright install chromium
npm ci
python -m unittest discover -s tests -v
python scripts/publish.py build
python scripts/publish.py check
python scripts/smoke.py
npm run check:wrangler
python scripts/smoke.py --wrangler
```

macOS 若使用已安装的 Chrome，可用 `python scripts/smoke.py --browser-channel chrome`。由 Codex 启动浏览器时须遵循主机审批限制，不能用 `--no-sandbox` 绕过。Linux 首次安装浏览器系统依赖可运行 `python -m playwright install --with-deps chromium`。

`smoke.py` 自动创建临时本地 HTTP 服务并关闭；`--wrangler` 自动启停实际 Wrangler 本地服务，并检查响应头。验证 6 个报告面板、筛选、CSV 缺值、预算边界、4 种 Opus 证据、桌面与 390/320px 布局，以及无外部请求。输出在被 Git 忽略的 `test-results/`。它也可检查已经启动的 Wrangler 本地服务：

```sh
npm run preview
# 在另一个终端，沿用上面的 Python 环境：
python scripts/smoke.py --base-url http://127.0.0.1:8787 --cloudflare
```

原 `validate_report.py` 是保留的更完整历史验收脚本；需提供 README 中的本地 HTTP 服务与 Chrome。新流水线使用不依赖固定端口、Chrome 安装位置或个人配置的 `scripts/smoke.py`。

## 公开产物边界

`python scripts/publish.py build` 在临时目录调用现有 `build_report.py`，不会改写根目录旧报告。`dist/` 只允许 5 个文件：

| 文件 | 用途 |
| --- | --- |
| `index.html` | 原报告的完整静态页面，数据、样式和脚本内嵌 |
| `report-data.json`、`report-data.csv` | 报告已经展示的整理数据、来源及方法说明 |
| `version.json` | Git 提交、提交时间、证据核验日期、dirty 标记与文件 SHA256 |
| `_headers` | 缓存、内容类型保护、限制页面执行和外部请求；Cloudflare 不公开此控制文件 |

不复制 `.git`、凭据、README、研究网页/PDF 原件、截图、脚本或附件目录。白名单之外的文件、符号链接、明显密钥/邮箱/个人路径、数据不一致和哈希变化会阻止发布。扫描不能证明任意内容都适合公开；增加新字段或来源时仍须审阅其内容及再分发范围。当前整理数据保留原来源归属，不新增原始材料副本。

同一提交和输入产生相同字节；版本使用提交时间，不写当前机器时间。`--require-clean` 拒绝未提交变化，CI 绑定 `version.json.source_commit` 与该次 GitHub SHA。HTML、JSON、CSV 保真检查继续保留缺测、回退、估计值和原始 121 条证据。

## 唯一发布入口

GitHub Actions 的 **Deploy static preview** 是唯一部署入口。推送 `main` 或手动执行时，先调用 **Verify static report**。验证生成并上传一次 `dist/`；部署下载同一不可变产物，复核提交与 SHA256 后才执行 Wrangler，不重新构建。部署串行且不会取消正在执行的上传；旧提交若已不再是 `main`，停止发布。发布后检查线上版本、HTML/JSON/CSV 哈希及缓存/安全响应头，失败会使工作流失败，不能据此宣称上线成功。

默认没有 `CLOUDFLARE_DEPLOY_ENABLED=true`，所以只执行验证。启用前需要负责人逐项确认并在 GitHub 设置：

1. 创建 `cloudflare-preview` Environment，只允许 `main`；建议指定人工审核人。
2. 配置经确认的 Cloudflare API token 为该 Environment 的 `CLOUDFLARE_API_TOKEN` secret；不得写入文件、命令参数或日志。
3. 将该 Environment 的 `CLOUDFLARE_ACCOUNT_ID` variable 设为已核对账户 ID。
4. 最后将仓库 variable `CLOUDFLARE_DEPLOY_ENABLED` 设为 `true`，才启用未来持续部署。

以上持久授权和凭据配置尚未执行。新建 token、复用现有 token 到 CI、OAuth/GitHub App 授权均需动作时确认。建议只授予目标账户的 Workers Scripts 编辑权限；若 Cloudflare 当前 UI/API 还要求读取账户资料，再明确列出后确认。预览不需要 Zone/DNS 编辑、KV、R2、D1 或计费权限。普通 token 的账户级 Workers 权限可能覆盖该账户其他 Worker，不能声称已经限制到单个 Worker；如 UI 支持更窄资源范围，优先选取并重新核实。

配置只上传静态资源，没有 Worker 运行代码、数据库、动态模型调用、自定义域名或 routes。不接入 Cloudflare Git 自动构建，以免与 GitHub Actions 形成第二个发布入口。Hermes 后续若需发布，也应触发同一 GitHub workflow。

2026-10-16 浏览器只读核对：`localgpt.net` 为 Active / Free / DNS Full，没有连接 Worker；账户已有 `rproxy`、`vless`，尚无 `model-observatory`。账户 Workers 子域为 `openai-proxy-local.workers.dev`。计划创建的新 Worker 名为 `model-observatory`，预期平台地址为 `https://model-observatory.openai-proxy-local.workers.dev`；此记录不表示它已创建或上线。首次启用前再次核查同名 Worker，防止覆盖后来新增的应用。自定义域名可考虑 `models.localgpt.net`，需用户另行选定并确认 DNS/绑定动作。

## 回滚与失败恢复

若线上探针失败，先看工作流日志、`version.json` 与已保存产物，不重复创建凭据或改变 DNS。默认不自动回滚，因为探针可能因临时网络失败；先确认实际线上版本。

常规回滚：用 `git revert` 撤销有问题的内容提交，提交 PR、验证后合入 `main`，由同一流水线发布回退后的内容。这样保留新的审计提交与版本探针；不要直接重跑已过时的部署任务，旧提交保护会拒绝它。若工作流本身损坏，可在明确确认后使用 Cloudflare 的已有版本回滚能力进行应急恢复，并立即同步 Git 历史及重新核验线上版本；本阶段没有执行此操作。

## 仍然存在的研究限制

静态校验只能保证构建和证据保真，不能证明模型身份/别名映射、实时可用性或跨基准可比性正确。中文任务与真实 OpenClaw/Hermes 工作流仍未实测；模型身份、默认回退与不同快照的解释沿用原报告。不得把通过 CI 解释为重新验证了研究结论。自动调研、定时任务及大规模数据结构调整留到下一阶段。

参考：[Workers Static Assets](https://developers.cloudflare.com/workers/static-assets/)、[响应头](https://developers.cloudflare.com/workers/static-assets/headers/)、[GitHub Actions 部署](https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/)。
