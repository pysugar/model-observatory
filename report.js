"use strict";
(() => {
  const DATA = JSON.parse(document.getElementById("report-data").textContent);
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const finite = value => typeof value === "number" && Number.isFinite(value);
  const fmt = (value, digits = 2) => finite(value) ? value.toLocaleString("en-US", {maximumFractionDigits:digits}) : "未提供";
  const money = value => finite(value) ? "$" + fmt(value, value < 1 ? 4 : 2) : "未提供";
  const link = (url, label) => `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(label)}</a>`;
  const modelMap = new Map(DATA.models.map(m => [m.name, m]));
  const claudeAdvice = new Map(DATA.claude_advice.map(row => [row.model, row]));
  const inScope = (model, scope) => scope === "all" || scope === "current" && model.current || scope === "claude" && model.vendor === "Anthropic" || scope === "screenshot" && model.screenshot_visible;
  const order = ["minimal", "low", "medium", "high", "xhigh", "max", "default", "ultra", "unspecified", "unverified"];
  const symbols = {minimal:"·", low:"●", medium:"■", high:"▲", xhigh:"◆", max:"★", default:"○", ultra:"✚", unspecified:"◇", unverified:"×"};
  const labels = {default:"provider default", ultra:"Ultra 编排", unspecified:"档位未注明", unverified:"配置待核验"};
  const effortKey = row => row.variant === "provider_default" ? "default" : row.variant === "ultra_harness" ? "ultra" : row.effort;
  const effortText = row => row.variant === "provider_default" ? `default（来源：${row.source_effort_label || row.effort}）` : row.variant === "unverified" ? `${row.source_effort_label} · 待核验` : row.variant === "unspecified" ? "未注明档位" : row.effort;
  const sampleText = row => row.benchmark === "general" ? row.score_estimated ? "来源估计；部分子项缺测" : "10 项指数（预算见来源）" : row.benchmark === "writing" ? "10 brief × 5 稿" : row.benchmark === "arena" ? `${fmt(row.n,0)} 会话` : `${row.passes}/${row.n} 通过`;
  const timeText = row => finite(row.time_s) ? fmt(row.time_s,1) + " 秒" : finite(row.minutes_per_task_all_runs) ? fmt(row.minutes_per_task_all_runs,1) + " 分钟" : "未提供";
  const table = (head, body) => `<table><thead><tr>${head.map(x => `<th>${x}</th>`).join("")}</tr></thead><tbody>${body}</tbody></table>`;
  const exportCSV = (rows, name) => {
    const fields = [...new Set(rows.flatMap(row => Object.keys(row)))];
    const cell = value => '"' + String(value == null ? "" : typeof value === "object" ? JSON.stringify(value) : value).replaceAll('"','""') + '"';
    const contents = "\uFEFF" + [fields.map(cell).join(","), ...rows.map(row => fields.map(k => cell(row[k])).join(","))].join("\r\n");
    const url = URL.createObjectURL(new Blob([contents], {type:"text/csv;charset=utf-8"}));
    const a = document.createElement("a"); a.href = url; a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  // Availability, API controls, and measured coverage are separate facts.
  function claudeCoverage(name) {
    const profile = DATA.aa_profiles.find(p => p.model === name);
    const rows = DATA.rows.filter(r => r.model === name);
    return {
      aa: profile ? `${fmt(profile.metrics["Intelligence Index"])}${profile.score_estimated ? "* 估计" : ""} · ${profile.effort === "unspecified" ? "thinking / 档位未注明" : profile.effort}${profile.fallback ? " · 含回退" : ""}` : "未纳入同版数据",
      aa_url: profile?.source_url,
      writing: rows.filter(r => r.benchmark === "writing").length,
      coding: rows.filter(r => r.benchmark === "coding").length,
    };
  }
  const shownClaude = () => DATA.models.filter(m => m.vendor === "Anthropic" && inScope(m,$("claudeScope").value));
  function renderClaudeCatalog() {
    const models = shownClaude();
    $("claudeCount").textContent = `${models.length} 款 · 起步建议不等于已测甜蜜点`;
    $("claudeCatalog").innerHTML = `<table class="task-table"><caption>Claude 型号、推理起点与证据覆盖</caption><thead><tr>${["型号 / 入口","推理控制 / API 默认","编码起步 / 依据","保留、升档或换模型条件","本报告证据"].map(title => `<th scope="col">${title}</th>`).join("")}</tr></thead><tbody>${models.map(m => {
      const advice = claudeAdvice.get(m.name), coverage = claudeCoverage(m.name);
      return `<tr><th scope="row">${link(m.source,m.short)}<span class="task-detail">${esc(m.lifecycle)}${m.screenshot_visible ? " · 客户端常见" : " · 扩展目录"}</span>${m.lifecycle === "Deprecated" ? '<span class="evidence-badge">11-30 退役</span>' : ""}${m.short === "Fable 5" ? '<span class="evidence-badge">需 usage credits</span>' : ""}</th><td data-label="推理控制 / API 默认">${esc(m.efforts)}<span class="task-detail">默认：${esc(m.default_effort)}</span></td><td data-label="编码起步 / 依据"><strong>${esc(advice.start)}</strong><span class="task-detail">${esc(advice.basis)}</span></td><td data-label="保留、升档或换模型条件">${esc(advice.upgrade)}</td><td data-label="本报告证据">AA：${coverage.aa_url ? link(coverage.aa_url,coverage.aa) : coverage.aa}<span class="task-detail">英文写作：${coverage.writing ? coverage.writing+" 个配置" : "缺测"}<br>Vulcan v4：${coverage.coding ? coverage.coding+" 个配置" : "缺同版数据"}</span><button class="inline-button" data-claude-reasoning="${esc(m.name)}">查看档位证据 →</button></td></tr>`;
    }).join("")}</tbody></table>`;
    $("claudeCatalog").querySelectorAll("[data-claude-reasoning]").forEach(button => button.addEventListener("click", () => {
      $("deltaModel").value = button.dataset.claudeReasoning;
      $("deltaGroup").value = "coding";
      renderDeltas(); showPanel("reasoning");
      $("deltaModel").scrollIntoView({block:"center"});
    }));
  }
  $("claudeScope").addEventListener("change",renderClaudeCatalog);
  $("exportClaude").addEventListener("click",() => exportCSV(shownClaude().map(m => ({model:m.name,lifecycle:m.lifecycle,availability:m.availability_note,efforts:m.efforts,api_default:m.default_effort,...claudeAdvice.get(m.name),...claudeCoverage(m.name),chinese_tested:false,reviewed_at:DATA.claude_scope.reviewed_at,source_url:m.source,effort_source_url:"https://platform.claude.com/docs/en/build-with-claude/effort"})),"Claude选型-2026-10-16.csv"));
  $("restrictedClaude").innerHTML = table(["受限型号","官方状态","访问与证据限制"],DATA.claude_scope.restricted_models.map(m => `<tr><th>${link(m.source,m.model)}</th><td>${esc(m.status)}</td><td>${esc(m.access)}</td></tr>`).join(""));

  // Tabs retain independent filter state and expose keyboard navigation.
  function showPanel(name, updateHash = true) {
    if (!document.querySelector(`[data-panel="${name}"]`)) name = "overview";
    document.querySelectorAll(".panel").forEach(panel => { panel.hidden = panel.id !== name; });
    document.querySelectorAll("[data-panel]").forEach(tab => {
      tab.setAttribute("aria-selected", String(tab.dataset.panel === name));
      tab.tabIndex = tab.dataset.panel === name ? 0 : -1;
    });
    if (updateHash) {
      history.replaceState(null, "", "#" + name);
      window.scrollTo({top:Math.min(window.scrollY, document.querySelector(".nav-shell").offsetTop), behavior:"instant"});
    }
    if (name === "overview") renderTaskEffortChart();
    if (name === "explorer") renderExplorer();
    if (name === "capabilities") { renderEffortScalingChart(); renderCapIndexChart(); }
  }
  const tabs = [...document.querySelectorAll("[data-panel]")];
  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => showPanel(tab.dataset.panel));
    tab.addEventListener("keydown", event => {
      const target = event.key === "ArrowRight" ? (i+1)%tabs.length : event.key === "ArrowLeft" ? (i+tabs.length-1)%tabs.length : event.key === "Home" ? 0 : event.key === "End" ? tabs.length-1 : null;
      if (target !== null) { event.preventDefault(); showPanel(tabs[target].dataset.panel); tabs[target].focus(); }
    });
  });
  document.querySelectorAll("[data-jump]").forEach(button => button.addEventListener("click", () => {
    if (button.dataset.benchmark) changeGroup(button.dataset.benchmark);
    showPanel(button.dataset.jump);
    $("report-nav").scrollIntoView({block:"start"});
  }));
  window.addEventListener("hashchange", () => showPanel(location.hash.slice(1), false));
  $("printReport").addEventListener("click", () => window.print());

  // Each metric keeps its published unit; no synthetic overall score is made.
  const metrics = [
    ["Intelligence Index","综合指数","分","all","10 项评测加权；公开取整。"],
    ["AA-Briefcase v1.1","知识工作","Elo","work","知识工作交付质量；Elo 只在该基准内比较。"],
    ["GDPval-AA v2.1","职业任务","Elo","work","专业工作任务的成品质量。"],
    ["AutomationBench-AA","自动化","%","work","代理式计算机与业务工作流。"],
    ["Terminal-Bench 4.0","终端任务","%","coding","终端环境中的代理任务完成能力。"],
    ["SciCode","科学编码","%","coding","科学问题的代码实现。"],
    ["Humanity's Last Exam","高难知识","%","coding","高难度学科问题；使用 AA 的具体实验协议。"],
    ["CritPt","物理研究","%","coding","研究级物理问题。"],
    ["GDP.pdf","PDF 理解","%","reliability","从专业 PDF 提取并运用信息。"],
    ["AA-Omniscience","事实可靠性","指数","reliability","正确、错误与拒答共同计分，不是简单正确率。"],
    ["AA-LCR v1.1","长文推理","%","reliability","长上下文推理，不是上下文容量。"],
    ["Output Speed","生成吞吐","token/s","speed","流式输出速度，越高越快；不含开始作答前的等待。"],
    ["Time to First Answer Token","开始作答","秒 ↓","speed","TTFA 含开始输出可见答案前的推理等待，越低越快。"],
    ["Time per Task","任务时间估算","秒 ↓","speed","由 token 用量及吞吐推算；不是每道题实测墙钟。"],
    ["Cost per Task","加权任务费用","USD ↓","all","来源按子项加权的费用，不等于总费用除以固定题数。"]
  ];
  let metricSort = {key:"Intelligence Index", descending:true};
  const shownProfiles = () => DATA.aa_profiles.filter(p => inScope(modelMap.get(p.model),$("profileScope").value));
  function renderProfiles() {
    const dimension = $("dimension").value;
    const columns = metrics.filter(m => dimension === "all" || m[3] === dimension || m[3] === "all");
    const profiles = shownProfiles().sort((a,b) => {
      const x = a.metrics[metricSort.key], y = b.metrics[metricSort.key];
      if (!finite(x)) return finite(y) ? 1 : 0;
      if (!finite(y)) return -1;
      return (metricSort.descending ? -1 : 1) * (x-y);
    });
    $("capabilityTable").innerHTML = table(["模型 / 来源配置", ...columns.map(m => `<button class="metric-head" data-sort="${esc(m[0])}" title="${esc(m[4])}">${m[1]}${metricSort.key === m[0] ? metricSort.descending ? " ↓" : " ↑" : ""}<br><span class="small">${m[2]}</span></button>`)], profiles.map(p => `<tr><th class="metric-model">${link(p.source_url,p.model)}<small>${esc(p.source_label.replace(/^Anthropic /,""))}<br>${esc(p.snapshot)}${p.score_estimated ? " · 综合分为估计值" : ""}</small></th>${columns.map(m => `<td class="metric-value" title="${esc(p.raw_metrics[m[0]] || "未提供")}">${m[2].startsWith("USD") ? money(p.metrics[m[0]]) : fmt(p.metrics[m[0]],2)}${p.raw_metrics[m[0]]?.includes("*") ? "*" : ""}</td>`).join("")}</tr>`).join(""));
    $("capabilityTable").querySelectorAll("[data-sort]").forEach(button => button.addEventListener("click", () => {
      metricSort = {key:button.dataset.sort, descending:metricSort.key === button.dataset.sort ? !metricSort.descending : !["Time to First Answer Token","Time per Task","Cost per Task"].includes(button.dataset.sort)};
      renderProfiles();
    }));
    $("dimensionNotes").innerHTML = columns.map(m => `<span><strong>${m[1]}：</strong>${m[4]}</span>`).join("　");
  }
  $("dimension").addEventListener("change", renderProfiles);
  $("profileScope").addEventListener("change", renderProfiles);
  $("exportProfiles").addEventListener("click", () => exportCSV(shownProfiles().map(p => ({model:p.model,effort:p.effort,source_label:p.source_label,snapshot:p.snapshot,version:p.version,fallback:p.fallback,score_estimated:!!p.score_estimated,...p.metrics,source_url:p.source_url})),"AA分项-2026-10-16.csv"));
  $("officialTable").innerHTML = table(["指标", ...DATA.official_metric_models.map(esc), "来源与可比性"], DATA.official_metrics.map(m => `<tr><th>${esc(m.metric)}<span class="spec-detail">${esc(m.unit)}</span></th>${m.values.map(v => `<td class="metric-value">${fmt(v,1)}</td>`).join("")}<td>${esc(m.caveat)}</td></tr>`).join(""));

  const GROUPS = {
    general:{title:"AA · 综合能力与评测费用", y:"AA Intelligence Index（分）", xmin:10, yrange:[15,65], axes:[["cost_usd","整套指数费用 USD"],["weighted_cost_per_task_usd","加权单任务费用 USD"]], unit:"v4.3.2；原45条为10-14，补4条于10-15、10条于10-16。同版、不同读取时间；* 为来源估计。", caveat:"整套指数与加权单任务是两种费用口径。Default Fallback 是来源配置的一部分，比例未知；这些点不能解释为无回退纯模型。", method:"综合指数由10项评测组成，样本规模因子项而异，不能合并为一个统一 n。费用为 AA 按来源价格与用量估算；不含重复测试，不是官方 token 单价或订阅扣额。原45条保持原快照；14个补充点使用同版页面。Opus 4.7 / 4.6 / 4.5 综合分为估计值；Fable 5 含4.8回退，均不进入纯模型前沿。Haiku 5.5 的阶梯价覆盖未确认。"},
    coding:{title:"Vulcan · 完整通过率与投入", y:"23题完整通过率（%）", yrange:[0,105], axes:[["cost_usd","每次尝试费用 USD"],["minutes_per_task_all_runs","每题墙钟分钟"]], unit:"9型号 × 5档 × 23题，每题每档一次；分数为全部隐藏测试通过率。", caveat:"CLI、运行日期和超时协议不同。Opus medium及以上混入4.8回退；Luna 6 xhigh/max 缺完整收据，保留失败分数与全部耗时，费用留空。", method:"任务为23个二进制重建题，不是一般仓库修复。费用为所有尝试的每题 API 等价均值，完整计费需要23/23收据；超时和失败不能删去。墙钟分钟覆盖全部运行。混合回退点可查看，但不连成纯模型曲线、不参与前沿。成本轴不会用有收据子样本均值补齐缺失费用。"},
    writing:{title:"ToneBench · 英文脚本质量与投入", y:"Writing Score（0–100）", yrange:[60,89], axes:[["cost_usd","每篇稿费用 USD"],["time_s","每篇稿秒数"]], unit:"同一 2026-10-13 20:08 UTC 快照；10个英文脚本 brief ×5稿；公开原始JSON的SHA256与原附件一致。", caveat:"自动评审与特定编辑风格，不代表中文写作。费用含思考输出，但全部失败重试的费用覆盖未确认；耗时含重试。default、Ultra、Fable 5 回退与待核验配置单独标记。", method:"四位自动评审按该项目的编辑标准打分，每个配置50篇稿。overall_std 是稿件间离散度，不是均值95%置信区间，因此没有伪造误差棒。provider_default 不等同显式 effort；Ultra 为编排变体。Argon no thinking 与当前官方支持档位冲突，原始观测保留但不进入标准比较。"},
    arena:{title:"Agent Arena · 真实用户代码任务", y:"Net Improvement（百分点）", yrange:[-2,26], axes:[["cost_usd","平台 Cost/Task P50 USD"]], unit:"2026-10-14榜单；本报告12个配置。误差棒为来源95% CI；10-12版当前信号口径。", caveat:"随机路由、相对平台平均基线的变化，不是绝对成功率。Cost/Task 为平台P50估计，部分单价与官方Standard不同；不能与Vulcan或其他基准直接换算。", method:"Arena 随机分配模型并以真实用户会话及工具行为估计相对效果。当前五项信号为确认成功、赞扬/抱怨、可引导性、Bash Reliability、工具幻觉，按平台当前方法等权。置信区间和样本量原样保留；前沿只看点估计，未进行模型之间的显著性检验。"}
  };
  const state = {group:"general", models:new Set(DATA.models.filter(m => m.current).map(m => m.name)), efforts:new Set(order), selected:null};
  const pureVariant = row => !["mixed_fallback","provider_default","ultra_harness","unverified","unspecified","estimated"].includes(row.variant) && !row.score_estimated;
  function eligible(row, xkey = $("xmetric").value) {
    if (!pureVariant(row) || !finite(row.score) || !finite(row[xkey]) || row[xkey] <= 0) return false;
    if (row.benchmark === "coding" && xkey === "cost_usd" && row.cost_complete === false) return false;
    return true;
  }
  function eligibilityText(row) {
    const reasons = {mixed_fallback:"混合回退", provider_default:"默认配置", ultra_harness:"Ultra 编排", unverified:"配置待核验", unspecified:"档位 / 预算未注明", estimated:"来源估计值"};
    if (reasons[row.variant]) return reasons[row.variant];
    if (!finite(row[$("xmetric").value])) return "当前横轴缺失";
    return row.benchmark === "general" && String(row.fallback).includes("Default Fallback") ? "可参与 · 含来源回退" : "可参与";
  }
  function filteredRows() {
    return DATA.rows.filter(r => r.benchmark === state.group && state.models.has(r.model) && state.efforts.has(effortKey(r)) && (!$("verifiedOnly").checked || eligible(r)));
  }
  function renderFilters() {
    $("models").innerHTML = DATA.models.map((m,i) => `<label class="check"><input type="checkbox" data-model="${i}" ${state.models.has(m.name) ? "checked" : ""}><span class="swatch" style="background:${m.color}"></span>${esc(m.name)}${!m.current ? '<span class="baseline">基线</span>' : ""}</label>`).join("");
    $("models").querySelectorAll("input").forEach(input => input.addEventListener("change", () => {
      const name = DATA.models[Number(input.dataset.model)].name;
      input.checked ? state.models.add(name) : state.models.delete(name); renderExplorer();
    }));
    const available = new Set(DATA.rows.filter(r => r.benchmark === state.group).map(effortKey));
    $("efforts").innerHTML = order.filter(e => available.has(e)).map(e => `<label class="check"><input type="checkbox" data-effort="${e}" ${state.efforts.has(e) ? "checked" : ""}>${symbols[e]} ${labels[e] || e}</label>`).join("");
    $("efforts").querySelectorAll("input").forEach(input => input.addEventListener("change", () => {
      input.checked ? state.efforts.add(input.dataset.effort) : state.efforts.delete(input.dataset.effort); renderExplorer();
    }));
  }
  function changeGroup(group) {
    state.group = group; state.selected = null;
    $("xmetric").innerHTML = GROUPS[group].axes.map(([key,label]) => `<option value="${key}">${label}</option>`).join("");
    document.querySelectorAll("[data-group]").forEach(b => b.setAttribute("aria-pressed",String(b.dataset.group === group)));
    renderFilters(); renderExplorer();
  }
  document.querySelectorAll("[data-group]").forEach(b => b.addEventListener("click", () => changeGroup(b.dataset.group)));
  ["xmetric","scale","pareto","verifiedOnly"].forEach(id => $(id).addEventListener("change",renderExplorer));
  function chooseModels(mode) { state.models = new Set(DATA.models.filter(m => inScope(m,mode)).map(m => m.name)); renderFilters(); renderExplorer(); }
  $("currentModels").addEventListener("click", () => chooseModels("current"));
  $("claudeModels").addEventListener("click", () => chooseModels("claude"));
  $("screenshotModels").addEventListener("click", () => chooseModels("screenshot"));
  $("selectAll").addEventListener("click", () => chooseModels("all"));
  $("clearAll").addEventListener("click", () => chooseModels("none"));
  $("reset").addEventListener("click", () => {state.efforts = new Set(order); $("verifiedOnly").checked = false; $("pareto").checked = true; $("scale").value = "log"; chooseModels("current"); changeGroup(state.group);});
  $("export").addEventListener("click", () => exportCSV(filteredRows(),`${state.group}-筛选数据-2026-10-16.csv`));

  function mark(row, x, y, color, open) {
    const attrs = `fill="${open ? "#fffef9" : color}" stroke="${color}" stroke-width="1.6"`;
    const e = effortKey(row);
    if (e === "medium") return `<rect x="${x-5}" y="${y-5}" width="10" height="10" ${attrs}/>`;
    if (e === "high") return `<path d="M${x},${y-6.5} L${x+6},${y+5} L${x-6},${y+5} Z" ${attrs}/>`;
    if (e === "xhigh" || e === "unspecified") return `<path d="M${x},${y-7} L${x+6},${y} L${x},${y+7} L${x-6},${y} Z" ${attrs}/>`;
    if (e === "max") {
      const points = Array.from({length:10},(_,i) => {const a = i*Math.PI/5-Math.PI/2, r = i%2 ? 3.6 : 7.2; return `${x+r*Math.cos(a)},${y+r*Math.sin(a)}`;});
      return `<polygon points="${points.join(" ")}" ${attrs}/>`;
    }
    if (e === "unverified" || e === "ultra") return `<path d="M${x-5},${y-5} L${x+5},${y+5} M${x-5},${y+5} L${x+5},${y-5}" stroke="${color}" stroke-width="2.4"/>`;
    return `<circle cx="${x}" cy="${y}" r="5" ${attrs}/>`;
  }
  function renderExplorer() {
    renderReleaseChart();
    const meta = GROUPS[state.group], rows = filteredRows(), key = $("xmetric").value;
    const plotted = rows.filter(r => finite(r[key]) && r[key] > 0 && finite(r.score));
    const candidates = plotted.filter(r => eligible(r,key));
    const frontier = candidates.filter(r => !candidates.some(o => o[key] <= r[key] && o.score >= r.score && (o[key] < r[key] || o.score > r.score))).sort((a,b) => a[key]-b[key]);
    $("charttitle").textContent = meta.title; $("unit").textContent = meta.unit; $("caveat").textContent = meta.caveat;
    $("count").textContent = `${rows.length} 条记录 · ${plotted.length} 个可绘点 · ${candidates.length} 个前沿可参与配置`;
    $("table-count").textContent = `${rows.length} 条；费用缺失仍保留记录。`;
    $("frontnote").textContent = `实心：可参与；空心/叉号：受限配置。${$("pareto").checked ? `虚线连接当前筛选下的 ${frontier.length} 个点估计前沿点；不代表差异显著。` : "条件前沿已隐藏。"}`;
    $("method").innerHTML = `<p>${meta.method}</p>`;
    const raw = DATA.raw_methods[state.group];
    $("rawmethod").textContent = raw ? typeof raw === "string" ? raw : JSON.stringify(raw,null,2) : "新增基准没有原报告英文方法；请参阅上方中文说明与证据页的方法链接。";
    $("tbody").innerHTML = rows.length ? rows.map(r => `<tr><td><button data-row="${r.id}">${esc(r.model)}<br>${esc(effortText(r))}</button></td><td>${fmt(r.score)}${r.score_estimated ? "*" : ""}${finite(r.ci95_halfwidth) ? ` ±${fmt(r.ci95_halfwidth)}` : ""}</td><td>${money(r.cost_usd)}</td><td>${timeText(r)}</td><td>${sampleText(r)}</td><td>${eligibilityText(r)}</td><td>${link(r.scorecard_url || r.source_url,"原始来源")}</td></tr>`).join("") : '<tr><td colspan="7" class="empty">当前没有符合筛选的记录。</td></tr>';
    $("tbody").querySelectorAll("[data-row]").forEach(button => button.addEventListener("click", () => showDetail(DATA.rows[Number(button.dataset.row)])));
    const missing = rows.filter(r => !finite(r[key]));
    const uncovered = [...state.models].filter(name => !DATA.rows.some(r => r.benchmark === state.group && r.model === name));
    $("gaps").innerHTML = missing.length || uncovered.length ? `<div class="gap">${missing.length ? `<p><strong>横轴缺失：</strong>${missing.map(r => `${esc(r.model)} ${esc(effortText(r))}${r.priced_n != null ? `（收据 ${r.priced_n}/${r.n}）` : ""}`).join("；")}。未画为零；记录仍可查看。</p>` : ""}${uncovered.length ? `<p><strong>没有纳入同基准数据：</strong>${uncovered.map(esc).join("、")}。不代表其能力为零。</p>` : ""}</div>` : "";
    const svg = $("chart"), width = Math.max(320,Math.round(svg.getBoundingClientRect().width || 1100));
    const height = width < 600 ? 390 : 470, margin = {left:54,right:22,top:34,bottom:66};
    svg.setAttribute("viewBox",`0 0 ${width} ${height}`); svg.setAttribute("height",height);
    if (!plotted.length) {
      svg.innerHTML = `<text x="${width/2}" y="${height/2}" text-anchor="middle" class="axis-label">当前筛选没有可绘数据</text>`;
      $("detail").innerHTML = '<p class="empty">选择模型和档位后查看配置细节。</p>'; return;
    }
    const log = $("scale").value === "log", values = plotted.map(r => r[key]);
    let lo = Math.min(...values), hi = Math.max(...values);
    if (log) { const pad = Math.max(Math.log10(hi/lo)*.055,.10); lo = 10**(Math.log10(lo)-pad); hi = 10**(Math.log10(hi)+pad); }
    else { hi *= 1.08; lo = 0; }
    const x = v => margin.left + (log ? Math.log(v/lo)/Math.log(hi/lo) : (v-lo)/(hi-lo))*(width-margin.left-margin.right);
    const [ymin,ymax] = meta.yrange, y = v => height-margin.bottom-(v-ymin)/(ymax-ymin)*(height-margin.top-margin.bottom);
    let parts = [`<title>${esc(meta.title)}</title>`];
    parts.push(`<rect x="${margin.left}" y="${margin.top}" width="${width-margin.left-margin.right}" height="${height-margin.top-margin.bottom}" fill="#ffffff"/>`);
    if ($("pareto").checked && plotted.length > 2) {
      const sortedX = [...values].sort((a,b) => a-b);
      const qxVal = sortedX[Math.floor(sortedX.length * 0.52)];
      const qyVal = ymin + (ymax - ymin) * 0.56;
      const qx = Math.max(margin.left + 40, Math.min(width - margin.right - 40, x(qxVal)));
      const qy = Math.max(margin.top + 30, Math.min(height - margin.bottom - 30, y(qyVal)));
      parts.push(`<rect x="${margin.left}" y="${margin.top}" width="${qx - margin.left}" height="${qy - margin.top}" fill="#dcfce7" fill-opacity="0.68"/>`);
      parts.push(`<rect x="${qx}" y="${qy}" width="${width - margin.right - qx}" height="${height - margin.bottom - qy}" fill="#f3f4f6" fill-opacity="0.65"/>`);
      parts.push(`<line x1="${qx}" x2="${qx}" y1="${margin.top}" y2="${height - margin.bottom}" stroke="#86efac" stroke-dasharray="3 3"/>`);
      parts.push(`<line x1="${margin.left}" x2="${width - margin.right}" y1="${qy}" y2="${qy}" stroke="#86efac" stroke-dasharray="3 3"/>`);
      parts.push(`<text x="${margin.left + 8}" y="${margin.top + 16}" font-size="10.5" font-weight="600" fill="#15803d" opacity="0.88">Most attractive quadrant</text>`);
    }
    for (let i=0;i<=5;i++) {const v = ymin+(ymax-ymin)*i/5; parts.push(`<line x1="${margin.left}" x2="${width-margin.right}" y1="${y(v)}" y2="${y(v)}" stroke="#e5ebe3"/><text x="${margin.left-10}" y="${y(v)+4}" text-anchor="end" class="tick">${fmt(v,1)}</text>`);}
    const ticks = width < 600 ? 4 : 6;
    for (let i=0;i<ticks;i++) {const v = log ? lo*(hi/lo)**(i/(ticks-1)) : lo+(hi-lo)*i/(ticks-1); parts.push(`<line x1="${x(v)}" x2="${x(v)}" y1="${margin.top}" y2="${height-margin.bottom}" stroke="#eef2ec" stroke-dasharray="3 3"/><text x="${x(v)}" y="${height-margin.bottom+23}" text-anchor="middle" class="tick">${fmt(v,v < 1 ? 3 : v < 10 ? 2 : 0)}</text>`);}
    parts.push(`<text x="${margin.left}" y="16" class="axis-label">${esc(meta.y)}</text><text x="${width/2}" y="${height-13}" text-anchor="middle" class="axis-label">${esc(meta.axes.find(a => a[0] === key)[1])}${log ? " · 对数刻度" : ""}</text>`);
    for (const name of state.models) {
      const line = plotted.filter(r => r.model === name && r.connect && pureVariant(r)).sort((a,b) => order.indexOf(a.effort)-order.indexOf(b.effort));
      if (line.length > 1) parts.push(`<polyline points="${line.map(r => `${x(r[key])},${y(r.score)}`).join(" ")}" fill="none" stroke="${modelMap.get(name).color}" stroke-width="1.6" opacity=".45"/>`);
    }
    if ($("pareto").checked && frontier.length > 1) parts.push(`<polyline points="${frontier.map(r => `${x(r[key])},${y(r.score)}`).join(" ")}" fill="none" stroke="#111827" stroke-width="2" stroke-dasharray="2.5 3.5"/>`);
    for (const r of plotted) {
      const cx=x(r[key]), cy=y(r.score), color=modelMap.get(r.model).color;
      if (finite(r.ci95_halfwidth)) parts.push(`<path d="M${cx},${y(r.score-r.ci95_halfwidth)} V${y(r.score+r.ci95_halfwidth)} M${cx-4},${y(r.score-r.ci95_halfwidth)} H${cx+4} M${cx-4},${y(r.score+r.ci95_halfwidth)} H${cx+4}" stroke="${color}" opacity=".55"/>`);
      parts.push(`<g class="dot" tabindex="0" role="button" data-row="${r.id}" aria-label="${esc(r.model+" "+effortText(r)+"，分数 "+fmt(r.score)+"，横轴 "+fmt(r[key],4))}"><title>${esc(r.model+" · "+effortText(r))}</title><circle class="focusring" cx="${cx}" cy="${cy}" r="10" fill="transparent" stroke="transparent"/>${mark(r,cx,cy,color,!eligible(r,key))}</g>`);
    }
    svg.innerHTML = parts.join("");
    svg.querySelectorAll(".dot").forEach(dot => {
      const select = () => showDetail(DATA.rows[Number(dot.dataset.row)]);
      dot.addEventListener("click",select); dot.addEventListener("mouseenter",select); dot.addEventListener("focus",select);
      dot.addEventListener("keydown",e => {if(e.key === "Enter" || e.key === " "){e.preventDefault();select();}});
    });
    const selected = rows.find(r => r.id === state.selected) || frontier[0] || plotted[0];
    showDetail(selected);
  }
  function showDetail(row) {
    state.selected = row.id;
    const notes = [];
    if (row.variant === "mixed_fallback") notes.push(row.benchmark === "coding" ? `包含 ${row.solver_fallback_runs} 个回退运行，Opus 4.8 回复占 ${fmt(row.opus48_reply_share_pct)}%；不视为纯 Opus 5.5。` : `来源包含 ${row.fallback || "Opus 4.8 回退"}；不视为纯模型成绩。`);
    if (row.score_estimated) notes.push("综合分是来源估计值，部分子项未测；不参与标准升档差分或前沿。");
    if (row.cost_complete === false) notes.push(`费用缺失：${row.priced_n}/${row.n} 个完整收据；有收据子集均价不用于主图。`);
    if (row.benchmark === "coding") notes.push(`CLI：${row.harness}；${row.protocol}；运行 ${row.run_start_utc} 至 ${row.run_end_utc}；超时 ${row.timeouts} 次。`);
    if (row.benchmark === "general") notes.push(`加权单任务 ${money(row.weighted_cost_per_task_usd)}；回退标记：${row.fallback || "未标注"}。`);
    if (row.benchmark === "writing") notes.push(`稿件间标准差 ${fmt(row.overall_std)}，不作为均值置信区间；${row.variant === "provider_default" ? "provider default 非显式指定档位。" : ""}`);
    if (row.variant === "unverified") notes.push("来源 no thinking 与官方支持档位不一致，实际请求设置尚未核验。");
    if (row.benchmark === "arena") notes.push(`95% CI：[${fmt(row.score-row.ci95_halfwidth)}, ${fmt(row.score+row.ci95_halfwidth)}] 个百分点；${fmt(row.n,0)} 会话。`);
    const peers = filteredRows().filter(r => r.id !== row.id && finite(r[$("xmetric").value]) && finite(row[$("xmetric").value]) && Math.abs(r.score-row.score) < (state.group === "coding" ? 1 : .5) && Math.abs(Math.log(r[$("xmetric").value]/row[$("xmetric").value])) < .1);
    $("detail").innerHTML = `<div class="topline"><h3>${esc(row.model)} · ${esc(effortText(row))}</h3><span class="tag">${eligibilityText(row)}</span></div><div class="numbers"><div><b>${fmt(row.score)}${row.score_estimated ? "*" : ""}${finite(row.ci95_halfwidth) ? " ±"+fmt(row.ci95_halfwidth) : ""}</b><span>${esc(row.score_name)}</span></div><div><b>${money(row.cost_usd)}</b><span>${state.group === "general" ? "整套指数" : state.group === "arena" ? "平台 P50 / 任务" : state.group === "writing" ? "每篇稿" : "每次尝试"}</span></div><div><b>${timeText(row)}</b><span>${sampleText(row)}</span></div></div>${notes.map(n => `<p>${esc(n)}</p>`).join("")}<p>快照 / 版本：${esc(row.snapshot || row.publication_date || "来源未统一快照")} · ${esc(row.version || row.version_snapshot || "")}</p><p>${link(row.scorecard_url || row.source_url,"查看原始来源")}${row.data_source_url ? " · "+link(row.data_source_url,"运行记录") : ""}</p>${peers.length ? `<div class="near"><span class="small">邻近点：</span>${peers.map(p => `<button data-peer="${p.id}">${esc(modelMap.get(p.model).short)} ${esc(effortText(p))}</button>`).join("")}</div>` : ""}`;
    $("detail").querySelectorAll("[data-peer]").forEach(b => b.addEventListener("click",() => showDetail(DATA.rows[Number(b.dataset.peer)])));
  }
  let resizeTimer;
  window.addEventListener("resize",() => {
    clearTimeout(resizeTimer);
    resizeTimer=setTimeout(() => {
      if(!$("overview").hidden) renderTaskEffortChart();
      if(!$("explorer").hidden) renderExplorer();
      if(!$("capabilities").hidden) { renderEffortScalingChart(); renderCapIndexChart(); }
    },120);
  });

  // Price scenarios use a shared token assumption, never benchmark re-pricing.
  const shownModels = () => DATA.models.filter(m => inScope(m,$("specScope").value));
  function renderSpecs() {
    $("specTable").innerHTML = table(["模型 / 定位", "窗口 / 最大输出", "原生输入 → 输出", "推理档位 / 默认", "输入 / 缓存 / 输出<br>USD / 百万 token"], shownModels().map(m => `<tr><th class="spec-name">${link(m.source,m.name)}<code>${esc(m.id)}</code><span class="spec-detail">${esc(m.role)}${!m.current ? " · 代际基线" : ""}</span>${m.lifecycle ? `<span class="spec-detail">${esc(m.lifecycle)} · ${esc(m.availability_note)}</span>` : ""}</th><td>${fmt(m.context,0)} / ${fmt(m.max_output,0)}<span class="spec-detail">${esc(m.context_note || (m.context_kind === "shared" ? "上下文窗口含输入和输出。" : "列为输入上限；输出另计。"))}</span></td><td>${esc(m.input_modalities)}<span class="spec-detail">→ ${esc(m.output_modalities)}</span></td><td>${esc(m.efforts)}<span class="spec-detail">默认：${esc(m.default_effort)}</span></td><td class="spec-money">${money(m.input)} / ${money(m.cached)} / ${money(m.output)}<span class="spec-detail">${esc(m.price_note)} ${link(m.price_source,"定价来源")} · ${esc(m.price_checked)}</span></td></tr>`).join(""));
    renderCalculator();
  }
  function renderCalculator() {
    const ids=["inputTokens","cachePercent","answerTokens","reasonTokens","requestCount"];
    const vals=ids.map(id => $(id).value === "" ? NaN : Number($(id).value));
    const [input,cache,answer,reason,count]=vals;
    if (vals.some(v => !finite(v) || v < 0) || cache > 100 || count < 1 || ![input,answer,reason,count].every(Number.isSafeInteger)) {
      $("calcSummary").textContent="请输入非负整数 token、至少1次请求，以及0–100%的缓存占比。"; $("costTable").innerHTML=""; return;
    }
    const future=$("priceScenario").value === "afterPromo";
    const costs=shownModels().map(m => {
      let prices={input:m.input,cached:m.cached,output:m.output},note="核验日 Standard";
      if(future && finite(m.future_input)){prices={input:m.future_input,cached:m.future_cached,output:m.future_output};note=`优惠 ${m.promo_end} 结束后`;}
      if(m.tier_threshold && input > m.tier_threshold){prices={input:m.tier_input,cached:m.tier_cached,output:m.tier_output};note=`prompt >${fmt(m.tier_threshold,0)}；整次升档`;}
      const over=answer+reason > m.max_output ? "超出同步输出上限" : input > m.context || m.context_kind === "shared" && input+answer+reason > m.context ? "超出上下文窗口" : null;
      const per=over ? null : (input*(1-cache/100)*prices.input+input*cache/100*prices.cached+(answer+reason)*prices.output)/1e6;
      return {m,prices,note,over,per,total:per === null ? null : per*count};
    }).sort((a,b) => (a.total ?? Infinity)-(b.total ?? Infinity));
    $("calcSummary").textContent=`每次 ${fmt(input,0)} 输入（${fmt(cache)}% 已命中缓存）＋ ${fmt(answer+reason,0)} 输出含推理，重复 ${fmt(count,0)} 次。按费用排序，未控制模型质量和实际用量差异。`;
    const max=Math.max(...costs.map(c => c.total || 0),.001);
    $("costTable").innerHTML=table(["模型","每次费用","全部请求费用","实际采用单价：输入 / 缓存 / 输出","适用条件"],costs.map(c => `<tr data-cost-model="${esc(c.m.id)}" data-per="${c.per ?? ""}" data-total="${c.total ?? ""}"><th>${esc(c.m.name)}</th><td>${money(c.per)}</td><td>${money(c.total)}${c.total !== null ? `<div class="cost-bar" style="width:${150*c.total/max}px"></div>` : ""}</td><td>${money(c.prices.input)} / ${money(c.prices.cached)} / ${money(c.prices.output)}</td><td>${esc(c.over || c.note)}</td></tr>`).join(""));
  }
  $("specScope").addEventListener("change",renderSpecs);
  $("exportSpecs").addEventListener("click",() => exportCSV(shownModels(),"官方规格-2026-10-16.csv"));
  ["inputTokens","cachePercent","answerTokens","reasonTokens","requestCount"].forEach(id => $(id).addEventListener("input",renderCalculator));
  $("priceScenario").addEventListener("change",renderCalculator);

  $("deltaModel").innerHTML=DATA.models.map(m => `<option>${esc(m.name)}</option>`).join("");
  $("deltaModel").value="Claude Opus 5.5";
  $("deltaGroup").value="writing";
  const opusViews = DATA.opus_coding_evidence.views;
  $("opusEvidenceView").innerHTML = opusViews.map(view => `<option value="${esc(view.id)}">${esc(view.title)}</option>`).join("");
  const currentOpusView = () => opusViews.find(view => view.id === $("opusEvidenceView").value);
  function renderOpusEvidence() {
    const view = currentOpusView();
    $("opusEvidenceScope").textContent = view.scope;
    $("opusEvidenceTable").innerHTML = table(view.columns.map(esc), view.display_rows.map(row => `<tr><th scope="row">${esc(row[0])}</th>${row.slice(1).map(value => `<td>${esc(value)}</td>`).join("")}</tr>`).join(""));
    $("opusEvidenceTable").scrollLeft = 0;
    $("opusEvidenceTakeaway").textContent = view.takeaway;
    $("opusEvidenceCaveat").textContent = view.caveat;
    $("opusEvidenceSources").innerHTML = view.sources.map(([url,title]) => link(url,title)).join(" · ");
  }
  $("opusEvidenceView").addEventListener("change", renderOpusEvidence);
  $("exportOpusEvidence").addEventListener("click", () => {
    const view = currentOpusView();
    exportCSV(view.rows.map(row => ({model:DATA.opus_coding_evidence.model,evidence_view:view.id,...row,scope:view.scope,caveat:view.caveat,common_tasks:view.common_tasks || null,source_urls:view.sources.map(source => source[0]),reviewed_at:DATA.opus_coding_evidence.reviewed_at})),`Opus编码-${view.id}-2026-10-16.csv`);
  });
  renderOpusEvidence();
  function renderDeltas() {
    const model = modelMap.get($("deltaModel").value), advice = claudeAdvice.get(model.name);
    $("deltaModelInfo").hidden = !advice;
    if (advice) {
      const coverage = claudeCoverage(model.name);
      $("deltaModelInfo").innerHTML = `<h3>${esc(model.name)} · ${esc(model.lifecycle)}</h3><p><strong>支持：</strong>${esc(model.efforts)}；<strong>API 默认：</strong>${esc(model.default_effort)}。</p><p><strong>编码起步：</strong>${esc(advice.start)}。${esc(advice.basis)}。</p><p>${esc(advice.upgrade)}</p><p><strong>覆盖：</strong>AA ${esc(coverage.aa)}；英文写作 ${coverage.writing} 个配置；Vulcan v4 ${coverage.coding ? coverage.coding+" 个配置" : "无同版数据"}。<strong>中文未实测。</strong></p><p class="small">${esc(model.availability_note)} ${link(model.source,"官方型号页")} · ${link("https://platform.claude.com/docs/en/build-with-claude/effort","effort 指南")}</p>`;
    }
    const opusCoding = $("deltaModel").value === "Claude Opus 5.5" && $("deltaGroup").value === "coding";
    $("opusCodingEvidence").hidden = !opusCoding;
    $("deltaTable").hidden = opusCoding;
    if (opusCoding) {
      $("deltaNote").textContent = "纯 Opus 5.5 的完整 23 题差分仍不足两个档位。下方可查看五档实际配置及三种补充证据；每张表的任务、统计与回退口径独立。";
      return;
    }
    const rows=DATA.rows.filter(r => r.model === $("deltaModel").value && r.benchmark === $("deltaGroup").value && pureVariant(r) && r.variant === "standard_effort").sort((a,b) => order.indexOf(a.effort)-order.indexOf(b.effort));
    const pairs=rows.slice(1).map((r,i) => [rows[i],r]).filter(([a,b]) => a.snapshot === b.snapshot && a.version === b.version && a.version_snapshot === b.version_snapshot);
    $("deltaTable").innerHTML=table(["相邻已测档位","分数变化","费用变化","耗时变化","如何解释"],pairs.length ? pairs.map(([a,b]) => {
      const delta=b.score-a.score,ratio=finite(a.cost_usd)&&finite(b.cost_usd)&&a.cost_usd>0 ? b.cost_usd/a.cost_usd : null;
      const ta=a.time_s ?? a.minutes_per_task_all_runs,tb=b.time_s ?? b.minutes_per_task_all_runs;
      const unit=a.benchmark === "coding" ? " 分钟" : " 秒";
      return `<tr><th>${esc(a.effort)} → ${esc(b.effort)}</th><td>${fmt(a.score)} → ${fmt(b.score)}<span class="spec-detail ${delta<0 ? "delta-negative" : "delta-positive"}">${delta>0 ? "+" : ""}${fmt(delta)} ${a.benchmark === "coding" ? "百分点" : "分"}</span></td><td>${money(a.cost_usd)} → ${money(b.cost_usd)}<span class="spec-detail">${finite(ratio) ? `${fmt(ratio)} 倍（${ratio>1 ? "+" : ""}${fmt((ratio-1)*100,1)}%）` : "费用不完整，不能算倍数"}</span></td><td>${finite(ta)&&finite(tb) ? `${fmt(ta,1)} → ${fmt(tb,1)}${unit}` : "未提供同口径耗时"}</td><td>${delta<0 ? "点估计下降；不证明普遍倒挂" : delta === 0 ? "本批分数不变；仍需考虑离散度" : "观测有增益；结合额外投入判断"}</td></tr>`;
    }).join("") : '<tr><td colspan="5" class="empty">不足两个可比较的显式标准档位；不补造升档曲线。</td></tr>');
    $("deltaNote").textContent=($("deltaGroup").value === "general" ? "AA 公开分数取整；Fable 5.1 / Opus 5.5 / Sonnet 5.5 含来源 Default Fallback，比例未知。旧版估计值、Fable 5 混合回退和未注明预算不进入标准差分。" : $("deltaGroup").value === "coding" ? "每档每题一次；Opus 5.5 混合回退被排除，Luna6缺费档位仍可比较分数但不计算费用倍数。" : "使用同一ToneBench快照；稿件离散度不等于差分置信区间。")+" 表中比较的是相邻已测档，不保证覆盖所有支持档位；分差未做配对显著性检验。";
  }
  ["deltaModel","deltaGroup"].forEach(id => $(id).addEventListener("change",renderDeltas));

  // 1. Five-Platform × Four-Family Panorama (#overview)
  function shownPanoramaRows() {
    const fam = $("panoramaFamily") ? $("panoramaFamily").value : "all";
    return (DATA.external_leaderboards?.four_family_matrix || []).filter(r => fam === "all" || String(r.family).includes(fam));
  }
  function renderPanorama() {
    const ext = DATA.external_leaderboards;
    if (!ext || !$("platformCards")) return;
    $("platformCards").innerHTML = ext.platforms.map(p => `<article class="platform-card"><h3>${link(p.url, p.name)}</h3><p><strong>核心指标：</strong>${esc(p.focus)}</p><p><strong>成本口径：</strong>${esc(p.cost_metric)}</p><span class="platform-stat">快照：${esc(p.snapshot)}</span></article>`).join("");
    const rows = shownPanoramaRows();
    if ($("panoramaCount")) $("panoramaCount").textContent = `${rows.length} 个在用系列 · 5 大主流评测站与生产调用横向对照`;
    $("panoramaTable").innerHTML = `<table class="task-table"><caption>四大模型家族（Grok / ChatGPT / Gemini / Claude）跨平台能力与成本对照矩阵</caption><thead><tr>${["家族 / 型号与状态","Artificial Analysis (v4.3.2)","Arena.ai & LiveBench 2.0","Scale SEAL 专项表现","OpenRouter 生产用量与成本","跨榜选型与甜蜜点建议"].map(h => `<th scope="col">${h}</th>`).join("")}</tr></thead><tbody>${rows.map(r => `<tr><th scope="row">${esc(r.model)} <span class="badge">${esc(r.family)}</span><span class="task-detail">${esc(r.status)}</span></th><td data-label="Artificial Analysis (v4.3.2)"><strong>II：${esc(r.aa_ii)}</strong><span class="task-detail">单任务成本：${esc(r.aa_cost_task)}<br>能力强项：${esc(r.aa_cap_highlights)}</span></td><td data-label="Arena.ai & LiveBench 2.0"><strong>Arena：${esc(r.arena)}</strong><span class="task-detail">LiveBench 2.0：${esc(r.livebench_2)}</span></td><td data-label="Scale SEAL 专项表现">${esc(r.scale_seal)}</td><td data-label="OpenRouter 生产用量与成本">${esc(r.openrouter)}</td><td data-label="跨榜选型与甜蜜点建议">${esc(r.sweet_spot)}</td></tr>`).join("")}</tbody></table>`;
    $("scaleHighlightsTable").innerHTML = table(["Scale SEAL 专项榜单","Top 1","Top 2","Top 3","Top 4"], ext.scale_highlights.map(s => `<tr><th>${link("https://labs.scale.com/leaderboard", s.benchmark)}</th><td><strong>#1</strong> ${esc(s.top1)}</td><td><strong>#2</strong> ${esc(s.top2)}</td><td><strong>#3</strong> ${esc(s.top3)}</td><td><strong>#4</strong> ${esc(s.top4)}</td></tr>`).join(""));
  }
  if ($("panoramaFamily")) {
    $("panoramaFamily").addEventListener("change", renderPanorama);
    $("exportPanorama").addEventListener("click", () => exportCSV(shownPanoramaRows(), "四大家族五站全景对比-2026-10-19.csv"));
  }

  // Capability values stay official; missing domains never borrow Intelligence Index.
  // BEGIN CAPABILITY_MATH (also exercised by the offline regression tests)
  const capabilityEfforts = ["non-reasoning", "minimal", "low", "medium", "high", "xhigh", "max", "unspecified"];
  const capScore = (e, key) => {
    const value = key === "__ii__" ? e.intelligenceIndex : e.capabilities?.[key];
    return finite(value) ? value : null;
  };
  const capPrecision = value => Number(value.toFixed(2));
  function capRanking(entries, key) {
    const valid = entries.filter(e => finite(capScore(e, key))).sort((a,b) =>
      capPrecision(capScore(b,key)) - capPrecision(capScore(a,key)) || a.slug.localeCompare(b.slug));
    const ranks = new Map();
    let previous = null, rank = 0;
    valid.forEach((e,i) => {
      const score = capPrecision(capScore(e,key));
      if (score !== previous) rank = i + 1;
      ranks.set(e.slug, rank); previous = score;
    });
    return {valid, ranks, n:valid.length};
  }
  function capScopeEntries(entries, scope) {
    return entries.filter(e => scope === "four_family_top" ? e.isTopVariant && e.isFourFamily && e.isCurrent :
      scope === "four_family_all" ? e.isFourFamily && e.isCurrent : scope === "all_top" ? e.isTopVariant : true)
      .sort((a,b) => b.intelligenceIndex - a.intelligenceIndex || a.slug.localeCompare(b.slug));
  }
  function capExportRows(entries, domains) {
    const rankings = new Map(domains.map(d => [d.key,capRanking(entries,d.key)]));
    return entries.map(e => {
      const row = {model:e.name, release:e.releaseName, vendor:e.vendor, effort:e.effort,
        fallback:e.fallbackLabel || "", intelligence_index:e.intelligenceIndex, cost_per_task_usd:e.costPerTask,
        representative_by_overall_ii:!!e.isTopVariant, comparison_n:entries.length,
        rank_rule:"competition ranks at published 2-decimal precision", source_url:e.sourceUrl};
      domains.forEach(d => {
        const ranking = rankings.get(d.key), score = capScore(e,d.key);
        row[d.key+"_score"] = score;
        row[d.key+"_status"] = finite(score) ? "observed" : "missing";
        row[d.key+"_view_rank"] = ranking.ranks.get(e.slug) ?? null;
        row[d.key+"_valid_n"] = ranking.n;
        row[d.key+"_aa_global_rank"] = e.strengthsGlobalRank?.[d.slug] ?? null;
      });
      return row;
    });
  }
  function effortRows(entries, key, selectedSlug) {
    const sorted = [...entries].sort((a,b) => capabilityEfforts.indexOf(a.effort)-capabilityEfforts.indexOf(b.effort));
    const best = Math.max(...sorted.map(e => capScore(e,key)).filter(finite));
    return sorted.map((e,i) => {
      const previous = sorted[i-1], score = capScore(e,key), previousScore = previous ? capScore(previous,key) : null;
      const cost = finite(e.costPerTask) ? e.costPerTask : null;
      return {variant:e.slug, model:e.releaseName, effort:e.effort, metric:key, score,
        score_status:finite(score) ? "observed" : "missing", cost_per_task_usd:cost,
        delta_score:finite(score) && finite(previousScore) ? score-previousScore : null,
        delta_cost_usd:previous && finite(cost) && finite(previous.costPerTask) ? cost-previous.costPerTask : null,
        previous_measured_effort:previous?.effort ?? null, selected:e.slug === selectedSlug,
        representative_by_overall_ii:!!e.isTopVariant,
        best_for_metric:finite(score) && capPrecision(score) === capPrecision(best),
        fallback:e.fallbackLabel || "", source_url:e.sourceUrl,
        snapshot:"2026-10-19", cost_scope:"AA overall Intelligence Index weighted cost per task; not domain cost"};
    });
  }
  // END CAPABILITY_MATH
  const capState = {tab:"all", selectedId:null};
  const getCapEntries = () => capScopeEntries(DATA.aa_capability_indexes?.entries || [], $("capIndexScope")?.value || "four_family_top");
  const capLabel = e => `${e.releaseShort || e.releaseName} · ${e.effort}`;
  function renderCapDetail(entry, entries, domains) {
    if (!entry || !$("capIndexDetail")) return;
    const rows = domains.map(d => {
      const score = capScore(entry,d.key), ranking = capRanking(entries,d.key), rank = ranking.ranks.get(entry.slug);
      return `<tr><th>${link("https://artificialanalysis.ai/zh/indexes/"+d.slug,d.label)}<span class="task-detail">${esc(d.coreEvals.join(" · "))}<br>${esc(d.weightNote)}</span></th><td>${finite(score) ? fmt(score,2) : "无数据 · 不参排"}</td><td>${rank ? `#${rank} / ${ranking.n} 个有效配置` : `不参排 / ${ranking.n} 个有效配置`}<span class="task-detail">候选 ${entries.length} 个；缺测 ${entries.length-ranking.n} 个</span></td><td>${entry.strengthsGlobalRank?.[d.slug] ? `AA 来源全球发布排名 #${entry.strengthsGlobalRank[d.slug]}` : "未提供"}<span class="task-detail">AA 全库分母未存档；与当前筛选排名不同</span></td></tr>`;
    }).join("");
    $("capIndexDetail").innerHTML = `<h3>${esc(capLabel(entry))} · 官方领域得分</h3><p class="small">${esc(entry.fallbackLabel || "来源未标记回退")} · ${link(entry.sourceUrl,"模型来源")} · ${link("https://artificialanalysis.ai/methodology/capability-indices","官方权重与方法")}。分项共享部分底层评测，六域领先不是六组独立实验。</p><div class="table-scroll">${table(["领域 / 构成与权重","官方分数","当前筛选排名 / 有效分母","来源全球排名（独立口径）"],rows)}</div>`;
  }
  function renderCapIndexChart() {
    const cap = DATA.aa_capability_indexes, svg = $("capBumpChart");
    if (!cap || !svg) return;
    const entries = getCapEntries();
    if (!entries.some(e => e.slug === capState.selectedId)) capState.selectedId = entries[0]?.slug;
    $("capModelPills").innerHTML = entries.map(e => `<button type="button" class="pill-btn ${e.slug === capState.selectedId ? "is-active" : ""}" aria-pressed="${e.slug === capState.selectedId}" data-cap-model="${esc(e.slug)}"><span class="swatch" style="background:${e.color}"></span>${esc(capLabel(e))}</button>`).join("");
    const width = Math.max(1180,Math.round(svg.getBoundingClientRect().width || 1180));
    const showII = $("capShowII").checked, domains = cap.domains;
    const allCols = [...(showII ? [{key:"__ii__",shortLabel:"综合指数 II"}] : []),...domains];
    const cols = capState.tab === "all" ? allCols : domains.filter(d => d.key === capState.tab);
    const rankings = new Map(cols.map(d => [d.key,capRanking(entries,d.key)]));
    const all = capState.tab === "all", margin = {left:all ? 255 : 265,right:all ? 255 : 140,top:90,bottom:40}, rowH=34;
    const maxN = Math.max(1,...cols.map(c => rankings.get(c.key).n));
    const height = margin.top+maxN*rowH+margin.bottom;
    const rankY = r => margin.top+(r-.5)*rowH;
    svg.setAttribute("viewBox",`0 0 ${width} ${height}`); svg.setAttribute("height",height);
    const parts = [`<title>官方能力指数；按发布的两位小数并列排名；缺失值不参排</title>`];
    const summary = cols.map(c => `${c.shortLabel} ${rankings.get(c.key).n}/${entries.length}`).join("；");
    $("capIndexCount").textContent = `候选 ${entries.length} 个配置，完整展示。有效数/候选数：${summary}。同分并列（1、1、3），按来源两位小数；无数据不参排。`;
    if (all) {
      const colX = i => margin.left+i*(width-margin.left-margin.right)/Math.max(1,cols.length-1);
      for(let r=1;r<=maxN;r++) parts.push(`<line x1="${margin.left}" x2="${width-margin.right}" y1="${rankY(r)}" y2="${rankY(r)}" stroke="#e3e9e1" stroke-dasharray="3 3"/><text x="12" y="${rankY(r)+4}" class="tick">#${r}</text>`);
      cols.forEach((c,i) => {
        const x=colX(i), n=rankings.get(c.key).n;
        parts.push(`<text x="${x}" y="28" text-anchor="middle" font-size="12" font-weight="700" fill="#165e54">${esc(c.shortLabel)}</text><text class="cap-denominator" data-domain="${c.key}" data-valid-n="${n}" x="${x}" y="49" text-anchor="middle" font-size="11" fill="#647571">有效 ${n}/${entries.length}</text><line x1="${x}" x2="${x}" y1="65" y2="${height-margin.bottom}" stroke="#dce3db"/>`);
      });
      const endPositions = new Map();
      [cols[0],cols[cols.length-1]].forEach(c=>{
        const groups=new Map();
        rankings.get(c.key).valid.forEach(e=>{const rank=rankings.get(c.key).ranks.get(e.slug);if(!groups.has(rank))groups.set(rank,[]);groups.get(rank).push(e);});
        groups.forEach((group,rank)=>group.forEach((e,i)=>endPositions.set(c.key+e.slug,rankY(rank)+(i-(group.length-1)/2)*14)));
      });
      [...entries].sort((a,b) => Number(a.slug===capState.selectedId)-Number(b.slug===capState.selectedId)).forEach(e => {
        const selected=e.slug===capState.selectedId;
        let path="", previous=false;
        const nodes=cols.map((c,i) => {
          const rank=rankings.get(c.key).ranks.get(e.slug), score=capScore(e,c.key);
          if (!rank) {previous=false;return "";}
          const x=colX(i), y=rankY(rank);
          path+=`${previous ? "L" : "M"}${x},${y} `;previous=true;
          return `<circle class="cap-node" data-domain="${c.key}" data-score="${score}" data-rank="${rank}" data-valid-n="${rankings.get(c.key).n}" cx="${x}" cy="${y}" r="${selected ? 9 : 5}" fill="${e.color}" stroke="#fffef9" stroke-width="1.5"><title>${esc(capLabel(e)+" · "+c.shortLabel+" "+fmt(score,2)+" · #"+rank+"/"+rankings.get(c.key).n)}</title></circle>${selected ? `<text x="${x}" y="${y+3}" font-size="9" text-anchor="middle" fill="white">${rank}</text>` : ""}`;
        }).join("");
        const first=cols[0], last=cols[cols.length-1], firstRank=rankings.get(first.key).ranks.get(e.slug),lastRank=rankings.get(last.key).ranks.get(e.slug);
        const endLabel=(c,r,x,anchor) => {
          if(!r)return "";
          const labelY=endPositions.get(c.key+e.slug), pointX=anchor==="end"?margin.left:width-margin.right;
          return `${Math.abs(labelY-rankY(r))>2?`<line x1="${pointX}" y1="${rankY(r)}" x2="${x}" y2="${labelY}" stroke="${e.color}" stroke-width=".8"/>`:""}<text x="${x}" y="${labelY+4}" text-anchor="${anchor}" font-size="10.5" fill="${selected ? "#165e54" : "#223c3a"}">${esc(capLabel(e))} · ${esc(c.key==="__ii__" ? "II" : c.shortLabel)} ${fmt(capScore(e,c.key),2)}</text>`;
        };
        parts.push(`<g class="bump-group ${selected ? "is-highlighted" : ""}" tabindex="0" role="button" aria-pressed="${selected}" data-cap-id="${esc(e.slug)}" aria-label="${esc(capLabel(e))}"><title>${esc(capLabel(e)+" · "+(e.fallbackLabel || "来源未标记回退"))}</title><path class="bump-path" d="${path}" fill="none" stroke="${e.color}" stroke-width="${selected?3.6:2}" opacity="${selected?1:.55}"/>${nodes}${endLabel(first,firstRank,margin.left-14,"end")}${endLabel(last,lastRank,width-margin.right+14,"start")}</g>`);
      });
    } else {
      const dom=cols[0], ranking=rankings.get(dom.key), x=v=>margin.left+v/100*(width-margin.left-margin.right);
      for(let t=0;t<=100;t+=20) parts.push(`<text x="${x(t)}" y="46" class="tick" text-anchor="middle">${t} 分</text><line x1="${x(t)}" x2="${x(t)}" y1="65" y2="${height-margin.bottom}" stroke="#e3e9e1"/>`);
      ranking.valid.forEach((e,i) => {
        const y=rankY(i+1), sc=capScore(e,dom.key), rank=ranking.ranks.get(e.slug);
        parts.push(`<g class="bump-group" tabindex="0" role="button" data-cap-id="${esc(e.slug)}" aria-label="${esc(capLabel(e)+"，"+fmt(sc,2)+"分，排名"+rank+"，有效"+ranking.n)}"><text x="8" y="${y+4}" font-size="11">#${rank} ${esc(capLabel(e))}</text><rect class="cap-bar" data-score="${sc}" data-rank="${rank}" data-valid-n="${ranking.n}" x="${margin.left}" y="${y-9}" width="${x(sc)-margin.left}" height="18" rx="3" fill="${e.color}"/><text x="${x(sc)+8}" y="${y+4}" font-size="12">${fmt(sc,2)} 分</text></g>`);
      });
    }
    svg.innerHTML=parts.join("");
    const missing=domains.map(d=>({d,entries:entries.filter(e=>!finite(capScore(e,d.key)))})).filter(x=>x.entries.length);
    $("capMissingNote").textContent=missing.length ? missing.map(x=>`${x.d.label}缺测 ${x.entries.length} 个：${x.entries.map(capLabel).join("、")}`).join("；")+"。无节点、断开连线、不补值，CSV 分数与排名留空。" : "当前集合六域数据完整。";
    const select=id=>{capState.selectedId=id;renderCapIndexChart();[...$("capModelPills").querySelectorAll("button")].find(b=>b.dataset.capModel===id)?.focus();};
    $("capModelPills").querySelectorAll("[data-cap-model]").forEach(b=>b.addEventListener("click",()=>select(b.dataset.capModel)));
    svg.querySelectorAll("[data-cap-id]").forEach(node=>{
      node.addEventListener("click",()=>select(node.dataset.capId));
      node.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();select(node.dataset.capId);}});
    });
    renderCapDetail(entries.find(e=>e.slug===capState.selectedId),entries,domains);
  }
  if ($("capIndexTabs")) {
    $("capIndexTabs").querySelectorAll("[data-cap-tab]").forEach(btn=>btn.addEventListener("click",()=>{
      capState.tab=btn.dataset.capTab;
      $("capIndexTabs").querySelectorAll("[data-cap-tab]").forEach(b=>b.setAttribute("aria-pressed",String(b===btn)));
      renderCapIndexChart();
    }));
    ["capIndexScope","capShowII"].forEach(id=>$(id).addEventListener("change",renderCapIndexChart));
    $("exportCapIndexes").addEventListener("click",()=>exportCSV(capExportRows(getCapEntries(),DATA.aa_capability_indexes.domains),"AA官方能力指数-2026-10-19.csv"));
  }

  // Same-release, same-snapshot official effort evidence in the reasoning tab.
  const effortView = {selectedSlug:null};
  function renderReasoningCharts() {
    const cap=DATA.aa_capability_indexes;
    if (!cap || !$("reasoningCurve")) return;
    const entries=cap.entries.filter(e=>e.releaseSlug===$("reasoningRelease").value);
    if (!entries.some(e=>e.slug===effortView.selectedSlug)) effortView.selectedSlug=entries.find(e=>e.isTopVariant)?.slug || entries[0]?.slug;
    const key=$("reasoningMetric").value, metric=key==="__ii__" ? "综合指数 II" : cap.domains.find(d=>d.key===key).label;
    const rows=effortRows(entries,key,effortView.selectedSlug), color=entries[0]?.color || "#165e54";
    $("reasoningSelected").innerHTML=rows.map(r=>`<option value="${esc(r.variant)}">${esc(r.effort)}${r.representative_by_overall_ii?" · II 代表档":""}</option>`).join("");
    $("reasoningSelected").value=effortView.selectedSlug;
    const selected=rows.find(r=>r.selected), valid=rows.filter(r=>finite(r.score)), costs=valid.filter(r=>finite(r.cost_per_task_usd)&&r.cost_per_task_usd>=0);
    $("reasoningChartNote").textContent=`图表与表格可横向滚动。${entries[0]?.releaseName} · ${metric}：${valid.length}/${rows.length} 个配置有分数，${costs.length} 个同时有 AA 加权成本。选中 ${selected?.effort}；实心点为选中档，外圈为该维度最高分（可并列）。横轴档位等距只表顺序；不同厂商不等预算。`;
    const maxScore=Math.max(10,...valid.map(r=>r.score)), ceiling=Math.ceil(maxScore/10)*10;
    const w=620,h=340,m={left:65,right:35,top:35,bottom:65}, y=v=>h-m.bottom-v/ceiling*(h-m.top-m.bottom);
    const axis=()=>{
      const parts=[];
      for(let tick=0;tick<=ceiling;tick+=ceiling/5) parts.push(`<line x1="${m.left}" x2="${w-m.right}" y1="${y(tick)}" y2="${y(tick)}" stroke="#e3e9e1"/><text x="${m.left-10}" y="${y(tick)+4}" text-anchor="end" font-size="11">${fmt(tick,1)}</text>`);
      parts.push(`<text x="${m.left}" y="18" font-size="12" fill="#165e54">${esc(metric)}（0–100）</text>`);return parts;
    };
    const node=(r,x,cy,offset=-15,compact=false)=>`<g class="reasoning-dot" role="button" tabindex="0" aria-pressed="${r.selected}" data-variant="${esc(r.variant)}" data-score="${r.score}" aria-label="${esc(r.effort+"，"+metric+" "+fmt(r.score,2)+"，AA 加权成本 "+money(r.cost_per_task_usd))}"><title>${esc(r.effort+" · "+fmt(r.score,2)+" 分 · "+money(r.cost_per_task_usd)+" · "+(r.fallback||"来源未标记回退"))}</title>${r.best_for_metric?`<circle cx="${x}" cy="${cy}" r="11" fill="none" stroke="${color}" stroke-width="1.5"/>`:""}<circle cx="${x}" cy="${cy}" r="${r.selected?7:5}" fill="${r.selected?color:"#fffef9"}" stroke="${color}" stroke-width="2"/><text x="${x}" y="${cy+offset}" text-anchor="middle" font-size="11" fill="${color}">${esc(r.effort)}${compact ? "" : " · "+fmt(r.score,2)}</text></g>`;
    const x=i=>rows.length===1 ? (m.left+w-m.right)/2 : m.left+i*(w-m.left-m.right)/(rows.length-1);
    const curve=axis();let path="",previous=false;
    rows.forEach((r,i)=>{if(!finite(r.score)){previous=false;return;}path+=`${previous?"L":"M"}${x(i)},${y(r.score)} `;previous=true;});
    curve.push(`<path d="${path}" fill="none" stroke="${color}" stroke-width="2"/>`);
    rows.forEach((r,i)=>{curve.push(`<text x="${x(i)}" y="${h-40}" text-anchor="middle" font-size="11">${esc(r.effort)}</text>`);if(finite(r.score))curve.push(node(r,x(i),y(r.score)));else curve.push(`<text x="${x(i)}" y="${h-75}" text-anchor="middle" font-size="11">无数据</text>`);});
    curve.push(`<text x="${w/2}" y="${h-10}" text-anchor="middle" font-size="12">同一模型的已测档位（等距，不代表投入倍数）</text>`);
    const cost=axis(), maxCost=Math.max(.01,...costs.map(r=>r.cost_per_task_usd))*1.12, cx=v=>m.left+v/maxCost*(w-m.left-m.right);
    for(let i=0;i<=4;i++){const v=i*maxCost/4;cost.push(`<text x="${cx(v)}" y="${h-40}" text-anchor="middle" font-size="11">${money(v)}</text>`);}
    costs.forEach((r,i)=>cost.push(node(r,cx(r.cost_per_task_usd),y(r.score),i%2 ? 24 : -18,true)));
    if(!costs.length)cost.push(`<text x="${w/2}" y="${h/2}" text-anchor="middle">无同口径费用，不补估算散点</text>`);
    cost.push(`<text x="${w/2}" y="${h-10}" text-anchor="middle" font-size="12">AA 综合指数加权单任务成本（USD）</text>`);
    [["reasoningCurve",curve],["reasoningCost",cost]].forEach(([id,parts])=>{const svg=$(id);svg.setAttribute("viewBox",`0 0 ${w} ${h}`);svg.innerHTML=`<title>${esc(entries[0]?.releaseName+" · "+metric)}</title>`+parts.join("");});
    $("reasoningEvidenceTable").innerHTML=table(["已测档位 / 来源配置","官方得分","相对上一已测档分差","AA 加权成本 / 增量","选档标记"],rows.map(r=>`<tr data-variant="${esc(r.variant)}"><th>${link(r.source_url,r.effort)}<span class="task-detail">${esc(r.fallback||"来源未标记回退")}</span></th><td>${finite(r.score)?fmt(r.score,2):"无数据"}</td><td>${finite(r.delta_score)?`${r.delta_score>0?"+":""}${fmt(r.delta_score,2)}（${esc(r.previous_measured_effort)} → ${esc(r.effort)}）`:"无可比相邻值"}</td><td>${money(r.cost_per_task_usd)}<span class="task-detail">增量 ${finite(r.delta_cost_usd)?(r.delta_cost_usd>0?"+":"")+money(r.delta_cost_usd):"未提供"}</span></td><td>${[r.selected?"当前选中":"",r.representative_by_overall_ii?"II 最高代表档":"",r.best_for_metric?"本维度最高（可并列）":""].filter(Boolean).join(" · ")||"—"}</td></tr>`).join(""));
    $("reasoningEvidenceTable").dataset.selected=effortView.selectedSlug;
    document.querySelectorAll("#reasoningCharts .reasoning-dot").forEach(dot=>{
      const select=()=>{effortView.selectedSlug=dot.dataset.variant;renderReasoningCharts();};
      dot.addEventListener("click",select);dot.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();select();$("reasoningSelected").focus();}});
    });
  }
  if ($("reasoningRelease")) {
    const releases=[...new Map(DATA.aa_capability_indexes.entries.map(e=>[e.releaseSlug,e.releaseName])).entries()];
    $("reasoningRelease").innerHTML=releases.map(([id,name])=>`<option value="${esc(id)}">${esc(name)}</option>`).join("");
    $("reasoningRelease").value="claude-opus-5-5";
    $("reasoningMetric").innerHTML=`<option value="__ii__">综合指数 II</option>`+DATA.aa_capability_indexes.domains.map(d=>`<option value="${d.key}">${esc(d.label)}</option>`).join("");
    ["reasoningRelease","reasoningMetric"].forEach(id=>$(id).addEventListener("change",renderReasoningCharts));
    $("reasoningSelected").addEventListener("change",()=>{effortView.selectedSlug=$("reasoningSelected").value;renderReasoningCharts();});
    $("exportReasoningEvidence").addEventListener("click",()=>exportCSV(effortRows(DATA.aa_capability_indexes.entries.filter(e=>e.releaseSlug===$("reasoningRelease").value),$("reasoningMetric").value,effortView.selectedSlug),"同模型推理档位-官方能力与AA加权成本-2026-10-19.csv"));
  }
  // Shared AA-style chart helpers (Most attractive quadrant, Pareto line, Vendor legend, Watermark)
  const AA_VENDOR_COLORS = {
    Anthropic: "#c86d51",
    OpenAI: "#111827",
    Google: "#1ca350",
    xAI: "#6e56cf",
    SpaceXAI: "#6e56cf",
    Meta: "#0284c7",
    Xiaomi: "#ea580c",
    DeepSeek: "#2563eb",
    Zhipu: "#0d9488",
    Alibaba: "#7c3aed",
    Moonshot: "#4f46e5",
    MiniMax: "#db2777",
    Other: "#6b7280"
  };
  const getReleaseColor = (rel, colorMode = "vendor") => {
    if (colorMode === "model") return rel.color || AA_VENDOR_COLORS[rel.vendor] || AA_VENDOR_COLORS.Other;
    return AA_VENDOR_COLORS[rel.vendor] || rel.color || AA_VENDOR_COLORS.Other;
  };
  function renderAALegendBar(containerId, {showQuadrant = true, showPareto = true, includeBackdropVendors = false, colorMode = "vendor", activeReleases = []} = {}) {
    const el = $(containerId);
    if (!el) return;
    const items = [];
    if (showQuadrant) {
      items.push(`<span class="aa-legend-item"><span class="aa-quad-swatch"></span>Most attractive quadrant</span>`);
    }
    if (showPareto) {
      items.push(`<span class="aa-legend-item"><span class="aa-pareto-swatch"></span>Pareto line</span>`);
    }
    if (colorMode === "model" && activeReleases.length) {
      activeReleases.forEach(r => {
        items.push(`<span class="aa-legend-item"><span class="aa-vendor-dot" style="background:${r.color}"></span>${esc(r.shortName || r.name)}</span>`);
      });
    } else {
      const vendors = [
        ["Anthropic", AA_VENDOR_COLORS.Anthropic],
        ["OpenAI", AA_VENDOR_COLORS.OpenAI],
        ["Google", AA_VENDOR_COLORS.Google],
        ["SpaceXAI (xAI)", AA_VENDOR_COLORS.xAI],
        ...(includeBackdropVendors ? [
          ["Meta", AA_VENDOR_COLORS.Meta],
          ["Xiaomi", AA_VENDOR_COLORS.Xiaomi],
          ["DeepSeek", AA_VENDOR_COLORS.DeepSeek],
          ["Other Models", AA_VENDOR_COLORS.Other]
        ] : [])
      ];
      vendors.forEach(([label, col]) => {
        items.push(`<span class="aa-legend-item"><span class="aa-vendor-dot" style="background:${col}"></span>${esc(label)}</span>`);
      });
    }
    el.innerHTML = items.join("");
  }
  function drawAAPlotChrome(parts, {width, height, margin, qx, qy, showQuadrant = true}) {
    const plotW = width - margin.left - margin.right;
    const plotH = height - margin.top - margin.bottom;
    parts.push(`<rect x="${margin.left}" y="${margin.top}" width="${plotW}" height="${plotH}" fill="#ffffff"/>`);
    if (showQuadrant && finite(qx) && finite(qy)) {
      const cx = Math.max(margin.left + 36, Math.min(width - margin.right - 36, qx));
      const cy = Math.max(margin.top + 28, Math.min(height - margin.bottom - 28, qy));
      parts.push(`<rect x="${margin.left}" y="${margin.top}" width="${cx - margin.left}" height="${cy - margin.top}" fill="#dcfce7" fill-opacity="0.72"/>`);
      parts.push(`<rect x="${cx}" y="${cy}" width="${width - margin.right - cx}" height="${height - margin.bottom - cy}" fill="#f3f4f6" fill-opacity="0.65"/>`);
      parts.push(`<line x1="${cx}" x2="${cx}" y1="${margin.top}" y2="${height - margin.bottom}" stroke="#86efac" stroke-width="1.1" stroke-dasharray="3 3"/>`);
      parts.push(`<line x1="${margin.left}" x2="${width - margin.right}" y1="${cy}" y2="${cy}" stroke="#86efac" stroke-width="1.1" stroke-dasharray="3 3"/>`);
      parts.push(`<text x="${margin.left + 10}" y="${margin.top + 17}" font-size="11" font-weight="600" fill="#15803d" opacity="0.9">Most attractive quadrant</text>`);
    }
    parts.push(`<rect x="${margin.left}" y="${margin.top}" width="${plotW}" height="${plotH}" fill="none" stroke="#d5dfd9" stroke-width="1"/>`);
    // Artificial Analysis watermark badge in bottom-right inside plot area
    const wmW = 118, wmH = 22, wmX = width - margin.right - wmW - 10, wmY = height - margin.bottom - wmH - 8;
    parts.push(`<g opacity="0.86"><rect x="${wmX}" y="${wmY}" width="${wmW}" height="${wmH}" rx="4" fill="#ffffff" stroke="#d1d5db" stroke-width="0.9"/><text x="${wmX + wmW / 2}" y="${wmY + 14.5}" text-anchor="middle" font-size="11" font-weight="700" fill="#111827">Artificial Analysis</text></g>`);
  }
  function renderSmartLabels(parts, items, {width, height, margin, minGap = 15, xSpan = 135}) {
    items.forEach(it => {
      it.lx = Math.min(width - margin.right + 6, it.cx + 9);
      it.ly = Math.max(margin.top + 10, Math.min(height - margin.bottom - 8, it.cy));
    });
    for (let pass = 0; pass < 6; pass++) {
      items.sort((a,b) => a.ly - b.ly || a.lx - b.lx);
      for (let i = 0; i < items.length; i++) {
        for (let j = 0; j < i; j++) {
          if (Math.abs(items[i].lx - items[j].lx) < xSpan && items[i].ly - items[j].ly < minGap) {
            const mid = (items[i].ly + items[j].ly) / 2;
            items[j].ly = Math.max(margin.top + 10, mid - minGap / 2);
            items[i].ly = Math.min(height - margin.bottom - 8, items[j].ly + minGap);
          }
        }
      }
    }
    items.forEach(item => {
      if (Math.abs(item.ly - item.cy) > 3 || item.lx - item.cx > 12) {
        parts.push(`<line x1="${item.cx + 4}" y1="${item.cy}" x2="${item.lx - 2}" y2="${item.ly}" stroke="${item.col}" stroke-width="0.95" opacity="0.65"/>`);
      }
      parts.push(`<text x="${item.lx}" y="${item.ly + 3.5}" font-size="${item.isSel ? 12 : 11}" font-weight="${item.isSel ? 700 : 600}" fill="${item.isSel ? "#111827" : "#1f2937"}" style="paint-order:stroke;stroke:#ffffff;stroke-width:3.5px;stroke-linejoin:round">${esc(item.text)}</text>`);
    });
  }

  // 3. Flagship Task × Reasoning Effort Quadrant & Trajectory Chart (#overview -> #taskEffortCard)
  const TASK_DEFINITIONS = {
    complex: {
      key: "complex",
      shortLabel: "复杂问题解决",
      title: "复杂问题解决能力（HLE 50% + CritPt 50%）vs. 单任务成本（对数刻度）",
      yLabel: "复杂问题解决得分（HLE + CritPt 均值 · %）",
      unit: "%",
      digits: 1,
      yrange: [0, 54],
      yTicks: [0, 10, 20, 30, 40, 50],
      attractiveY: 35,
      attractiveX: 1.10,
      subnote: "本报告任务视图（Complex Reasoning & Frontier Science）：Humanity's Last Exam 与 CritPt 的等权均值，不是 AA 单独发布的任务指数。Opus 5.5 low {{aa:claude-opus-5-5:low:complex:1}}% → high {{aa:claude-opus-5-5:high:complex:1}}% → max {{aa:claude-opus-5-5:max:complex:1}}%；Sol high {{aa:gpt-6-1-sol:high:complex:1}}%，成本 ${{aa:gpt-6-1-sol:high:costPerTask:2}}。点估计差异不证明统计显著性。",
      getScore: v => v.taskScores?.complex
    },
    coding: {
      key: "coding",
      shortLabel: "编程与软件工程",
      title: "编程与软件工程能力（Terminal-Bench 4.0 + SciCode）vs. 单任务成本（对数刻度）",
      yLabel: "编程与软件工程得分（Terminal-Bench + SciCode 均值 · %）",
      unit: "%",
      digits: 1,
      yrange: [12, 68],
      yTicks: [20, 30, 40, 50, 60],
      attractiveY: 47,
      attractiveX: 1.10,
      subnote: "本报告任务视图（Coding & Software Engineering）：Terminal-Bench 4.0 与 SciCode 的等权均值，不是通用软件工程通过率。Opus 5.5 max {{aa:claude-opus-5-5:max:coding:1}}%，Sonnet 5.5 max {{aa:claude-sonnet-5-5:max:coding:1}}%；Sol medium/high 分别为 {{aa:gpt-6-1-sol:medium:coding:1}}% / {{aa:gpt-6-1-sol:high:coding:1}}%。Vulcan 的题集、脚手架与成本另列。",
      getScore: v => v.taskScores?.coding
    },
    planning: {
      key: "planning",
      shortLabel: "方案设计与规划",
      title: "方案设计、多源综合与战略规划能力（AA-Briefcase v1.1 Elo）vs. 单任务成本",
      yLabel: "方案设计与多源规划（AA-Briefcase v1.1 · 原始 Elo）",
      unit: " Elo",
      digits: 0,
      yrange: [650, 1880],
      yTicks: [800, 1000, 1200, 1400, 1600, 1800],
      attractiveY: 1450,
      attractiveX: 1.10,
      subnote: "本报告任务视图（Architecture, Strategy & Multi-Source Planning）：直接展示 AA-Briefcase v1.1 原始 Elo。Sonnet 5.5 max {{aa:claude-sonnet-5-5:max:planning:0}}、Opus 5.5 max {{aa:claude-opus-5-5:max:planning:0}}；Grok high {{aa:grok-4-7:high:planning:0}} → xhigh {{aa:grok-4-7:xhigh:planning:0}}，成本 ${{aa:grok-4-7:high:costPerTask:2}} → ${{aa:grok-4-7:xhigh:costPerTask:2}}。Elo 只作同基准相对比较，不能换算为能力百分比。",
      getScore: v => v.taskScores?.planning
    },
    agentic: {
      key: "agentic",
      shortLabel: "长程代理交付",
      title: "长程代理工作流交付能力（GDPval-AA v2.1 Elo）vs. 单任务成本",
      yLabel: "长程代理工作流交付（GDPval-AA v2.1 · 原始 Elo）",
      unit: " Elo",
      digits: 0,
      yrange: [950, 1950],
      yTicks: [1000, 1200, 1400, 1600, 1800],
      attractiveY: 1480,
      attractiveX: 1.10,
      subnote: "本报告任务视图（Long-Horizon Agentic Delivery）：直接展示 GDPval-AA v2.1 原始 Elo。Opus 5.5 max {{aa:claude-opus-5-5:max:agentic:0}}、Sonnet 5.5 max {{aa:claude-sonnet-5-5:max:agentic:0}}；Sol xhigh {{aa:gpt-6-1-sol:xhigh:agentic:0}} / ${{aa:gpt-6-1-sol:xhigh:costPerTask:2}}。Flash high 为 {{aa:gemini-3-8-flash:high:agentic:0}} / ${{aa:gemini-3-8-flash:high:costPerTask:2}}，未达到本视图的优选象限条件。",
      getScore: v => v.taskScores?.agentic
    },
    automation: {
      key: "automation",
      shortLabel: "多工具自动化",
      title: "多工具业务流程自动化（AutomationBench-AA 完成率）vs. 单任务成本",
      yLabel: "多工具流程自动化（AutomationBench-AA · %）",
      unit: "%",
      digits: 0,
      yrange: [0, 86],
      yTicks: [0, 20, 40, 60, 80],
      attractiveY: 58,
      attractiveX: 1.10,
      subnote: "本报告任务视图（Multi-Tool Workflow Automation）：直接展示 AutomationBench-AA 完成率。Argon high {{aa:gemini-4-argon:high:automation:0}}%、Opus 5.5 max {{aa:claude-opus-5-5:max:automation:0}}%、Fable 5.1 max {{aa:claude-fable-5-1:max:automation:0}}%；Sol high/xhigh {{aa:gpt-6-1-sol:high:automation:0}}% / {{aa:gpt-6-1-sol:xhigh:automation:0}}%。同名档位不表示相同推理预算。",
      getScore: v => v.taskScores?.automation
    },
    knowledge: {
      key: "knowledge",
      shortLabel: "长文档与抗幻觉",
      title: "长文档分析与知识抗幻觉（AA-LCR + GDP.pdf + Omniscience）vs. 单任务成本",
      yLabel: "长文档与知识抗幻觉合成得分（分）",
      unit: " 分",
      digits: 1,
      yrange: [15, 60],
      yTicks: [20, 30, 40, 50, 60],
      attractiveY: 44,
      attractiveX: 1.10,
      subnote: "本报告自定义合成分（Long-Context & Factual Grounding）：(AA-LCR v1.1 + 2 × GDP.pdf + 3 × AA-Omniscience) / 6；沿用各子项数值后加权，不是 AA 官方独立指数或成功率。Sol low {{aa:gpt-6-1-sol:low:knowledge:2}} 分、high {{aa:gpt-6-1-sol:high:knowledge:2}} 分（${{aa:gpt-6-1-sol:high:costPerTask:2}}）；Opus high/xhigh {{aa:claude-opus-5-5:high:knowledge:2}} / {{aa:claude-opus-5-5:xhigh:knowledge:2}} 分。Omniscience 的档位变化不证明幻觉变化的原因。",
      getScore: v => v.taskScores?.knowledge
    },
    intelligenceIndex: {
      key: "intelligenceIndex",
      shortLabel: "AA 综合智力指数",
      title: "Artificial Analysis 综合智力指数（10 项全量 v4.3.2）vs. 单任务成本",
      yLabel: "AA Intelligence Index v4.3.2（分）",
      unit: " 分",
      digits: 1,
      yrange: [14, 64],
      yTicks: [20, 30, 40, 50, 60],
      attractiveY: 42.5,
      attractiveX: 1.10,
      subnote: "直接使用快照中的 AA Intelligence Index v4.3.2（10 项评测）。留档方法的分类权重为 Agents 30%、Coding 20%、Scientific Reasoning 20%、General 30%；不由本报告的任务合成分重建。显示其他市场参考模型时，可叠加全部 30 个发布版本（94 个配置）；不同子评测保留自己的单位与口径。",
      getScore: v => v.intelligenceIndex
    }
  };

  const taskEffortState = {
    tab: "complex",
    selectedReleaseId: "claude-opus-5-5",
    selectedVariantSlug: null
  };
  const EFFORT_ORDER = ["non-reasoning", "low", "medium", "high", "xhigh", "max"];
  const EFFORT_SHORT = {"non-reasoning":"non-reas.", low:"low", medium:"med", high:"high", xhigh:"xhigh", max:"max"};

  // Select by the displayed task, breaking equal scores by the lower known cost.
  function bestTaskVariant(rel, taskDef) {
    return rel.variants
      .filter(v => finite(taskDef.getScore(v)) && finite(v.costPerTask) && v.costPerTask > 0)
      .sort((a,b) => taskDef.getScore(b) - taskDef.getScore(a) || a.costPerTask - b.costPerTask)[0];
  }

  function renderTaskCategoryCards(taskDef, activeReleases) {
    const el = $("taskCategoryCards");
    if (!el) return;
    const allVars = activeReleases.flatMap(rel => rel.variants.map(v => ({rel, v, score:taskDef.getScore(v)}))).filter(x => finite(x.score) && finite(x.v.costPerTask));
    if (!allVars.length) { el.innerHTML = ""; return; }
    const bestOverall = [...allVars].sort((a,b) => (b.score - a.score) || (a.v.costPerTask - b.v.costPerTask))[0];
    const inQuad = allVars.filter(x => x.v.costPerTask <= taskDef.attractiveX && x.score >= taskDef.attractiveY);
    const bestQuad = (inQuad.length ? inQuad : allVars.filter(x => x.v.costPerTask <= taskDef.attractiveX)).sort((a,b) => (b.score - a.score) || (a.v.costPerTask - b.v.costPerTask))[0] || bestOverall;
    const ultraLow = allVars.filter(x => x.v.costPerTask <= 0.16).sort((a,b) => (b.score - a.score) || (a.v.costPerTask - b.v.costPerTask))[0] || bestQuad;
    let bestGain = null;
    activeReleases.forEach(rel => {
      const pts = rel.variants.map(v => ({v, score:taskDef.getScore(v)})).filter(x => finite(x.score));
      if (pts.length >= 2) {
        const first = pts[0], last = pts.reduce((a,b) => b.score >= a.score ? b : a, pts[0]);
        const gain = last.score - first.score;
        if (!bestGain || gain > bestGain.gain) bestGain = {rel, first, last, gain};
      }
    });
    const cards = [
      {
        title: "能力上限冠军（Peak Capability）",
        main: `${bestOverall.rel.shortName || bestOverall.rel.name} (${bestOverall.v.effort})`,
        stat: `${fmt(bestOverall.score, taskDef.digits)}${taskDef.unit} · ${money(bestOverall.v.costPerTask)}/任务`,
        desc: `耗时 ${fmt(bestOverall.v.timePerTaskMinutes, 2)} 分钟 · 综合指数 ${fmt(bestOverall.v.intelligenceIndex, 1)}`
      },
      {
        title: "优选象限冠军（Most Attractive ≤ $1.10）",
        main: `${bestQuad.rel.shortName || bestQuad.rel.name} (${bestQuad.v.effort})`,
        stat: `${fmt(bestQuad.score, taskDef.digits)}${taskDef.unit} · ${money(bestQuad.v.costPerTask)}/任务`,
        desc: `与最高分相差 ${fmt(bestOverall.score - bestQuad.score, taskDef.digits)}${taskDef.unit === "%" ? " 个百分点" : taskDef.unit}，成本为该配置的 ${fmt((bestQuad.v.costPerTask / Math.max(0.001, bestOverall.v.costPerTask)) * 100, 0)}%`
      },
      {
        title: "轻量低成本甜点（Ultra-Low Cost ≤ $0.16）",
        main: `${ultraLow.rel.shortName || ultraLow.rel.name} (${ultraLow.v.effort})`,
        stat: `${fmt(ultraLow.score, taskDef.digits)}${taskDef.unit} · ${money(ultraLow.v.costPerTask)}/任务`,
        desc: `适合高并发子代理、初筛与快速路由基线`
      },
      bestGain ? {
        title: "最大推理升档跃迁（Steepest Effort Gain）",
        main: `${bestGain.rel.shortName || bestGain.rel.name}（${bestGain.first.v.effort} → ${bestGain.last.v.effort}）`,
        stat: `+${fmt(bestGain.gain, taskDef.digits)}${taskDef.unit === "%" ? " 个百分点" : taskDef.unit}（${fmt(bestGain.first.score, taskDef.digits)} → ${fmt(bestGain.last.score, taskDef.digits)}）`,
        desc: `成本由 ${money(bestGain.first.v.costPerTask)} 升至 ${money(bestGain.last.v.costPerTask)}/任务`
      } : null
    ].filter(Boolean);
    el.innerHTML = cards.map(c => `<article class="platform-card"><h3>${esc(c.title)}</h3><p><strong>${esc(c.main)}</strong></p><span class="platform-stat">${esc(c.stat)}</span><p>${esc(c.desc)}</p></article>`).join("");
  }

  function renderTaskEffortDetail(rel, focusVar, taskDef) {
    const el = $("taskEffortDetail");
    if (!el || !rel) return;
    const best = bestTaskVariant(rel, taskDef);
    const v = focusVar || best || rel.variants[rel.variants.length - 1];
    const score = taskDef.getScore(v);
    const rowsHtml = rel.variants.map((vr, idx) => {
      const sc = taskDef.getScore(vr);
      const prevSc = idx > 0 ? taskDef.getScore(rel.variants[idx - 1]) : null;
      const delta = finite(sc) && finite(prevSc) ? sc - prevSc : null;
      const em = vr.evalMetrics || {};
      return `<tr class="${vr.slug === v.slug ? "recommended-controller" : ""}"><th>${esc(vr.effort)} ${vr === best ? '<span class="badge">当前任务最佳档</span>' : ""}</th><td class="metric-value"><strong>${fmt(sc, taskDef.digits)}${taskDef.unit}</strong>${delta !== null ? `<span class="spec-detail ${delta < 0 ? "delta-negative" : "delta-positive"}">${delta > 0 ? "+" : ""}${fmt(delta, taskDef.digits)}</span>` : ""}</td><td class="metric-value">${fmt(vr.intelligenceIndex, 1)}</td><td class="metric-value">${fmt(em["Humanity's Last Exam"], 0)}% / ${fmt(em["CritPt"], 0)}%</td><td class="metric-value">${fmt(em["Terminal-Bench 4.0"], 0)}% / ${fmt(em["SciCode"], 0)}%</td><td class="metric-value">${fmt(em["AA-Briefcase v1.1"], 0)} / ${fmt(em["GDPval-AA v2.1"], 0)} / ${fmt(em["AutomationBench-AA"], 0)}%</td><td class="metric-value">${fmt(em["AA-LCR v1.1"], 0)}% / ${fmt(em["GDP.pdf"], 0)}% / ${fmt(em["AA-Omniscience"], 0)}</td><td class="metric-value">${money(vr.costPerTask)}<span class="task-detail">${fmt(vr.timePerTaskMinutes, 2)}m · ${fmt(vr.outputTokensPerTask, 0)} tok</span></td></tr>`;
    }).join("");
    el.innerHTML = `<div class="topline"><h3><span class="swatch" style="display:inline-block;background:${rel.color};margin-right:7px"></span>${esc(rel.name)} · 全推理档位 × 主流任务实测明细（当前档位：${esc(v.effort)}）</h3><span class="tag">${esc(rel.vendor)} · ${rel.variants.length} 个已测档位 · ${v.evalSourceUrl ? link(v.evalSourceUrl, "AA 比较页来源") : "AA v4.3.2"}</span></div><div class="numbers"><div><b>${fmt(score, taskDef.digits)}${taskDef.unit}</b><span>当前维度：${esc(taskDef.shortLabel)}</span></div><div><b>${fmt(v.intelligenceIndex, 1)}</b><span>AA 综合智力指数</span></div><div><b>${money(v.costPerTask)}</b><span>单任务加权成本</span></div><div><b>${fmt(v.timePerTaskMinutes, 2)} 分钟</b><span>每任务推算耗时（${fmt(v.outputTokensPerTask, 0)} tok）</span></div></div><div class="table-scroll" style="margin-top:10px">${table(["推理档位","当前维度得分 / 升档差分","综合指数 (II)","复杂问题：HLE / CritPt","编程工程：Terminal / SciCode","规划与代理：Briefcase / GDPval / AutoBench","知识与文档：LCR / PDF / Omniscience","单任务成本 / 耗时 / 输出 Token"], rowsHtml)}</div>`;
  }

  function renderTaskEffortChart() {
    const ser = DATA.aa_release_series;
    const svg = $("taskEffortChart");
    if (!ser || !svg) return;
    const taskDef = TASK_DEFINITIONS[taskEffortState.tab] || TASK_DEFINITIONS.complex;
    const mode = $("taskEffortMode") ? $("taskEffortMode").value : "release_trajectories";
    const focusEffort = $("taskEffortFocus") ? $("taskEffortFocus").value : "all";
    const colorMode = $("taskColorMode") ? $("taskColorMode").value : "vendor";
    const showBackdrop = $("taskEffortBackdrop") && $("taskEffortBackdrop").checked;

    if ($("taskEffortTitle")) $("taskEffortTitle").textContent = taskDef.title;
    if ($("taskEffortSubnote")) $("taskEffortSubnote").textContent = taskDef.subnote;

    const activeReleases = ser.releases.filter(r => r.variants.some(v => v.taskScores));
    const otherReleases = showBackdrop ? ser.releases.filter(r => !r.variants.some(v => v.taskScores)) : [];
    if (!activeReleases.some(r => r.releaseSlug === taskEffortState.selectedReleaseId)) {
      taskEffortState.selectedReleaseId = activeReleases[0]?.releaseSlug || "claude-opus-5-5";
      taskEffortState.selectedVariantSlug = null;
    }

    renderAALegendBar("taskEffortLegend", {
      showQuadrant: true,
      showPareto: true,
      includeBackdropVendors: showBackdrop && taskDef.key === "intelligenceIndex",
      colorMode,
      activeReleases
    });
    renderTaskCategoryCards(taskDef, activeReleases);

    $("taskEffortPills").innerHTML = activeReleases.map(r => {
      const col = getReleaseColor(r, colorMode);
      const topV = bestTaskVariant(r, taskDef) || r.variants[r.variants.length - 1];
      const sc = taskDef.getScore(topV);
      return `<button type="button" class="pill-btn ${r.releaseSlug === taskEffortState.selectedReleaseId ? "is-active" : ""}" data-task-pill="${esc(r.releaseSlug)}"><span class="swatch" style="background:${col}"></span>${esc(r.shortName || r.name)} <span class="small">(${fmt(sc, taskDef.digits)}${taskDef.unit})</span></button>`;
    }).join("");
    $("taskEffortPills").querySelectorAll("[data-task-pill]").forEach(btn => btn.addEventListener("click", () => {
      taskEffortState.selectedReleaseId = btn.dataset.taskPill;
      taskEffortState.selectedVariantSlug = null;
      renderTaskEffortChart();
    }));

    const variantMatchesFocus = (v, rel) => {
      if (focusEffort === "all") return mode === "top_variants" ? v === bestTaskVariant(rel, taskDef) : true;
      return v.effort === focusEffort;
    };

    const plottedActive = activeReleases.flatMap(rel =>
      rel.variants
        .filter(v => variantMatchesFocus(v, rel) && finite(v.costPerTask) && v.costPerTask > 0 && finite(taskDef.getScore(v)))
        .map(v => ({rel, v, score:taskDef.getScore(v)}))
    );
    const backdropMarket = (showBackdrop && taskDef.key === "intelligenceIndex")
      ? otherReleases.flatMap(rel =>
          rel.variants
            .filter(v => (mode === "top_variants" ? v.isTopVariant : true) && finite(v.costPerTask) && v.costPerTask > 0 && finite(taskDef.getScore(v)))
            .map(v => ({rel, v, score:taskDef.getScore(v)}))
        )
      : [];

    const frontierPool = [...plottedActive, ...backdropMarket];
    const frontier = frontierPool
      .filter(p => !frontierPool.some(o => o.v.costPerTask <= p.v.costPerTask && o.score >= p.score && (o.v.costPerTask < p.v.costPerTask || o.score > p.score)))
      .sort((a,b) => a.v.costPerTask - b.v.costPerTask);

    if ($("taskEffortCount")) {
      $("taskEffortCount").textContent = `${activeReleases.length} 款四大家族活跃模型 · 当前显示 ${plottedActive.length} 个档位点${backdropMarket.length ? ` + ${backdropMarket.length} 个市场参照点` : ""} · 帕累托前沿 ${frontier.length} 个节点`;
    }

    const width = Math.max(720, Math.round(svg.getBoundingClientRect().width || 1100));
    const height = width < 640 ? 430 : 500, margin = {left:64, right:148, top:36, bottom:62};
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("height", height);

    const allForScale = activeReleases.flatMap(r => r.variants.filter(v => finite(v.costPerTask) && v.costPerTask > 0));
    const xs = [...allForScale, ...backdropMarket.map(p => p.v)].map(v => v.costPerTask);
    const lo = Math.min(0.0035, Math.min(...xs) * 0.8);
    const hi = Math.max(12, Math.max(...xs) * 1.25);
    const x = val => margin.left + (Math.log(val / lo) / Math.log(hi / lo)) * (width - margin.left - margin.right);
    const [ymin, ymax] = taskDef.yrange;
    const y = val => height - margin.bottom - ((val - ymin) / (ymax - ymin)) * (height - margin.top - margin.bottom);

    const parts = [`<title>${esc(taskDef.title)}</title>`];
    drawAAPlotChrome(parts, {
      width,
      height,
      margin,
      qx: x(taskDef.attractiveX),
      qy: y(taskDef.attractiveY),
      showQuadrant: true
    });

    taskDef.yTicks.forEach(t => {
      if (t >= ymin && t <= ymax) {
        parts.push(`<line x1="${margin.left}" x2="${width - margin.right}" y1="${y(t)}" y2="${y(t)}" stroke="#e5ebe3"/><text x="${margin.left - 10}" y="${y(t) + 4}" text-anchor="end" class="tick">${t}${taskDef.unit === "%" ? "%" : ""}</text>`);
      }
    });
    const xTicks = [0.005, 0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10];
    xTicks.filter(t => t >= lo && t <= hi).forEach(t => {
      const tx = x(t);
      const label = "$" + (t < 0.01 ? t.toFixed(3) : t < 1 ? t.toFixed(2) : t === 2.5 ? "2.5" : t.toFixed(0));
      parts.push(`<line x1="${tx}" x2="${tx}" y1="${margin.top}" y2="${height - margin.bottom}" stroke="#eef2ec" stroke-dasharray="3 3"/><text x="${tx}" y="${height - margin.bottom + 22}" text-anchor="middle" class="tick">${esc(label)}</text>`);
    });
    parts.push(`<text x="${margin.left}" y="20" class="axis-label">${esc(taskDef.yLabel)}</text>`);
    parts.push(`<text x="${(margin.left + width - margin.right) / 2}" y="${height - 12}" text-anchor="middle" class="axis-label">Cost per Task (USD, log scale · AA v4.3.2 单任务加权成本)</text>`);

    // Backdrop market models (when intelligenceIndex is active) or faint full trajectories (when a single effort is focused)
    if (showBackdrop && taskDef.key === "intelligenceIndex") {
      otherReleases.forEach(rel => {
        const col = getReleaseColor(rel, colorMode);
        const pts = rel.variants.filter(v => (mode === "top_variants" ? v.isTopVariant : true) && finite(v.costPerTask) && v.costPerTask > 0 && finite(v.intelligenceIndex));
        if (mode === "release_trajectories" && pts.length > 1) {
          parts.push(`<polyline points="${pts.map(v => `${x(v.costPerTask)},${y(v.intelligenceIndex)}`).join(" ")}" fill="none" stroke="${col}" stroke-width="1.2" opacity="0.28"/>`);
        }
        pts.forEach(v => {
          parts.push(`<circle cx="${x(v.costPerTask)}" cy="${y(v.intelligenceIndex)}" r="3.6" fill="${col}" opacity="0.42"><title>${esc(v.name + " · " + fmt(v.intelligenceIndex, 1) + " · " + money(v.costPerTask))}</title></circle>`);
        });
      });
    } else if (showBackdrop && focusEffort !== "all") {
      activeReleases.forEach(rel => {
        const col = getReleaseColor(rel, colorMode);
        const pts = rel.variants.filter(v => finite(v.costPerTask) && v.costPerTask > 0 && finite(taskDef.getScore(v)));
        if (pts.length > 1) {
          parts.push(`<polyline points="${pts.map(v => `${x(v.costPerTask)},${y(taskDef.getScore(v))}`).join(" ")}" fill="none" stroke="${col}" stroke-width="1.2" stroke-dasharray="2 2" opacity="0.25"/>`);
        }
      });
    }

    if (frontier.length > 1) {
      parts.push(`<polyline points="${frontier.map(p => `${x(p.v.costPerTask)},${y(p.score)}`).join(" ")}" fill="none" stroke="#111827" stroke-width="2.1" stroke-dasharray="2.5 3.5"/>`);
    }

    const topLabels = [];
    const orderedReleases = [...activeReleases].sort((a,b) => (a.releaseSlug === taskEffortState.selectedReleaseId ? 1 : b.releaseSlug === taskEffortState.selectedReleaseId ? -1 : 0));
    orderedReleases.forEach(rel => {
      const isSel = rel.releaseSlug === taskEffortState.selectedReleaseId;
      const col = getReleaseColor(rel, colorMode);
      const pts = rel.variants
        .filter(v => variantMatchesFocus(v, rel) && finite(v.costPerTask) && v.costPerTask > 0 && finite(taskDef.getScore(v)))
        .map(v => ({v, score:taskDef.getScore(v)}));
      if (!pts.length) return;
      const poly = pts.length > 1
        ? `<polyline class="release-line" points="${pts.map(p => `${x(p.v.costPerTask)},${y(p.score)}`).join(" ")}" fill="none" stroke="${col}" stroke-width="${isSel ? 3.2 : 2.1}" opacity="${isSel ? 1 : 0.82}"/>`
        : "";
      const dots = pts.map(p => {
        const cx = x(p.v.costPerTask), cy = y(p.score);
        const isPrimary = p.v === bestTaskVariant(rel, taskDef) || pts.length === 1;
        const r = isPrimary ? (isSel ? 6.8 : 5.6) : (isSel ? 5.2 : 4.3);
        const effTag = isSel && pts.length > 1 ? `<text x="${cx}" y="${cy - r - 4}" text-anchor="middle" font-size="9.5" font-weight="600" fill="${col}">${esc(EFFORT_SHORT[p.v.effort] || p.v.effort)}</text>` : "";
        return `<g class="task-dot" tabindex="0" role="button" data-task-rel="${esc(rel.releaseSlug)}" data-task-var="${esc(p.v.slug)}" aria-label="${esc(p.v.name + "，" + taskDef.shortLabel + " " + fmt(p.score, taskDef.digits) + taskDef.unit + "，成本 " + money(p.v.costPerTask))}"><title>${esc(p.v.name + " · " + taskDef.shortLabel + " " + fmt(p.score, taskDef.digits) + taskDef.unit + " · 单任务 " + money(p.v.costPerTask) + " · 耗时 " + fmt(p.v.timePerTaskMinutes, 2) + "m")}</title><circle cx="${cx}" cy="${cy}" r="${r}" fill="${isPrimary ? col : "#ffffff"}" stroke="${col}" stroke-width="${isPrimary ? 2.2 : 1.9}"/>${effTag}</g>`;
      }).join("");
      parts.push(`<g class="release-series ${isSel ? "is-highlighted" : ""}">${poly}${dots}</g>`);
      const labelPt = [...pts].sort((a,b) => b.score - a.score || a.v.costPerTask - b.v.costPerTask)[0];
      const suffix = focusEffort !== "all" ? ` (${labelPt.v.effort})` : "";
      topLabels.push({rel, col, v:labelPt.v, score:labelPt.score, text:(rel.shortName || rel.name) + suffix, cx:x(labelPt.v.costPerTask), cy:y(labelPt.score), ly:y(labelPt.score), isSel});
    });

    renderSmartLabels(parts, topLabels, {width, height, margin, minGap:15, xSpan:135});

    svg.innerHTML = parts.join("");
    svg.querySelectorAll(".task-dot").forEach(dot => {
      const select = () => {
        taskEffortState.selectedReleaseId = dot.dataset.taskRel;
        taskEffortState.selectedVariantSlug = dot.dataset.taskVar;
        renderTaskEffortChart();
      };
      dot.addEventListener("click", select);
      dot.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(); } });
    });

    const selRel = activeReleases.find(r => r.releaseSlug === taskEffortState.selectedReleaseId) || activeReleases[0];
    const selVar = selRel?.variants.find(v => v.slug === taskEffortState.selectedVariantSlug) || (selRel && bestTaskVariant(selRel, taskDef)) || selRel?.variants[selRel.variants.length - 1];
    renderTaskEffortDetail(selRel, selVar, taskDef);
  }

  if ($("taskEffortTabs")) {
    $("taskEffortTabs").querySelectorAll("[data-task-tab]").forEach(btn => btn.addEventListener("click", () => {
      taskEffortState.tab = btn.dataset.taskTab;
      $("taskEffortTabs").querySelectorAll("[data-task-tab]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.taskTab === taskEffortState.tab)));
      renderTaskEffortChart();
    }));
    ["taskEffortMode", "taskEffortFocus", "taskColorMode", "taskEffortBackdrop"].forEach(id => $(id)?.addEventListener("change", renderTaskEffortChart));
    $("exportTaskEffort")?.addEventListener("click", () => {
      const rows = DATA.aa_release_series.releases.filter(r => r.variants.some(v => v.taskScores)).flatMap(r => r.variants.map(v => ({
        release: r.name,
        vendor: r.vendor,
        variant: v.name,
        effort: v.effort,
        is_top_variant: v.isTopVariant,
        intelligence_index: v.intelligenceIndex,
        complex_problem_solving: v.taskScores?.complex,
        coding_software_eng: v.taskScores?.coding,
        planning_briefcase_elo: v.taskScores?.planning,
        agentic_gdpval_elo: v.taskScores?.agentic,
        automation_bench_pct: v.taskScores?.automation,
        knowledge_doc_score: v.taskScores?.knowledge,
        hle_pct: v.evalMetrics?.["Humanity's Last Exam"],
        critpt_pct: v.evalMetrics?.["CritPt"],
        terminal_bench_pct: v.evalMetrics?.["Terminal-Bench 4.0"],
        scicode_pct: v.evalMetrics?.["SciCode"],
        aa_lcr_pct: v.evalMetrics?.["AA-LCR v1.1"],
        gdp_pdf_pct: v.evalMetrics?.["GDP.pdf"],
        aa_omniscience: v.evalMetrics?.["AA-Omniscience"],
        cost_per_task_usd: v.costPerTask,
        time_per_task_minutes: v.timePerTaskMinutes,
        output_tokens_per_task: v.outputTokensPerTask,
        source_url: v.evalSourceUrl
      })));
      exportCSV(rows, `四大家族任务与推理档位全量评测-${taskEffortState.tab}-2026-10-20.csv`);
    });
  }

  // 4. Reasoning Effort Scaling Slopes & Heatmap Matrix (#capabilities -> #effortScalingCard)
  let scalingSelectedSlug = "claude-opus-5-5";
  function renderEffortScalingChart() {
    const ser = DATA.aa_release_series;
    const svg = $("effortScalingChart");
    if (!ser || !svg) return;
    const taskKey = $("effortScalingTask") ? $("effortScalingTask").value : "complex";
    const fam = $("effortScalingFamily") ? $("effortScalingFamily").value : "all";
    const taskDef = TASK_DEFINITIONS[taskKey] || TASK_DEFINITIONS.complex;

    const allActive = ser.releases.filter(r => r.variants.some(v => v.taskScores));
    const shown = allActive.filter(r => fam === "all" || r.vendor === fam);
    if (!shown.some(r => r.releaseSlug === scalingSelectedSlug)) {
      scalingSelectedSlug = shown[0]?.releaseSlug || "claude-opus-5-5";
    }

    renderAALegendBar("effortScalingLegend", {
      showQuadrant: false,
      showPareto: false,
      includeBackdropVendors: false,
      colorMode: "model",
      activeReleases: shown
    });

    const width = Math.max(720, Math.round(svg.getBoundingClientRect().width || 1100));
    const height = width < 640 ? 390 : 440, margin = {left:64, right:150, top:34, bottom:56};
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("height", height);

    const x = idx => margin.left + (idx / (EFFORT_ORDER.length - 1)) * (width - margin.left - margin.right);
    const [ymin, ymax] = taskDef.yrange;
    const y = val => height - margin.bottom - ((val - ymin) / (ymax - ymin)) * (height - margin.top - margin.bottom);

    const parts = [`<title>${esc(taskDef.shortLabel)} 推理档位升档曲线</title>`];
    parts.push(`<rect x="${margin.left}" y="${margin.top}" width="${width - margin.left - margin.right}" height="${height - margin.top - margin.bottom}" fill="#ffffff" stroke="#d5dfd9"/>`);
    taskDef.yTicks.forEach(t => {
      if (t >= ymin && t <= ymax) {
        parts.push(`<line x1="${margin.left}" x2="${width - margin.right}" y1="${y(t)}" y2="${y(t)}" stroke="#e5ebe3"/><text x="${margin.left - 10}" y="${y(t) + 4}" text-anchor="end" class="tick">${t}${taskDef.unit === "%" ? "%" : ""}</text>`);
      }
    });
    EFFORT_ORDER.forEach((eff, idx) => {
      const tx = x(idx);
      parts.push(`<line x1="${tx}" x2="${tx}" y1="${margin.top}" y2="${height - margin.bottom}" stroke="#edf1eb" stroke-dasharray="3 3"/><text x="${tx}" y="${height - margin.bottom + 22}" text-anchor="middle" class="tick" font-weight="600">${esc(eff)}</text>`);
    });
    parts.push(`<text x="${margin.left}" y="19" class="axis-label">${esc(taskDef.yLabel)}</text>`);
    parts.push(`<text x="${(margin.left + width - margin.right) / 2}" y="${height - 10}" text-anchor="middle" class="axis-label">推理档位（Reasoning Effort Level：non-reasoning → max）</text>`);

    const endLabels = [];
    const ordered = [...shown].sort((a,b) => (a.releaseSlug === scalingSelectedSlug ? 1 : b.releaseSlug === scalingSelectedSlug ? -1 : 0));
    ordered.forEach(rel => {
      const isSel = rel.releaseSlug === scalingSelectedSlug;
      const pts = rel.variants
        .map(v => ({v, idx:EFFORT_ORDER.indexOf(v.effort), score:taskDef.getScore(v)}))
        .filter(p => p.idx >= 0 && finite(p.score))
        .sort((a,b) => a.idx - b.idx);
      if (!pts.length) return;
      const poly = pts.length > 1
        ? `<polyline points="${pts.map(p => `${x(p.idx)},${y(p.score)}`).join(" ")}" fill="none" stroke="${rel.color}" stroke-width="${isSel ? 3.4 : 2.1}" opacity="${isSel ? 1 : 0.78}"/>`
        : "";
      const dots = pts.map(p => {
        const cx = x(p.idx), cy = y(p.score);
        return `<g class="scaling-dot" tabindex="0" role="button" data-scale-rel="${esc(rel.releaseSlug)}" aria-label="${esc(rel.name + " " + p.v.effort + " " + fmt(p.score, taskDef.digits) + taskDef.unit)}"><title>${esc(rel.name + " (" + p.v.effort + ") · " + fmt(p.score, taskDef.digits) + taskDef.unit + " · " + money(p.v.costPerTask))}</title><circle cx="${cx}" cy="${cy}" r="${isSel ? 6 : 4.8}" fill="${p.v.isTopVariant ? rel.color : "#ffffff"}" stroke="${rel.color}" stroke-width="2"/><text x="${cx}" y="${cy - 8}" text-anchor="middle" font-size="10" font-weight="600" fill="${rel.color}" opacity="${isSel ? 1 : 0}" style="paint-order:stroke;stroke:#ffffff;stroke-width:3px">${fmt(p.score, taskDef.digits)}</text></g>`;
      }).join("");
      parts.push(`<g>${poly}${dots}</g>`);
      const last = pts[pts.length - 1];
      endLabels.push({rel, col:rel.color, text:`${rel.shortName || rel.name} (${fmt(last.score, taskDef.digits)})`, cx:x(last.idx), cy:y(last.score), ly:y(last.score), isSel, score:last.score});
    });

    renderSmartLabels(parts, endLabels, {width, height, margin, minGap:15, xSpan:135});
    svg.innerHTML = parts.join("");
    svg.querySelectorAll(".scaling-dot").forEach(dot => {
      const select = () => { scalingSelectedSlug = dot.dataset.scaleRel; renderEffortScalingChart(); };
      dot.addEventListener("click", select);
      dot.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(); } });
    });

    // Render 11-model × 6-effort matrix table in #effortScalingTable
    if ($("effortScalingTable")) {
      const rowsHtml = shown.map(rel => {
        const byEff = new Map(rel.variants.map(v => [v.effort, v]));
        const validScores = rel.variants.map(v => taskDef.getScore(v)).filter(finite);
        const firstSc = validScores[0], maxSc = validScores.length ? Math.max(...validScores) : null;
        const gain = finite(firstSc) && finite(maxSc) && validScores.length > 1 ? maxSc - firstSc : null;
        const cells = EFFORT_ORDER.map(eff => {
          const v = byEff.get(eff);
          if (!v || !finite(taskDef.getScore(v))) return `<td class="metric-value small" style="color:#9ca3af">未设该档</td>`;
          const sc = taskDef.getScore(v);
          const ratio = Math.max(0, Math.min(1, (sc - ymin) / (ymax - ymin)));
          const bg = `rgba(22, 163, 74, ${(0.08 + ratio * 0.24).toFixed(2)})`;
          return `<td class="metric-value heat-cell"><span class="heat-pill" style="background:${bg}">${fmt(sc, taskDef.digits)}${taskDef.unit}</span><span class="task-detail">${money(v.costPerTask)} · ${fmt(v.timePerTaskMinutes, 1)}m</span></td>`;
        }).join("");
        return `<tr class="${rel.releaseSlug === scalingSelectedSlug ? "recommended-controller" : ""}"><th><span class="swatch" style="display:inline-block;background:${rel.color};margin-right:6px"></span>${esc(rel.name)}<span class="task-detail">${esc(rel.vendor)}</span></th>${cells}<td class="metric-value ${gain !== null && gain > 0 ? "delta-positive" : ""}"><strong>${gain !== null ? (gain > 0 ? "+" : "") + fmt(gain, taskDef.digits) + (taskDef.unit === "%" ? " 个百分点" : taskDef.unit) : "单档"}</strong></td></tr>`;
      }).join("");
      $("effortScalingTable").innerHTML = table(["活跃模型系列", ...EFFORT_ORDER.map(e => `<code>${esc(e)}</code>`), "全档最大跃升"], rowsHtml);
    }
  }
  if ($("effortScalingTask")) {
    ["effortScalingTask", "effortScalingFamily"].forEach(id => $(id)?.addEventListener("change", renderEffortScalingChart));
    $("exportEffortScaling")?.addEventListener("click", () => {
      const taskKey = $("effortScalingTask").value;
      const taskDef = TASK_DEFINITIONS[taskKey] || TASK_DEFINITIONS.complex;
      const rows = DATA.aa_release_series.releases.filter(r => r.variants.some(v => v.taskScores)).map(rel => {
        const byEff = new Map(rel.variants.map(v => [v.effort, v]));
        const out = {model:rel.name, vendor:rel.vendor, task_dimension:taskDef.shortLabel};
        EFFORT_ORDER.forEach(e => {
          const v = byEff.get(e);
          out[e + "_score"] = v ? taskDef.getScore(v) : null;
          out[e + "_cost_usd"] = v ? v.costPerTask : null;
        });
        return out;
      });
      exportCSV(rows, `四大家族推理升档矩阵-${taskKey}-2026-10-20.csv`);
    });
  }

  // 5. AA By-Release Intelligence Index vs Cost/Time/Output-Token Trajectory Chart (#explorer -> #releaseChartCard)
  const RELEASE_AXES = {
    costPerTask: {label:"单任务成本（Cost per Task · USD）", unit:"USD", attractiveX:1.10},
    timePerTaskMinutes: {label:"每任务耗时（Time per Task · 分钟）", unit:"分钟", attractiveX:5.5},
    outputTokensPerTask: {label:"每任务输出 Token 数（Reasoning + Answer）", unit:"tokens", attractiveX:14000}
  };
  const releaseState = {selectedReleaseId:"claude-opus-5-5", selectedVariantId:null};
  function releaseInScope(rel, scope) {
    if (scope === "four_family_current") return rel.isFourFamily && rel.isCurrent;
    if (scope === "four_family_flagship") return rel.isFourFamily && rel.isCurrent && (rel.maxIntelligenceIndex >= 45 || rel.vendor === "xAI");
    return true;
  }
  function renderReleaseDetail(rel, focusVar) {
    if (!rel || !$("releaseDetail")) return;
    const v = focusVar || rel.variants.find(x => x.isTopVariant) || rel.variants[rel.variants.length - 1];
    const cb = v.costBreakdown || {};
    const totalCost = cb.total || v.costPerTask || 0;
    const segs = [
      ["非缓存输入", cb.nonCacheInput || 0, "#3d7a68"],
      ["缓存读取", cb.cacheRead || 0, "#7ab09a"],
      ["缓存写入", cb.cacheWrite || 0, "#b8cfbe"],
      ["思考输出 (Reasoning)", cb.reasoning || 0, "#c87d28"],
      ["答案输出 (Answer)", cb.answer || 0, "#165e54"]
    ];
    const stackBar = totalCost > 0
      ? `<div class="cost-stack">${segs.map(([label, val, col]) => val > 0 ? `<span style="width:${Math.max(1.5, (val/totalCost)*100).toFixed(1)}%;background:${col}" title="${esc(label + ": " + money(val))}"></span>` : "").join("")}</div><div class="cost-legend">${segs.map(([label, val, col]) => `<span><i style="background:${col}"></i>${esc(label)}：${money(val)}</span>`).join("")}</div>`
      : "";
    const tb = v.outputTokensBreakdown || {};
    const rowsHtml = rel.variants.map(vr => {
      const c = vr.costBreakdown || {};
      const t = vr.outputTokensBreakdown || {};
      return `<tr class="${vr.slug === v.slug ? "recommended-controller" : ""}"><th>${esc(vr.shortName)} ${vr.isTopVariant ? '<span class="badge">最高分代表点</span>' : ""}</th><td class="metric-value"><strong>${fmt(vr.intelligenceIndex,1)}</strong></td><td class="metric-value">${money(vr.costPerTask)}</td><td class="metric-value">${money(c.nonCacheInput)} / ${money(c.cacheRead)} / ${money(c.cacheWrite)}</td><td class="metric-value">${money(c.reasoning)} / ${money(c.answer)}</td><td class="metric-value">${fmt(vr.outputTokensPerTask,0)}<span class="task-detail">思考 ${fmt(t.reasoning,0)} · 答案 ${fmt(t.answer,0)}</span></td><td class="metric-value">${fmt(vr.timePerTaskMinutes,2)} 分<span class="task-detail">吞吐 ${fmt(vr.outputSpeed,0)} tok/s · TTFA ${fmt(vr.ttfaSeconds,1)}s</span></td></tr>`;
    }).join("");
    $("releaseDetail").innerHTML = `<div class="topline"><h3><span class="swatch" style="display:inline-block;background:${rel.color};margin-right:7px"></span>${esc(rel.name)}（当前选中档位：${esc(v.effort)}）</h3><span class="tag">${esc(rel.vendor)} · 共 ${rel.variants.length} 个档位点 · 发布 ${esc(rel.releaseDate || "2026")}</span></div><div class="numbers"><div><b>${fmt(v.intelligenceIndex,1)}</b><span>Intelligence Index</span></div><div><b>${money(v.costPerTask)}</b><span>单任务总成本</span></div><div><b>${fmt(v.timePerTaskMinutes,2)} 分钟</b><span>每任务平均耗时</span></div><div><b>${fmt(v.outputTokensPerTask,0)}</b><span>每任务输出 Token（思考 ${fmt(tb.reasoning,0)}）</span></div></div>${stackBar}<div class="table-scroll" style="margin-top:10px">${table(["同版本已测档位","Intelligence Index","单任务总成本","输入拆分：非缓存 / 缓存读 / 缓存写","输出拆分：思考 / 答案","每任务输出 Token","每任务耗时 / 吞吐"], rowsHtml)}</div>`;
  }
  function renderReleaseChart() {
    const ser = DATA.aa_release_series;
    const svg = $("releaseChart");
    if (!ser || !svg) return;
    const xKey = $("releaseXMetric") ? $("releaseXMetric").value : "costPerTask";
    const scope = $("releaseScope") ? $("releaseScope").value : "four_family_current";
    const viewMode = $("releaseViewMode") ? $("releaseViewMode").value : "trajectories";
    const colorMode = $("releaseColorMode") ? $("releaseColorMode").value : "vendor";
    const showPareto = $("releasePareto") && $("releasePareto").checked;
    const showBackdrop = $("releaseBackdrop") && $("releaseBackdrop").checked;
    const xMeta = RELEASE_AXES[xKey] || RELEASE_AXES.costPerTask;

    const activeReleases = ser.releases.filter(r => releaseInScope(r, scope));
    const backdropReleases = showBackdrop ? ser.releases.filter(r => !releaseInScope(r, scope)) : [];
    if (!activeReleases.some(r => r.releaseSlug === releaseState.selectedReleaseId)) {
      releaseState.selectedReleaseId = activeReleases[0]?.releaseSlug || ser.releases[0]?.releaseSlug;
      releaseState.selectedVariantId = null;
    }

    renderAALegendBar("releaseLegendBar", {
      showQuadrant: showPareto,
      showPareto: showPareto,
      includeBackdropVendors: showBackdrop || scope === "all_releases",
      colorMode,
      activeReleases
    });

    $("releasePills").innerHTML = activeReleases.map(r => {
      const col = getReleaseColor(r, colorMode);
      return `<button type="button" class="pill-btn ${r.releaseSlug === releaseState.selectedReleaseId ? "is-active" : ""}" data-rel-pill="${esc(r.releaseSlug)}"><span class="swatch" style="background:${col}"></span>${esc(r.shortName || r.name)} <span class="small">(${r.variants.length}档)</span></button>`;
    }).join("");
    $("releasePills").querySelectorAll("[data-rel-pill]").forEach(btn => btn.addEventListener("click", () => {
      releaseState.selectedReleaseId = btn.dataset.relPill;
      releaseState.selectedVariantId = null;
      renderReleaseChart();
    }));

    const filterVars = rel => rel.variants.filter(v => (viewMode === "top_only" ? v.isTopVariant : true) && finite(v[xKey]) && v[xKey] > 0 && finite(v.intelligenceIndex));
    const activePoints = activeReleases.flatMap(r => filterVars(r).map(v => ({rel:r, v})));
    const backdropPoints = backdropReleases.flatMap(r => filterVars(r).map(v => ({rel:r, v})));
    const allPoints = [...activePoints, ...backdropPoints];
    const frontier = activePoints
      .filter(p => !activePoints.some(o => o.v[xKey] <= p.v[xKey] && o.v.intelligenceIndex >= p.v.intelligenceIndex && (o.v[xKey] < p.v[xKey] || o.v.intelligenceIndex > p.v.intelligenceIndex)))
      .sort((a,b) => a.v[xKey] - b.v[xKey]);

    if ($("releaseCount")) $("releaseCount").textContent = `${activeReleases.length} 个模型发布版本 · ${activePoints.length} 个推理档位点${backdropPoints.length ? `（另含 ${backdropPoints.length} 个市场参照点）` : ""} · ${viewMode === "top_only" ? "仅展示各发布版本最高分代表档" : "同色实线连接同一发布版本的不同推理投入档位"}`;

    const width = Math.max(720, Math.round(svg.getBoundingClientRect().width || 1100));
    const height = width < 640 ? 420 : 490, margin = {left:58, right:142, top:34, bottom:62};
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("height", height);
    if (!allPoints.length) return;

    const xs = allPoints.map(p => p.v[xKey]);
    let lo = Math.min(...xs) * 0.82, hi = Math.max(...xs) * 1.22;
    const x = val => margin.left + (Math.log(val / lo) / Math.log(hi / lo)) * (width - margin.left - margin.right);
    const ymin = 14, ymax = 64;
    const y = val => height - margin.bottom - ((val - ymin) / (ymax - ymin)) * (height - margin.top - margin.bottom);

    const parts = [`<title>按模型发布版本划分的 Intelligence Index 与 ${esc(xMeta.label)}</title>`];
    drawAAPlotChrome(parts, {
      width,
      height,
      margin,
      qx: x(xMeta.attractiveX),
      qy: y(42.5),
      showQuadrant: showPareto
    });

    for (let s = 20; s <= 60; s += 10) {
      parts.push(`<line x1="${margin.left}" x2="${width - margin.right}" y1="${y(s)}" y2="${y(s)}" stroke="#e3e9e1"/><text x="${margin.left - 10}" y="${y(s) + 4}" text-anchor="end" class="tick">${s}</text>`);
    }
    const tickCandidates = xKey === "costPerTask" ? [0.005,0.01,0.02,0.05,0.1,0.25,0.5,1,2.5,5,10,20] : xKey === "timePerTaskMinutes" ? [0.2,0.5,1,2,5,10,20,40] : [500,1000,2500,5000,10000,25000,50000,100000];
    tickCandidates.filter(t => t >= lo && t <= hi).forEach(t => {
      const tx = x(t);
      const label = xKey === "costPerTask" ? "$" + (t < 0.01 ? t.toFixed(3) : t < 1 ? t.toFixed(2) : t.toFixed(t === 2.5 ? 2 : 0)) : xKey === "timePerTaskMinutes" ? t + "m" : (t >= 1000 ? (t/1000) + "k" : String(t));
      parts.push(`<line x1="${tx}" x2="${tx}" y1="${margin.top}" y2="${height - margin.bottom}" stroke="#edf1eb" stroke-dasharray="3 3"/><text x="${tx}" y="${height - margin.bottom + 22}" text-anchor="middle" class="tick">${esc(label)}</text>`);
    });
    parts.push(`<text x="${margin.left}" y="18" class="axis-label">AA Intelligence Index（分）</text><text x="${(margin.left + width - margin.right)/2}" y="${height - 12}" text-anchor="middle" class="axis-label">${esc(xMeta.label)} · 对数刻度</text>`);

    backdropReleases.forEach(rel => {
      const col = getReleaseColor(rel, colorMode);
      const pts = filterVars(rel);
      if (viewMode === "trajectories" && pts.length > 1) {
        parts.push(`<polyline points="${pts.map(v => `${x(v[xKey])},${y(v.intelligenceIndex)}`).join(" ")}" fill="none" stroke="${col}" stroke-width="1.3" opacity="0.28"/>`);
      }
      pts.forEach(v => {
        parts.push(`<circle cx="${x(v[xKey])}" cy="${y(v.intelligenceIndex)}" r="3.6" fill="${col}" opacity="0.42"><title>${esc(v.name + " · II " + fmt(v.intelligenceIndex,1) + " · " + fmt(v[xKey],3))}</title></circle>`);
      });
    });

    if (showPareto && frontier.length > 1) {
      parts.push(`<polyline points="${frontier.map(p => `${x(p.v[xKey])},${y(p.v.intelligenceIndex)}`).join(" ")}" fill="none" stroke="#111827" stroke-width="2.1" stroke-dasharray="2.5 3.5"/>`);
    }

    const topLabels = [];
    const orderedReleases = [...activeReleases].sort((a,b) => (a.releaseSlug === releaseState.selectedReleaseId ? 1 : b.releaseSlug === releaseState.selectedReleaseId ? -1 : 0));
    orderedReleases.forEach(rel => {
      const isSel = rel.releaseSlug === releaseState.selectedReleaseId;
      const col = getReleaseColor(rel, colorMode);
      const pts = filterVars(rel);
      if (!pts.length) return;
      const poly = (viewMode === "trajectories" && pts.length > 1)
        ? `<polyline class="release-line" points="${pts.map(v => `${x(v[xKey])},${y(v.intelligenceIndex)}`).join(" ")}" fill="none" stroke="${col}" stroke-width="${isSel ? 3.2 : 2.1}" opacity="${isSel ? 1 : 0.8}"/>`
        : "";
      const dots = pts.map(v => {
        const cx = x(v[xKey]), cy = y(v.intelligenceIndex);
        const r = v.isTopVariant ? (isSel ? 6.8 : 5.6) : (isSel ? 5.0 : 4.2);
        return `<g class="release-dot" tabindex="0" role="button" data-rel-id="${esc(rel.releaseSlug)}" data-var-id="${esc(v.slug)}" aria-label="${esc(v.name + "，II " + fmt(v.intelligenceIndex,1))}"><title>${esc(v.name + " · II " + fmt(v.intelligenceIndex,1) + " · 单任务 " + money(v.costPerTask) + " · 耗时 " + fmt(v.timePerTaskMinutes,2) + "m")}</title><circle cx="${cx}" cy="${cy}" r="${r}" fill="${v.isTopVariant ? col : "#ffffff"}" stroke="${col}" stroke-width="${v.isTopVariant ? 2.2 : 1.8}"/></g>`;
      }).join("");
      parts.push(`<g class="release-series ${isSel ? "is-highlighted" : ""}">${poly}${dots}</g>`);
      const topV = pts.find(v => v.isTopVariant) || pts[pts.length - 1];
      topLabels.push({rel, col, v:topV, text:rel.shortName || rel.name, cx:x(topV[xKey]), cy:y(topV.intelligenceIndex), ly:y(topV.intelligenceIndex), isSel});
    });

    renderSmartLabels(parts, topLabels, {width, height, margin, minGap:15, xSpan:135});

    svg.innerHTML = parts.join("");
    svg.querySelectorAll(".release-dot").forEach(dot => {
      const select = () => {
        releaseState.selectedReleaseId = dot.dataset.relId;
        releaseState.selectedVariantId = dot.dataset.varId;
        renderReleaseChart();
      };
      dot.addEventListener("click", select);
      dot.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(); } });
    });

    const selRel = activeReleases.find(r => r.releaseSlug === releaseState.selectedReleaseId) || activeReleases[0];
    const selVar = selRel?.variants.find(v => v.slug === releaseState.selectedVariantId) || selRel?.variants.find(v => v.isTopVariant) || selRel?.variants[0];
    renderReleaseDetail(selRel, selVar);
  }
  if ($("releaseXMetric")) {
    ["releaseXMetric","releaseScope","releaseViewMode","releaseColorMode","releasePareto","releaseBackdrop"].forEach(id => $(id)?.addEventListener("change", renderReleaseChart));
    $("exportReleases").addEventListener("click", () => {
      const scope = $("releaseScope").value;
      const rows = DATA.aa_release_series.releases.filter(r => releaseInScope(r, scope)).flatMap(r => r.variants.map(v => ({
        release_id:r.releaseSlug,
        release_name:r.name,
        vendor:r.vendor,
        variant_id:v.slug,
        variant_name:v.name,
        effort:v.effort,
        is_top_variant:v.isTopVariant,
        intelligence_index:v.intelligenceIndex,
        cost_per_task_usd:v.costPerTask,
        cost_non_cache_input_usd:v.costBreakdown?.nonCacheInput,
        cost_cache_read_usd:v.costBreakdown?.cacheRead,
        cost_cache_write_usd:v.costBreakdown?.cacheWrite,
        cost_reasoning_usd:v.costBreakdown?.reasoning,
        cost_answer_usd:v.costBreakdown?.answer,
        time_per_task_minutes:v.timePerTaskMinutes,
        output_tokens_per_task:v.outputTokensPerTask,
        reasoning_tokens_per_task:v.outputTokensBreakdown?.reasoning,
        answer_tokens_per_task:v.outputTokensBreakdown?.answer,
        output_speed_tok_s:v.outputSpeed,
        ttfa_seconds:v.ttfaSeconds
      })));
      exportCSV(rows, `AA发布版本成本轨迹-${scope}-2026-10-20.csv`);
    });
  }

  const types=[...new Set(DATA.sources.map(s => s.type))];
  $("sourceList").innerHTML=types.map(type => `<div class="source-group"><h3>${esc(type)}</h3>${DATA.sources.filter(s => s.type === type).map(s => `<div class="source-item"><span class="source-id">${s.id}</span><div>${link(s.url,s.title)}<p>${esc(s.note)}</p><p>${esc(s.status)} · ${s.accessed}</p></div></div>`).join("")}</div>`).join("");
  $("integrityNote").textContent=`原记录 ${DATA.meta.original_rows} 条＋新增 ${DATA.rows.length-DATA.meta.original_rows} 条＝${DATA.rows.length} 条；AA分项 ${DATA.aa_profiles.length} 个配置。ToneBench SHA256：${DATA.meta.tonebench_sha256}`;
  renderReasoningCharts();renderTaskEffortChart();renderEffortScalingChart();renderPanorama();renderClaudeCatalog();renderProfiles();renderCapIndexChart();renderSpecs();renderDeltas();changeGroup("general");showPanel(location.hash.slice(1)||"overview",false);
})();
