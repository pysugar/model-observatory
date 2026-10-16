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
      return `<tr><th scope="row">${link(m.source,m.short)}<span class="task-detail">${esc(m.lifecycle)}${m.screenshot_visible ? " · 截图可见" : " · 截图未显示"}</span>${m.lifecycle === "Deprecated" ? '<span class="evidence-badge">11-30 退役</span>' : ""}${m.short === "Fable 5" ? '<span class="evidence-badge">需 usage credits</span>' : ""}</th><td data-label="推理控制 / API 默认">${esc(m.efforts)}<span class="task-detail">默认：${esc(m.default_effort)}</span></td><td data-label="编码起步 / 依据"><strong>${esc(advice.start)}</strong><span class="task-detail">${esc(advice.basis)}</span></td><td data-label="保留、升档或换模型条件">${esc(advice.upgrade)}</td><td data-label="本报告证据">AA：${coverage.aa_url ? link(coverage.aa_url,coverage.aa) : coverage.aa}<span class="task-detail">英文写作：${coverage.writing ? coverage.writing+" 个配置" : "缺测"}<br>Vulcan v4：${coverage.coding ? coverage.coding+" 个配置" : "缺同版数据"}</span><button class="inline-button" data-claude-reasoning="${esc(m.name)}">查看档位证据 →</button></td></tr>`;
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
    if (name === "explorer") renderExplorer();
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
    for (let i=0;i<=5;i++) {const v = ymin+(ymax-ymin)*i/5; parts.push(`<line x1="${margin.left}" x2="${width-margin.right}" y1="${y(v)}" y2="${y(v)}" stroke="#e1e7de"/><text x="${margin.left-10}" y="${y(v)+4}" text-anchor="end" class="tick">${fmt(v,1)}</text>`);}
    const ticks = width < 600 ? 4 : 6;
    for (let i=0;i<ticks;i++) {const v = log ? lo*(hi/lo)**(i/(ticks-1)) : lo+(hi-lo)*i/(ticks-1); parts.push(`<text x="${x(v)}" y="${height-margin.bottom+23}" text-anchor="middle" class="tick">${fmt(v,v < 1 ? 3 : v < 10 ? 2 : 0)}</text>`);}
    parts.push(`<text x="${margin.left}" y="16" class="axis-label">${esc(meta.y)}</text><text x="${width/2}" y="${height-13}" text-anchor="middle" class="axis-label">${esc(meta.axes.find(a => a[0] === key)[1])}${log ? " · 对数刻度" : ""}</text>`);
    for (const name of state.models) {
      const line = plotted.filter(r => r.model === name && r.connect && pureVariant(r)).sort((a,b) => order.indexOf(a.effort)-order.indexOf(b.effort));
      if (line.length > 1) parts.push(`<polyline points="${line.map(r => `${x(r[key])},${y(r.score)}`).join(" ")}" fill="none" stroke="${modelMap.get(name).color}" stroke-width="1.1" opacity=".23"/>`);
    }
    if ($("pareto").checked && frontier.length > 1) parts.push(`<polyline points="${frontier.map(r => `${x(r[key])},${y(r.score)}`).join(" ")}" fill="none" stroke="#56695f" stroke-width="1.8" stroke-dasharray="5 5"/>`);
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
  window.addEventListener("resize",() => {clearTimeout(resizeTimer);resizeTimer=setTimeout(() => {if(!$("explorer").hidden)renderExplorer();},120);});

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
  const types=[...new Set(DATA.sources.map(s => s.type))];
  $("sourceList").innerHTML=types.map(type => `<div class="source-group"><h3>${esc(type)}</h3>${DATA.sources.filter(s => s.type === type).map(s => `<div class="source-item"><span class="source-id">${s.id}</span><div>${link(s.url,s.title)}<p>${esc(s.note)}</p><p>${esc(s.status)} · ${s.accessed}</p></div></div>`).join("")}</div>`).join("");
  $("integrityNote").textContent=`原记录 ${DATA.meta.original_rows} 条＋新增 ${DATA.rows.length-DATA.meta.original_rows} 条＝${DATA.rows.length} 条；AA分项 ${DATA.aa_profiles.length} 个配置。ToneBench SHA256：${DATA.meta.tonebench_sha256}`;
  renderClaudeCatalog();renderProfiles();renderSpecs();renderDeltas();changeGroup("general");showPanel(location.hash.slice(1)||"overview",false);
})();
