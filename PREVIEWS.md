# PR 原生预览与首次配置 SOP

使用独立 Worker `model-observatory-preview` 的 Workers 原生 Previews。每个 PR 对应 `pr-<编号>`，有一个跟随更新的 Preview URL 和每次部署固定的 Unique Deployment URL。正式 Worker `model-observatory`、`cloudflare-preview` Environment 和 `models.localgpt.net` 继续使用原有发布流程。

## 两套 Environment，同名配置项

| 用途 | GitHub Environment | Cloudflare Worker | Secret | Variable |
| --- | --- | --- | --- | --- |
| 正式站 | `cloudflare-preview`（历史名称，暂不改名） | `model-observatory` | `CLOUDFLARE_API_TOKEN`：正式令牌 | `CLOUDFLARE_ACCOUNT_ID` |
| PR 预览 | 新建 `preview` | `model-observatory-preview` | `CLOUDFLARE_API_TOKEN`：独立预览令牌 | `CLOUDFLARE_ACCOUNT_ID` |

工作流 job 的 `environment` 决定读哪套配置，因此无需换 Secret/Variable 名称。账户 ID 相同：`cf37bfe5ee78022d9099c57673e50dbc`。不要在 Repository secrets 中放一个两套流程共用的 Cloudflare token。

## 用户配置

1. 在上述账户创建 `model-observatory-preview` 占位 Worker，并启用它的 workers.dev 地址与 **Preview URLs**。新原生 Previews 同样需要此地址开关。保持空白静态用途，不绑定自定义域名、生产资源、Cron、路由或业务 secrets。不需要新 DNS、Pages 项目或 prerelease 分支，也不连接 Cloudflare Git 构建。
2. 在 **Manage Account → Account API Tokens** 创建独立的 account-owned token：资源范围 **Specified Workers → 仅 `model-observatory-preview` → Editor**。Review token 时移除模板附带的全账户/全 Zone 权限。不要添加生产 Worker，不需要 Zone/DNS 权限。令牌由用户直接保存到 GitHub，不能粘贴到聊天、命令参数、仓库或日志。
3. 到仓库 **Settings → Environments → New environment**，创建 `preview`。添加上述同名 Secret 与 Variable。将 Deployment branches and tags 设为仅分支 `main`（不允许 tag）；这项新持久限制由用户确认并操作。是否加 Required reviewers 也由用户决定。不要修改已有 `cloudflare-preview`。
4. 保持 Repository variable `CLOUDFLARE_PREVIEWS_ENABLED` 缺省或 `false`。原正式开关 `CLOUDFLARE_DEPLOY_ENABLED` 不变。
5. 审阅并由用户决定合并本基础设施 PR。新增 workflow 必须先成为可信 `main` 代码；不要为抢先验收而让带 token 的任务执行 PR 分支。此 PR 本身只能验证无密钥 CI，不能自证新的生产权限。
6. 在 **Actions → Native PR previews → Run workflow**，分支选择 `main`，operation 选择 `permission-smoke`，PR 留空。该入口仅对预览 Worker 创建 `permission-smoke`、更新它、验证两次固定地址与稳定地址，再删除并确认不存在。只有 artifact 中 `deployment.json.status = passed`，才证明当前 token 能完成创建、更新、清理。单独的 Editor 文档不能代替这个实测。若报告没有可用 URL，先检查占位 Worker 的 Preview URLs 开关；不要改正式 Worker。必要时由用户明确授权后从干净 main 运行一次 `wrangler deploy --config wrangler.preview.json` 初始化这个独立父 Worker 的地址设置，再重新试验；本自动入口不会自行发布父 Worker。
7. 权限验收成功后，由用户设置 Repository variable `CLOUDFLARE_PREVIEWS_ENABLED=true`。新建一个普通源码 PR，等待 Verify static report 与 Native PR previews 完成，检查评论中的两个地址、commit 和数据变化摘要；追加一次提交验证稳定地址更新，然后关闭 PR 验证清理。不要通过直接 push main 来测试临时预览。

配置或权限验收尚未完成时，代码、单元测试与无密钥 PR CI 仍可先完成。当前不能把“实现已提交”写成“单 Worker Editor 已验收”。若 GitHub Actions 策略禁止工作流评论 PR，由用户检查仓库 Actions 权限设置；不要自动提升长期权限。

## 构建与凭据边界

`Verify static report` 在 PR 上构建、运行 Python 检查、Wrangler dry-run 和 Chrome 浏览器测试。它只有 `contents: read`，没有 Environment 和 Cloudflare secret。fork PR 也仅运行此验证；本阶段只给本仓库分支创建云端预览。

