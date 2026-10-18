# 将正式 GitHub Environment 迁移为 release

此迁移准备完成前，正式环境仍为 `cloudflare-preview`（ID `24488063583`），PR 预览仍为 `preview`。工作流只在 Repository variable `PRODUCTION_ENVIRONMENT` 精确等于 `release` 时选择新环境；未设置或其他值继续使用既有 `cloudflare-preview`。只允许这两个固定名称，不能通过变量指定任意环境。新环境和凭据准备完成前不要切换变量，以免创建未配置保护的空环境。

2026-10-18 已只读检查 GitHub REST 环境接口和实际 GraphQL schema：`UpdateEnvironmentInput` 没有 name，Mutation 仅提供 create/delete/pin/reorder/updateEnvironment，没有 renameEnvironment。现有正式接口不能在保留同一 Environment ID、Secret 和历史的情况下原位改名。创建另一个环境也不会复制原 Secret；其值无法从 GitHub 读取。

## 需用户具体确认的迁移动作

- 新建 GitHub Environment `release`，从创建时就启用指定分支策略，并仅添加 `main` 分支规则，不允许 tag。其余保护与当前生产相同：无等待计时、无强制额外审批人。
- 在新环境设置非敏感 Variable `CLOUDFLARE_ACCOUNT_ID=cf37bfe5ee78022d9099c57673e50dbc`。
- 用户在 GitHub 页面直接录入已有的生产 Token，Secret 名仍为 `CLOUDFLARE_API_TOKEN`。代理不读取、导出或显示现有 Secret，不为改名生成新凭据。若用户已不保存原 Token，暂停并另行决定是否轮换，不能自动创建。
- 保留旧 `cloudflare-preview`、原 Secret、保护和部署历史；本次不删除旧环境，也不改变 Token 权限或 DNS。

2026-10-19（Asia/Taipei）用户确认后已回读：新 `release` ID 为 `24650354682`，仅 `main` 分支规则 ID 为 `63502314`，没有 tag 规则；部署 Secret 名称与账户 ID variable 均已配置。旧环境保留。实际切换是否成功仍以使用 `release` 的生产 run 和双入口验收为准。

## 配置完成后的切换顺序

1. 回读新环境：名称、ID、仅 main 的分支规则、Secret 名称与更新时间、账户 ID；只读元数据，不读取 Secret 值。
2. 确认没有旧的生产任务仍在上传，由用户确认准备完成后设置 Repository variable `PRODUCTION_ENVIRONMENT=release`，再从 main 运行现有生产工作流。工作流会选择已准备好的 `release`；Cloudflare Worker 仍是 `model-observatory`，域名仍是 `models.localgpt.net`。
3. 仓库开关 `CLOUDFLARE_DEPLOY_ENABLED=true` 保持原位。工作流需在新 Environment 成功取得既有凭据，通过原测试和双入口版本/哈希/响应头验收，才认定迁移成功。
4. 若新环境配置失败，先定位具体缺项或权限，不导出旧 Secret、不放宽分支规则。保留旧环境可通过普通回退 PR 恢复旧引用；先核对真实线上版本，不反复创建凭据或改 DNS。
5. 旧环境是否最终删除需另行明确确认。仅改显示名称不值得丢失凭据和历史，因此也可选择保留现名。

正式接口参考：[REST 环境接口](https://docs.github.com/en/rest/deployments/environments)、[Environment 保护规则](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)。
