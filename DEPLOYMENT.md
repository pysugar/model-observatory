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

macOS 若使用已安装的 Chrome，可用 `python scripts/smoke.py --browser-channel chrome`。由 Codex 启动浏览器时须遵循主机审批限制，不能用 `--no-sandbox` 绕过。Linux 首次安装浏览器系统依赖可运行 `python -m playwright install --with-deps chromium`。Ubuntu 23.10+ 若限制下载版 Chromium 的 user namespace，使用系统 Chrome：`python -m playwright install --with-deps chrome`，再给 smoke 命令加 `--browser-channel chrome`。CI 采用此通道并保持 sandbox 开启；不修改 AppArmor/sysctl。[Chromium 说明](https://chromium.googlesource.com/chromium/src/+/main/docs/security/apparmor-userns-restrictions.md)。实际浏览器版本记入 `test-results/smoke.json`，随 runner 系统 Chrome 更新。

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

GitHub Actions 的 **Deploy static preview** 是唯一部署入口。推送 `main` 或手动执行时，先调用 **Verify static report**。验证生成并上传一次 `dist/`；部署下载同一不可变产物，复核提交与 SHA256 后才执行 Wrangler，不重新构建。部署串行且不会取消正在执行的上传；旧提交若已不再是 `main`，停止发布。发布后分别检查自定义域名与 workers.dev 的线上版本、HTML/JSON/CSV 哈希及缓存/安全响应头，失败会使工作流失败，不能据此宣称上线成功。

部署开关使用非敏感的 Repository variable `CLOUDFLARE_DEPLOY_ENABLED`：未设置或 `false` 时关闭，明确授权发布后设为 `true`。工作流的 job `if` 只读取该 variable，不直接引用 Secret；即使存在同名 Secret，也不会用它打开部署门控。用户自行配置凭据，代理不读取、抓取或请求令牌展示页，也不要求把令牌发到聊天中。准备步骤如下：

1. 用户先在目标账户创建用于本项目的 `model-observatory` 占位 Worker；确认没有同名既有业务，使用平台 `workers.dev` 地址，不绑定自定义域名或连接 Git 自动构建。单 Worker 权限只能授予已存在的 Worker，`Editor` 不能创建或删除 Worker。
2. 进入 **Manage Account → Account API Tokens → Create Token**。在 **Permission policies** 中打开账户策略卡片的 **Edit policy**，展开当前显示 **Entire Account** 的资源范围下拉菜单，再选择 **Specified Workers → 仅 `model-observatory` → Editor**，由用户创建账户所属（account-owned）API token。`Specified Workers` 是资源范围选项，不在权限名称搜索框里。不要选择 All Workers、其他 Worker 或 Admin，也不推荐旧版账户全局 `Workers Scripts Edit`。
3. 用户在 GitHub 创建 `cloudflare-preview` Environment，只允许 `main`；建议指定人工审核人。将令牌直接保存为该 Environment 的 `CLOUDFLARE_API_TOKEN` secret，将已核对的账户 ID 保存为同一 Environment 的 `CLOUDFLARE_ACCOUNT_ID` variable；工作流使用 `vars.CLOUDFLARE_ACCOUNT_ID`，API Token 仍使用 `secrets.CLOUDFLARE_API_TOKEN`。`deploy` job 保留 `environment: cloudflare-preview`，运行步骤才能取得该环境的配置。GitHub 保存后不回显 Token Secret 值是正常行为，无需为了核验而重填；部署任务会校验目标账户并使用已保存令牌，不能打印令牌。令牌不得写入仓库、命令参数、聊天或日志。
4. 配置完成后仍保持部署开关关闭。首次平台预览发布须在发布改动通过审阅并合入 `main` 后另行确认；确认后再启用仓库 variable `CLOUDFLARE_DEPLOY_ENABLED=true` 并运行现有发布入口。

2026-10-16 已在实际 Account API Tokens 创建页展开上述资源菜单并确认存在 `Specified Workers`，入口不是个人 User API Tokens。若从模板进入，草稿可能同时带有“所有域名的 Workers Routes Write”和整账户多项权限；用户须移除这些宽泛策略，再检查 **Review token** 摘要只包含指定的 `model-observatory` 及其 `Editor` 权限后自行创建。不要把模板原有策略与新增的单 Worker 策略一起保留。当天复核 Worker 列表仍只有 `rproxy`、`vless`，目标占位 Worker 尚未创建，不能选择现有业务 Worker 来代替。代理此次仅展开菜单，未选择权限、提交策略或创建令牌。

Cloudflare 于 [2026-09-15 发布单 Worker 权限](https://developers.cloudflare.com/changelog/post/2026-09-15-granular-worker-permissions/)。[Workers 权限文档](https://developers.cloudflare.com/workers/authorization/workers/)说明：指定 Worker 的 `Editor` 可读取、更新和部署该 Worker，`wrangler deploy` 更新已有 Worker 的最低角色为该 Worker 的 `Editor`。CI 仅更新已有 Worker 的静态资源，不申请 Zone/DNS、KV、R2、D1 或计费权限；自定义域名由已授权的控制台会话管理。

**实际部署状态：**2026-10-16 的 [发布工作流 38899413377](https://github.com/pysugar/model-observatory/actions/runs/38899413377) 已完成静态资源上传与线上验收。它证明用户提供的凭据可用于当前链路，不证明令牌实际收窄到了建议的 granular 范围。若以后出现权限错误，应定位失败操作与端点，不自动改成账户全局权限；任何额外权限或资源范围扩展须重新说明并确认。新建 token、复用现有 token 到 CI、OAuth/GitHub App 授权仍由用户在动作时确认。

配置只上传静态资源，没有 Worker 运行代码、数据库或动态模型调用。`wrangler.json` 有意省略 `route` / `routes`，自定义域名按下节在控制台管理。不接入 Cloudflare Git 自动构建，以免与 GitHub Actions 形成第二个发布入口。Hermes 后续若需发布，也应触发同一 GitHub workflow。

2026-10-16 浏览器只读核对：`localgpt.net` 为 Active / Free / DNS Full，没有连接 Worker；账户已有 `rproxy`、`vless`，尚无 `model-observatory`。账户 Workers 子域为 `openai-proxy-local.workers.dev`。计划创建的新 Worker 名为 `model-observatory`，预期平台地址为 `https://model-observatory.openai-proxy-local.workers.dev`；此记录不表示它已创建或上线。首次启用前再次核查同名 Worker，确认仅更新用户为本项目创建的占位 Worker，避免覆盖其他业务。自定义域名可考虑 `models.localgpt.net`，需用户另行选定并确认 DNS/绑定动作。

2026-10-16 后续部署核查：用户已创建 `model-observatory`，平台地址与上面的计划一致；用户现已更换 Token，并将账户 ID 从 Secret 迁移到 variable：`cloudflare-preview` 使用 `CLOUDFLARE_API_TOKEN` Secret 与 `CLOUDFLARE_ACCOUNT_ID` variable。部署环境现已限制为分支 `main`（0 个 tag），未设置 Required reviewers。额外的 S3 相关 Secrets 不被本流水线引用，也不在此流程中修改。凭据实际是否可用，以经用户授权的部署结果为准；不因值不可见而更换令牌。

首次实际发布的上传步骤已成功，浏览器能读取报告与版本清单；默认 `Python-urllib` 客户端的验收请求收到 Cloudflare [1010 客户端签名拦截](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/)。探针现在发送明确的项目 User-Agent（含仓库链接），不伪装浏览器、不更改 Cloudflare 防护或凭据，并继续严格核验 TLS、版本、数据哈希与响应头。若仍收到 HTTP 错误，日志包含状态码与请求路径；不能因页面可见就跳过发布验收。上传成功只证明用户当前提供的凭据可用，不证明其权限已收窄到文档建议的单 Worker 范围。

## 修改内容与自动上线条件

发布入口读取源码，调用 `build_report.py` 在临时目录重建，再把生成的 HTML 放到 `dist/index.html`。根目录的 `model-capability-cost.html`、`report-data.json` 和 `report-data.csv` 是离线产物，不是发布构建的直接输入。仅修改这些产物并推送 `main` 也会触发工作流，但线上内容仍由源码决定，手改产物的内容不会进入发布。具体编辑文件及证据输入见 [README 的更新入口](README.md#更新线上报告)。

自动发布需要同时满足：

1. 提交已经推送到 `main`（包括 PR 合并），或手动运行 **Deploy static preview** 并选择 `main`。工作流没有文件路径过滤；本地未推送的修改、其他分支推送不会发布，PR 验证本身也不部署。
2. Repository variable `CLOUDFLARE_DEPLOY_ENABLED` 为字符串 `true`。它用于 job 启动前的门控，继续放在 Repository variables；不要随账户 ID 一起搬到 Environment variables。
3. **Verify static report** 的测试、干净构建、产物审计、Wrangler 检查及浏览器冒烟测试全部通过。
4. `cloudflare-preview` 环境允许 `main`，环境的有效 `CLOUDFLARE_API_TOKEN` Secret 与匹配目标账户的 `CLOUDFLARE_ACCOUNT_ID` variable 已配置；若以后设置人工审批，审批也须通过。
5. 部署下载同一份已验证产物，提交及哈希核验通过，而且该提交在上传前仍是远程 `main` 最新提交。上传串行执行。

发布后两个域名都必须通过版本、HTML/JSON/CSV 哈希和响应头验收，才能认定上线成功。修改 GitHub Secret / variable 本身不会触发发布；需要新的 `main` 提交或上述手动入口。构建离线执行，不会自动抓取或调研新的模型数据。

## 自定义域名与后续发布

正式入口为 <https://models.localgpt.net>；<https://model-observatory.openai-proxy-local.workers.dev> 保留用于独立验收。2026-10-16 用户明确授权后，先确认 `models` 和通配符 DNS 搜索无记录、`localgpt.net` 无 Worker Routes，再通过目标 Worker 的 **Domains → Add Domain → localgpt.net → models → Production** 绑定。Cloudflare 自动管理对应的 Worker DNS 记录和证书；不手工 CNAME 到 workers.dev。参见 [Custom Domains 官方说明](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/)。上文未创建/未绑定的记录是此前准备阶段的历史状态。

域名由控制台管理，CI 不写入域名绑定，也不扩展部署令牌权限。保持 `wrangler.json` 省略 `route` / `routes`，部署命令不传 `--route` / `--domain`：锁定的 Wrangler 4.151.1 在没有域名条目时跳过 Custom Domain 发布，保留已存在的绑定。已核对其 `resolveRoutes` 与 `triggersDeploy` 实现；`publishCustomDomains` 只在 Custom Domain 列表非空时调用。不要随意加上其他域名条目，因为该接口会替换此 Worker 的域名集合。升级 Wrangler 时须复核行为，并在正常发布后确认域名仍有效。

首次自定义域名验收发现 Zone 现有 Web Analytics 会自动注入 beacon，导致 HTML 哈希与原产物不同。发布响应头因此包含 `Cache-Control: public, max-age=0, must-revalidate, no-transform`；[Cloudflare 官方文档](https://developers.cloudflare.com/web-analytics/get-started/#sites-proxied-through-cloudflare)说明 `public, no-transform` 会阻止自动注入。此设置只作用于本项目响应，保留原 HTML 和 CSP，不修改其他站点的统计或安全设置。

同一发布工作流现在同时探测两个 HTTPS 入口，并要求它们都匹配已验证产物中的 Git 提交、HTML/JSON/CSV 哈希与缓存/安全响应头。任一入口证书失败、不可访问或内容不一致，发布验收都会失败；不降低 TLS 校验、不跳过自定义域名。GitHub Environment 的展示 URL 使用正式入口。

## 回滚与失败恢复

若线上探针失败，先看工作流日志、`version.json` 与已保存产物，不重复创建凭据或改变 DNS。默认不自动回滚，因为探针可能因临时网络失败；先确认实际线上版本。

常规回滚：用 `git revert` 撤销有问题的内容提交，提交 PR、验证后合入 `main`，由同一流水线发布回退后的内容。这样保留新的审计提交与版本探针；不要直接重跑已过时的部署任务，旧提交保护会拒绝它。若工作流本身损坏，可在明确确认后使用 Cloudflare 的已有版本回滚能力进行应急恢复，并立即同步 Git 历史及重新核验线上版本；本阶段没有执行此操作。

## 仍然存在的研究限制

静态校验只能保证构建和证据保真，不能证明模型身份/别名映射、实时可用性或跨基准可比性正确。中文任务与真实 OpenClaw/Hermes 工作流仍未实测；模型身份、默认回退与不同快照的解释沿用原报告。不得把通过 CI 解释为重新验证了研究结论。自动调研、定时任务及大规模数据结构调整留到下一阶段。

参考：[Workers Static Assets](https://developers.cloudflare.com/workers/static-assets/)、[响应头](https://developers.cloudflare.com/workers/static-assets/headers/)、[GitHub Actions 部署](https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/)。

## 独立 PR 预览与研究入口

新增 [原生 Previews 流程](PREVIEWS.md)使用另一个 Worker 和 `preview` Environment；上文的 `cloudflare-preview` 保持正式用途。本文件既有准备阶段记录按时间保留，当前已验证基线见 [RELEASES.md](RELEASES.md)。[研究任务包与独立复核](RESEARCH_WORKFLOW.md)已提供手动入口，模型执行器、定时 LLM、长期身份和自动合并仍待用户确认接入。