随后默认分支的 `Native PR previews` 收到 `workflow_run`。它固定 checkout `github.workflow_sha`，使用 main 的脚本、锁文件、Wrangler 4.151.1 和 `wrangler.preview.json`。不恢复 PR 写过的缓存，不执行 npm package hooks，不 checkout、导入或运行 PR 源码。

上传前核验：正确的 workflow ID/路径、成功 PR run、最新 run attempt、当前打开且非 draft 的 PR、当前 main base、当前 head、由这两个父提交生成的 build SHA，以及 artifact 名称和 ZIP digest。`version.json.ci` 必须逐字段匹配 repository/run/attempt/PR/head/base/build。run 超过七天、artifact 过期、PR 已变更或身份关系不符都会拒绝；更新分支并重新运行当前 PR 验证即可，不能重用旧 artifact。

ZIP 只允许 `index.html`、`report-data.json`、`report-data.csv`、`_headers`、`version.json` 五个有界普通文件；不接受目录、符号链接、重复项、额外代码或路径穿越。GitHub token 不随签名下载重定向发送。可信校验器再检查内容哈希、HTML/JSON/CSV 一致性及固定 CSP/响应头。

Cloudflare token 仅进入单独的发布/清理步骤。发布先确认目标父 Worker 已存在，使用 `wrangler preview --ignore-base-config --json`；已有 Preview 若含 bindings/secrets 会拒绝。原生 Preview JSON 返回的 URL 和部署 ID 写入记录，不猜测地址。相同 PR 的发布与清理共用并发锁；上传前后检查新旧状态，发现过期时清理本次 Preview。两个地址的版本、数据哈希和安全响应头都通过后，才更新同一条 PR 评论。

原生机制由 `previews: {}` 与 `wrangler preview` 决定，而 `preview_urls: true` 也负责它的 workers.dev 地址开关；独立预览配置设为 true。此字段名称沿用了 Version URLs，不能据此误判正在使用旧机制。正式配置仍为 false。静态文件同样使用 `_headers`，不增加 Worker 业务运行代码。

## 清理与失败恢复

启用自动预览后，PR close/merge 触发可信 `pull_request_target: closed` 清理任务；它只运行 main 脚本，不取 PR 代码。API 再次确认 PR 已关闭，只删除指定 `pr-<编号>` 的 Preview 及其历史部署，不删除父 Worker。已经不存在时视为成功。

- 自动清理失败、workflow 被禁用或关闭了预览开关：手动运行同一 workflow，operation=`cleanup`，填已关闭 PR 的编号。开放 PR 会被拒绝。
- 权限试验留下了 Preview：operation=`cleanup-smoke`，只清理固定的 `permission-smoke`。
- HTTP 401/403 或 Cloudflare code：保留 run 链接和 `preview-record` artifact，报告失败动作、端点与错误码。停止该动作，不自动扩成 All Workers/Admin，也不反复创建 token。
- 上传超时或未收到预期 JSON：记录是 `upload-started` 或 `uploaded`，结果可能不确定。先到指定 Worker 的对应 Preview 检查，不把失败日志理解为没有上传，也不宣称已验证成功。
- 旧 head/base 的任务失败是保护行为；先更新 PR，再等新的成功验证。draft 改为 ready 后可重跑该 PR 的 Verify 工作流 run；若基线已变更，先更新分支。

关掉 `CLOUDFLARE_PREVIEWS_ENABLED` 会同时停掉自动创建与自动 close 清理；手动清理仍可用。关闭开关前应清理现有临时预览，或记录后续手动清理清单。

预览公开访问，workers.dev 原生提供 `X-Robots-Tag: noindex`；这不是身份认证。Free 计划每 Worker 100 个 Preview、每 Preview 100 个部署，超限会清除最旧记录。固定部署地址也可能因超限或 PR 清理失效，不当作永久归档。项目长期证据保留在 Git；每次运行记录保留为 90 天 GitHub artifact。

参考（2026-10-17 核对）：[原生 Previews 与限制](https://developers.cloudflare.com/workers/previews/)、[配置与版本要求](https://developers.cloudflare.com/workers/previews/get-started/)、[CLI 与清理示例](https://developers.cloudflare.com/workers/previews/examples/)、[workers.dev 地址开关](https://developers.cloudflare.com/workers/previews/custom-domains/#enable-workersdev-preview-urls)、[单 Worker 权限](https://developers.cloudflare.com/workers/authorization/workers/)。官方现有权限页列明 Editor 的已有 Worker 部署能力，但未单列新 Preview 创建/删除端点，因此保留实际权限验收。
