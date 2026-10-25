"use strict";
(() => {
  const DATA = JSON.parse(document.getElementById("report-data").textContent);
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const finite = value => typeof value === "number" && Number.isFinite(value);
  const fmt = (value, digits = 2) => finite(value) ? value.toLocaleString("en-US", {maximumFractionDigits:digits}) : "未提供";
  const money = value => finite(value) ? "$" + fmt(value, value < 1 ? 4 : 2) : "未提供";
  const medianOf = arr => { const a = arr.filter(finite).sort((p,q) => p-q), m = Math.floor(a.length/2); return a.length ? (a.length % 2 ? a[m] : (a[m-1]+a[m])/2) : NaN; };
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
  // Presentation-only export names; immutable evidence and calculation keys stay unchanged.
  const csvHeader = key => ({
    aa_ii:"AA 智能指数", intelligence_index:"AA 智能指数", "Intelligence Index":"AA 智能指数",
    "Cost to Run Intelligence Index":"运行 AA 智能指数费用", representative_by_overall_ii:"AA 智能指数最高代表档",
    __ii___score:"AA 智能指数_分数", __ii___status:"AA 智能指数_数据状态",
    __ii___view_rank:"AA 智能指数_当前排名", __ii___valid_n:"AA 智能指数_有效配置数",
    __ii___aa_global_rank:"AA 智能指数_来源全球排名"
  }[key] || key);
  const exportCSV = (rows, name) => {
    const fields = [...new Set(rows.flatMap(row => Object.keys(row)))];
    const cell = value => '"' + String(value == null ? "" : typeof value === "object" ? JSON.stringify(value) : value === "__ii__" ? "AA 智能指数" : value).replaceAll('"','""') + '"';
    const contents = "\uFEFF" + [fields.map(k=>cell(csvHeader(k))).join(","), ...rows.map(row => fields.map(k => cell(row[k])).join(","))].join("\r\n");
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
      return `<tr><th scope="row">${link(m.source,m.short)}<span class="task-detail">${esc(m.lifecycle)}${m.screenshot_visible ? " · 客户端常见" : " · 扩展目录"}</span>${m.lifecycle === "Deprecated" ? '<span class="evidence-badge">11-30 退役</span>' : ""}${m.short === "Fable 5" ? '<span class="evidence-badge">需 usage credits</span>' : ""}</th><td data-label="推理控制 / API 默认">${esc(m.efforts)}<span class="task-detail">默认：${esc(m.default_effort)}</span></td><td data-label="编码起步 / 依据"><strong>${esc(advice.start)}</strong><span class="task-detail">${esc(advice.basis)}</span></td><td data-label="保留、升档或换模型条件">${esc(advice.upgrade)}</td><td data-label="本报告证据">AA 智能指数：${coverage.aa_url ? link(coverage.aa_url,coverage.aa) : coverage.aa}<span class="task-detail">英文写作：${coverage.writing ? coverage.writing+" 个配置" : "缺测"}<br>Vulcan v4：${coverage.coding ? coverage.coding+" 个配置" : "缺同版数据"}</span><button class="inline-button" data-claude-reasoning="${esc(m.name)}">查看档位证据 →</button></td></tr>`;
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
  // Sticky in-page TOC for the visible panel. Buttons (not #anchors) keep the panel hash intact.
  let tocObserver=null;
  function buildPageToc(name){
    const toc=$("pageToc"), panel=$(name); if(!toc||!panel) return;
    const targets=[...panel.querySelectorAll("[data-toc], .section-heading")].filter(el=>el.matches("[data-toc]")||!el.querySelector(".eyebrow"));
    if(tocObserver) tocObserver.disconnect();
    toc.hidden=targets.length<2;
    toc.innerHTML=targets.map((el,i)=>{
      if(!el.id) el.id=`toc-${name}-${i}`;
      const label=el.dataset.toc||el.querySelector("h2")?.textContent||"";
      return `<button type="button" data-toc-target="${esc(el.id)}">${esc(label)}</button>`;
    }).join("");
    toc.querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>$(b.dataset.tocTarget)?.scrollIntoView({behavior:"smooth",block:"start"})));
    if(!("IntersectionObserver" in window)) return;
    const mark=id=>toc.querySelectorAll("button").forEach(b=>{const on=b.dataset.tocTarget===id;b.classList.toggle("active",on);if(on)b.scrollIntoView({block:"nearest",inline:"nearest"});});
    tocObserver=new IntersectionObserver(entries=>{const hit=entries.filter(e=>e.isIntersecting).sort((a,b)=>a.boundingClientRect.top-b.boundingClientRect.top)[0];if(hit)mark(hit.target.id);},{rootMargin:"-110px 0px -65% 0px"});
    targets.forEach(el=>tocObserver.observe(el));
  }
  function showPanel(name, updateHash = true) {
    // "#profiles?m=<model id>" deep-links a model in the profile tab; other panels ignore the query.
    const [panelName, query] = String(name || "").split("?");
    name = panelName;
    const linkedModel = new URLSearchParams(query || "").get("m");
    if (name === "profiles" && linkedModel && mpEntry(linkedModel)) mpView.model = linkedModel;
    if (![...document.querySelectorAll("[data-panel]")].some(tab => tab.dataset.panel === name)) name = "overview";
    document.querySelectorAll(".panel").forEach(panel => { panel.hidden = panel.id !== name; });
    document.querySelectorAll("[data-panel]").forEach(tab => {
      tab.setAttribute("aria-selected", String(tab.dataset.panel === name));
      tab.tabIndex = tab.dataset.panel === name ? 0 : -1;
    });
    if (updateHash) {
      history.replaceState(null, "", "#" + name + (name === "profiles" ? "?m=" + encodeURIComponent(mpView.model) : ""));
      window.scrollTo({top:Math.min(window.scrollY, document.querySelector(".nav-shell").offsetTop), behavior:"instant"});
    }
    if (name === "overview") renderTaskEffortChart();
    buildPageToc(name);
    if (name === "explorer") renderExplorer();
    if (name === "capabilities") { renderEffortScalingChart(); renderCapIndexChart(); }
    if (name === "profiles") renderModelProfile();
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
    ["Intelligence Index","AA 智能指数","分","all","10 项评测加权；公开取整。"],
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
    $("capabilityTable").innerHTML = table(["模型 / 来源配置", ...columns.map(m => `<button class="metric-head" data-sort="${esc(m[0])}" title="${esc(m[4])}">${m[1]}${metricSort.key === m[0] ? metricSort.descending ? " ↓" : " ↑" : ""}<br><span class="small">${m[2]}</span></button>`)], profiles.map(p => `<tr><th class="metric-model">${link(p.source_url,p.model)}<small>${esc(p.source_label.replace(/^Anthropic /,""))}<br>${esc(p.snapshot)}${p.score_estimated ? " · AA 智能指数为估计值" : ""}</small></th>${columns.map(m => `<td class="metric-value" title="${esc(p.raw_metrics[m[0]] || "未提供")}">${m[2].startsWith("USD") ? money(p.metrics[m[0]]) : fmt(p.metrics[m[0]],2)}${p.raw_metrics[m[0]]?.includes("*") ? "*" : ""}</td>`).join("")}</tr>`).join(""));
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
    general:{title:"AA 智能指数与评测费用", y:"AA 智能指数（分）", xmin:10, yrange:[15,65], axes:[["cost_usd","整套指数费用 USD"],["weighted_cost_per_task_usd","加权单任务费用 USD"]], unit:"v4.3.2；原45条为10-14，补4条于10-15、10条于10-16。同版、不同读取时间；* 为来源估计。", caveat:"整套指数与加权单任务是两种费用口径。Default Fallback 是来源配置的一部分，比例未知；这些点不能解释为无回退纯模型。", method:"AA 智能指数由10项评测组成，样本规模因子项而异，不能合并为一个统一 n。费用为 AA 按来源价格与用量估算；不含重复测试，不是官方 token 单价或订阅扣额。原45条保持原快照；14个补充点使用同版页面。Opus 4.7 / 4.6 / 4.5 AA 智能指数为估计值；Fable 5 含4.8回退，均不进入纯模型前沿。Haiku 5.5 的阶梯价覆盖未确认。"},
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
    if (row.score_estimated) notes.push("AA 智能指数是来源估计值，部分子项未测；不参与标准升档差分或前沿。");
    if (row.cost_complete === false) notes.push(`费用缺失：${row.priced_n}/${row.n} 个完整收据；有收据子集均价不用于主图。`);
    if (row.benchmark === "coding") notes.push(`CLI：${row.harness}；${row.protocol}；运行 ${row.run_start_utc} 至 ${row.run_end_utc}；超时 ${row.timeouts} 次。`);
    if (row.benchmark === "general") notes.push(`加权单任务 ${money(row.weighted_cost_per_task_usd)}；回退标记：${row.fallback || "未标注"}。`);
    if (row.benchmark === "writing") notes.push(`稿件间标准差 ${fmt(row.overall_std)}，不作为均值置信区间；${row.variant === "provider_default" ? "provider default 非显式指定档位。" : ""}`);
    if (row.variant === "unverified") notes.push("来源 no thinking 与官方支持档位不一致，实际请求设置尚未核验。");
    if (row.benchmark === "arena") notes.push(`95% CI：[${fmt(row.score-row.ci95_halfwidth)}, ${fmt(row.score+row.ci95_halfwidth)}] 个百分点；${fmt(row.n,0)} 会话。`);
    const peers = filteredRows().filter(r => r.id !== row.id && finite(r[$("xmetric").value]) && finite(row[$("xmetric").value]) && Math.abs(r.score-row.score) < (state.group === "coding" ? 1 : .5) && Math.abs(Math.log(r[$("xmetric").value]/row[$("xmetric").value])) < .1);
    $("detail").innerHTML = `<div class="topline"><h3>${esc(row.model)} · ${esc(effortText(row))}</h3><span class="tag">${eligibilityText(row)}</span></div><div class="numbers"><div><b>${fmt(row.score)}${row.score_estimated ? "*" : ""}${finite(row.ci95_halfwidth) ? " ±"+fmt(row.ci95_halfwidth) : ""}</b><span>${esc(row.benchmark === "general" ? "AA 智能指数" : row.score_name)}</span></div><div><b>${money(row.cost_usd)}</b><span>${state.group === "general" ? "整套指数" : state.group === "arena" ? "平台 P50 / 任务" : state.group === "writing" ? "每篇稿" : "每次尝试"}</span></div><div><b>${timeText(row)}</b><span>${sampleText(row)}</span></div></div>${notes.map(n => `<p>${esc(n)}</p>`).join("")}<p>快照 / 版本：${esc(row.snapshot || row.publication_date || "来源未统一快照")} · ${esc(row.version || row.version_snapshot || "")}</p><p>${link(row.scorecard_url || row.source_url,"查看原始来源")}${row.data_source_url ? " · "+link(row.data_source_url,"运行记录") : ""}</p>${peers.length ? `<div class="near"><span class="small">邻近点：</span>${peers.map(p => `<button data-peer="${p.id}">${esc(modelMap.get(p.model).short)} ${esc(effortText(p))}</button>`).join("")}</div>` : ""}`;
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
      if(usesLongContextPrice(m,input)){prices={input:m.tier_input,cached:m.tier_cached,output:m.tier_output};note=`prompt ${m.tier_inclusive ? "≥" : ">"}${fmt(m.tier_threshold,0)}；整次升档`;}
      const over=answer+reason > m.max_output ? "超出同步输出上限" : input > m.context || m.context_kind === "shared" && input+answer+reason > m.context ? "超出上下文窗口" : null;
      const per=over ? null : (input*(1-cache/100)*prices.input+input*cache/100*prices.cached+(answer+reason)*prices.output)/1e6;
      return {m,prices,note,over,per,total:per === null ? null : per*count};
    }).sort((a,b) => (a.total ?? Infinity)-(b.total ?? Infinity));
    $("calcSummary").textContent=`每次 ${fmt(input,0)} 输入（${fmt(cache)}% 已命中缓存）＋ ${fmt(answer+reason,0)} 输出含推理，重复 ${fmt(count,0)} 次。按费用排序，未控制模型质量和实际用量差异。`;
    const max=Math.max(...costs.map(c => c.total || 0),.001);
    $("costTable").innerHTML=table(["模型","每次费用","全部请求费用","实际采用单价：输入 / 缓存 / 输出","适用条件"],costs.map(c => `<tr data-cost-model="${esc(c.m.id)}" data-per="${c.per ?? ""}" data-total="${c.total ?? ""}"><th>${esc(c.m.name)}</th><td>${money(c.per)}</td><td>${money(c.total)}${c.total !== null ? `<div class="cost-bar" style="width:${150*c.total/max}px"></div>` : ""}</td><td>${money(c.prices.input)} / ${money(c.prices.cached)} / ${money(c.prices.output)}</td><td>${esc(c.over || c.note)}</td></tr>`).join(""));
  }
  $("specScope").addEventListener("change",renderSpecs);
  $("exportSpecs").addEventListener("click",() => exportCSV(shownModels(),`官方规格-${DATA.meta.reviewed_at}.csv`));
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
    $("platformCards").innerHTML = ext.platforms.map(p => `<article class="platform-card"><h3>${link(p.url, p.name)}</h3><p><strong>核心指标：</strong>${esc(p.focus.replace("10 项综合 Intelligence Index","AA 智能指数（10 项评测）"))}</p><p><strong>成本口径：</strong>${esc(p.cost_metric)}</p><span class="platform-stat">快照：${esc(p.snapshot)}</span></article>`).join("");
    const rows = shownPanoramaRows();
    if ($("panoramaCount")) $("panoramaCount").textContent = `${rows.length} 个在用系列 · 5 大主流评测站与生产调用横向对照`;
    $("panoramaTable").innerHTML = `<table class="task-table"><caption>四大模型家族（Grok / ChatGPT / Gemini / Claude）跨平台能力与成本对照矩阵</caption><thead><tr>${["家族 / 型号与状态","Artificial Analysis (v4.3.2)","Arena.ai & LiveBench 2.0","Scale SEAL 专项表现","OpenRouter 生产用量与成本","跨榜选型与甜蜜点建议"].map(h => `<th scope="col">${h}</th>`).join("")}</tr></thead><tbody>${rows.map(r => `<tr><th scope="row">${esc(r.model)} <span class="badge">${esc(r.family)}</span><span class="task-detail">${esc(r.status)}</span></th><td data-label="Artificial Analysis (v4.3.2)"><strong>AA 智能指数：${esc(r.aa_ii)}</strong><span class="task-detail">单任务成本：${esc(r.aa_cost_task)}<br>官方六域（整体 AA 智能指数最高代表档）：${esc(r.aa_cap_highlights)}<br>${link(r.aa_cap_source_url,"AA 领域来源")}</span></td><td data-label="Arena.ai & LiveBench 2.0"><strong>Arena：${esc(r.arena)}</strong><span class="task-detail">LiveBench ${esc(r.livebench_snapshot)}：${esc(r.livebench_2)}</span></td><td data-label="Scale SEAL 专项表现">${esc(r.scale_seal)}<span class="task-detail">${esc(r.scale_snapshot)}</span></td><td data-label="OpenRouter 生产用量与成本">${esc(r.openrouter)}<span class="task-detail">截至 ${esc(r.openrouter_snapshot)} · 用量不是能力</span></td><td data-label="跨榜选型与甜蜜点建议">${esc(r.sweet_spot)}</td></tr>`).join("")}</tbody></table>`;
    $("scaleHighlightsTable").innerHTML = table(["Scale SEAL 专项榜单","Top 1","Top 2","Top 3","Top 4"], ext.scale_highlights.map(s => `<tr><th>${link(s.source_url || "https://labs.scale.com/leaderboard", s.benchmark)}<span class="task-detail">${esc(s.checked_at || "2026-10-19")} 核验</span></th><td><strong>#1</strong> ${esc(s.top1)}</td><td><strong>#2</strong> ${esc(s.top2)}</td><td><strong>#3</strong> ${esc(s.top3)}</td><td><strong>#4</strong> ${esc(s.top4)}</td></tr>`).join(""));
  }
  if ($("panoramaFamily")) {
    $("panoramaFamily").addEventListener("change", renderPanorama);
    $("exportPanorama").addEventListener("click", () => exportCSV(shownPanoramaRows(), `四大家族五站全景对比-${DATA.meta.reviewed_at}.csv`));
  }

  // Capability values stay official; missing domains never borrow Intelligence Index.
  // BEGIN CAPABILITY_MATH (also exercised by the offline regression tests)
  const capabilityEfforts = ["non-reasoning", "minimal", "low", "medium", "high", "xhigh", "max", "unspecified"];
  const capScore = (e, key) => {
    const value = key === "__ii__" ? e.intelligenceIndex : key.startsWith("eval:") ? e.evalMetrics?.[key.slice(5)] : e.capabilities?.[key];
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
    domains = [{key:"__ii__",slug:"intelligence",label:"AA 智能指数",shortLabel:"AA 智能指数",coreEvals:[],weightNote:"AA 智能指数；排名按公开精度"},...domains];
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
      const cost = key === "__ii__" && finite(e.costPerTask) ? e.costPerTask : null;
      return {variant:e.slug, model:e.releaseName, effort:e.effort, metric:key, score,
        score_status:finite(score) ? "observed" : "missing", cost_per_task_usd:cost,
        delta_score:finite(score) && finite(previousScore) ? score-previousScore : null,
        delta_cost_usd:key === "__ii__" && previous && finite(cost) && finite(previous.costPerTask) ? cost-previous.costPerTask : null,
        previous_measured_effort:previous?.effort ?? null, selected:e.slug === selectedSlug,
        representative_by_overall_ii:!!e.isTopVariant,
        best_for_metric:finite(score) && capPrecision(score) === capPrecision(best),
        fallback:e.fallbackLabel || "", source_url:key.startsWith("eval:") ? (finite(score) ? e.evalSourceUrl || null : null) : e.sourceUrl || null, evidence_type:key==="eval:Terminal-Bench 4.0" ? "model + agent; exact AA configuration; harness not archived" : "exact model + effort", version:"AA v4.3.2", evaluation_date:null, harness:null, budget:null, confidence_interval:null,
        raw_unit:key.startsWith("eval:") ? "%" : "index points", collected_at:"2026-10-19", attempts:null, snapshot:"2026-10-19", cost_scope:"AA 智能指数加权单任务成本；非子评测专属费用"};
    });
  }
  // END CAPABILITY_MATH
  const capState = {tab:"all", selectedId:null};
  const getCapEntries = () => capScopeEntries(DATA.aa_capability_indexes?.entries || [], $("capIndexScope")?.value || "four_family_top");
  const capLabel = e => `${e.releaseShort || e.releaseName} · ${e.effort}`;
  function renderCapDetail(entry, entries, domains) {
    if (!entry || !$("capIndexDetail")) return;
    const rows = [{key:"__ii__",slug:"intelligence",label:"AA 智能指数",coreEvals:["AA 智能指数"],weightNote:"10 项底层评测；沿用 AA 官方方法"},...domains].map(d => {
      const score = capScore(entry,d.key), ranking = capRanking(entries,d.key), rank = ranking.ranks.get(entry.slug);
      return `<tr><th>${link(d.key==="__ii__" ? "https://artificialanalysis.ai/methodology/intelligence-benchmarking" : "https://artificialanalysis.ai/zh/indexes/"+d.slug,d.label)}<span class="task-detail">${esc(d.coreEvals.join(" · "))}<br>${esc(d.weightNote)}</span></th><td>${finite(score) ? fmt(score,2) : "无数据 · 不参排"}</td><td>${rank ? `#${rank} / ${ranking.n} 个有效配置` : `不参排 / ${ranking.n} 个有效配置`}<span class="task-detail">候选 ${entries.length} 个；缺测 ${entries.length-ranking.n} 个</span></td><td>${entry.strengthsGlobalRank?.[d.slug] ? `AA 来源全球发布排名 #${entry.strengthsGlobalRank[d.slug]}` : "未提供"}<span class="task-detail">AA 全库分母未存档；与当前筛选排名不同</span></td></tr>`;
    }).join("");
    $("capIndexDetail").innerHTML = `<h3>${esc(capLabel(entry))} · 完整 7 项指标</h3><p class="small">${esc(entry.fallbackLabel || "来源未标记回退")} · ${link(entry.sourceUrl,"模型来源")} · ${link("https://artificialanalysis.ai/methodology/capability-indices","官方权重与方法")}。分项共享部分底层评测，六域领先不是六组独立实验。</p><div class="table-scroll">${table(["领域 / 构成与权重","官方分数","当前筛选排名 / 有效分母","来源全球排名（独立口径）"],rows)}</div>`;
  }
  function renderCapIndexChart() {
    const cap = DATA.aa_capability_indexes, svg = $("capBumpChart");
    if (!cap || !svg) return;
    const entries = getCapEntries();
    $("capPointTip").classList.remove("is-visible");
    if (!entries.some(e => e.slug === capState.selectedId)) capState.selectedId = entries[0]?.slug;
    $("capModelPills").innerHTML = entries.map(e => `<button type="button" class="pill-btn ${e.slug === capState.selectedId ? "is-active" : ""}" aria-pressed="${e.slug === capState.selectedId}" data-cap-model="${esc(e.slug)}"><span class="swatch" style="background:${e.color}"></span>${esc(capLabel(e))}</button>`).join("");
    const width = Math.max(1180,Math.round(svg.getBoundingClientRect().width || 1180));
    const showII = $("capShowII").checked, domains = cap.domains;
    const allCols = [...(showII ? [{key:"__ii__",shortLabel:"AA 智能指数"}] : []),...domains];
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
          return `<circle class="cap-node" tabindex="0" role="button" aria-describedby="capPointTip" aria-label="${esc(capLabel(e)+" · "+c.shortLabel+" · 分数 "+fmt(score,2)+" · 名次 #"+rank+" · 有效配置 "+rankings.get(c.key).n+" · 候选 "+entries.length+" · 范围 "+$("capIndexScope").selectedOptions[0].textContent)}" data-domain="${c.key}" data-score="${score}" data-rank="${rank}" data-valid-n="${rankings.get(c.key).n}" cx="${x}" cy="${y}" r="${selected ? 9 : 5}" fill="${e.color}" stroke="#fffef9" stroke-width="1.5"><title>${esc(capLabel(e)+" · "+c.shortLabel+" "+fmt(score,2)+" · #"+rank+"/"+rankings.get(c.key).n)}</title></circle>${selected ? `<text pointer-events="none" x="${x}" y="${y+3}" font-size="9" text-anchor="middle" fill="white">${rank}</text>` : ""}`;
        }).join("");
        const first=cols[0], last=cols[cols.length-1], firstRank=rankings.get(first.key).ranks.get(e.slug),lastRank=rankings.get(last.key).ranks.get(e.slug);
        const endLabel=(c,r,x,anchor) => {
          if(!r)return "";
          const labelY=endPositions.get(c.key+e.slug), pointX=anchor==="end"?margin.left:width-margin.right;
          return `${Math.abs(labelY-rankY(r))>2?`<line x1="${pointX}" y1="${rankY(r)}" x2="${x}" y2="${labelY}" stroke="${e.color}" stroke-width=".8"/>`:""}<text x="${x}" y="${labelY+4}" text-anchor="${anchor}" font-size="10.5" fill="${selected ? "#165e54" : "#223c3a"}">${esc(capLabel(e))}</text>`;
        };
        parts.push(`<g class="bump-group ${selected ? "is-highlighted" : ""}" role="group" data-cap-id="${esc(e.slug)}" aria-label="${esc(capLabel(e))}"><title>${esc(capLabel(e)+" · "+(e.fallbackLabel || "来源未标记回退"))}</title><path class="bump-path" d="${path}" fill="none" stroke="${e.color}" stroke-width="${selected?3.6:2}" opacity="${selected?1:.55}"/>${nodes}${endLabel(first,firstRank,margin.left-14,"end")}${endLabel(last,lastRank,width-margin.right+14,"start")}</g>`);
      });
    } else {
      const dom=cols[0], ranking=rankings.get(dom.key), x=v=>margin.left+v/100*(width-margin.left-margin.right);
      for(let t=0;t<=100;t+=20) parts.push(`<text x="${x(t)}" y="46" class="tick" text-anchor="middle">${t} 分</text><line x1="${x(t)}" x2="${x(t)}" y1="65" y2="${height-margin.bottom}" stroke="#e3e9e1"/>`);
      ranking.valid.forEach((e,i) => {
        const y=rankY(i+1), sc=capScore(e,dom.key), rank=ranking.ranks.get(e.slug);
        parts.push(`<g class="bump-group" tabindex="0" role="button" data-cap-id="${esc(e.slug)}" aria-label="${esc(capLabel(e)+" · "+dom.shortLabel+" · 分数 "+fmt(sc,2)+" · 名次 #"+rank+" · 有效配置 "+ranking.n+" · 候选 "+entries.length+" · 范围 "+$("capIndexScope").selectedOptions[0].textContent)}"><text x="8" y="${y+4}" font-size="11">#${rank} ${esc(capLabel(e))}</text><rect class="cap-bar" data-score="${sc}" data-rank="${rank}" data-valid-n="${ranking.n}" x="${margin.left}" y="${y-9}" width="${x(sc)-margin.left}" height="18" rx="3" fill="${e.color}"/><text x="${x(sc)+8}" y="${y+4}" font-size="12">${fmt(sc,2)} 分</text></g>`);
      });
    }
    svg.innerHTML=parts.join("");
    const missing=domains.map(d=>({d,entries:entries.filter(e=>!finite(capScore(e,d.key)))})).filter(x=>x.entries.length);
    $("capMissingNote").textContent=missing.length ? missing.map(x=>`${x.d.label}缺测 ${x.entries.length} 个：${x.entries.map(capLabel).join("、")}`).join("；")+"。无节点、断开连线、不补值，CSV 分数与排名留空。" : "当前集合六域数据完整。";
    const select=id=>{capState.selectedId=id;renderCapIndexChart();[...$("capModelPills").querySelectorAll("button")].find(b=>b.dataset.capModel===id)?.focus();};
    $("capModelPills").querySelectorAll("[data-cap-model]").forEach(b=>b.addEventListener("click",()=>select(b.dataset.capModel)));
    svg.querySelectorAll("[data-cap-id]").forEach(node=>{
      node.addEventListener("click",()=>select(node.dataset.capId));
      node.addEventListener("keydown",event=>{if(node.getAttribute("role")==="button" && (event.key==="Enter"||event.key===" ")){event.preventDefault();select(node.dataset.capId);}});
    });
    svg.querySelectorAll(".cap-node").forEach(point=>{
      const show=()=>{
        const tip=$("capPointTip"), rect=point.getBoundingClientRect();
        tip.textContent=point.getAttribute("aria-label");tip.classList.add("is-visible");
        tip.style.left=Math.max(8,Math.min(innerWidth-tip.offsetWidth-8,rect.left))+"px";
        tip.style.top=Math.max(8,Math.min(innerHeight-tip.offsetHeight-8,rect.bottom+12))+"px";
      };
      const hide=()=>$("capPointTip").classList.remove("is-visible");
      point.addEventListener("pointerleave",hide);point.addEventListener("blur",hide);
      const selectPoint=()=>{
        const id=point.closest("[data-cap-id]").dataset.capId, domain=point.dataset.domain;
        capState.selectedId=id;renderCapIndexChart();
        svg.querySelector(`[data-cap-id="${id}"] .cap-node[data-domain="${domain}"]`)?.focus();
      };
      point.addEventListener("pointerenter",show); point.addEventListener("focus",show);
      point.addEventListener("click",event=>{event.stopPropagation();selectPoint();});
      point.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();event.stopPropagation();selectPoint();}});
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
  const reasoningEvals = ["Humanity's Last Exam", "CritPt", "Terminal-Bench 4.0", "SciCode"];
  const reasoningEntries = () => {
    const variants=new Map(DATA.aa_release_series.releases.flatMap(r=>r.variants).map(v=>[v.slug,v]));
    return DATA.aa_capability_indexes.entries.map(e=>{
      const v=variants.get(e.slug);
      return {...e,evalMetrics:v?.effort===e.effort ? v.evalMetrics : null,evalSourceUrl:v?.effort===e.effort ? v.evalSourceUrl : null};
    });
  };
  const effortView = {selectedSlug:null};
  function renderReasoningCharts() {
    const cap=DATA.aa_capability_indexes;
    if (!cap || !$("reasoningCurve")) return;
    const entries=reasoningEntries().filter(e=>e.releaseSlug===$("reasoningRelease").value);
    if (!entries.some(e=>e.slug===effortView.selectedSlug)) effortView.selectedSlug=entries.find(e=>e.isTopVariant)?.slug || entries[0]?.slug;
    const key=$("reasoningMetric").value, metric=key==="__ii__" ? "AA 智能指数" : key.startsWith("eval:") ? key.slice(5) : cap.domains.find(d=>d.key===key).label;
    const rows=effortRows(entries,key,effortView.selectedSlug), color=entries[0]?.color || "#165e54";
    $("reasoningSelected").innerHTML=rows.map(r=>`<option value="${esc(r.variant)}">${esc(r.effort)}${r.representative_by_overall_ii?" · AA 智能指数代表档":""}</option>`).join("");
    $("reasoningSelected").value=effortView.selectedSlug;
    $("reasoningCostPanel").hidden=key!=="__ii__";
    const selected=rows.find(r=>r.selected), valid=rows.filter(r=>finite(r.score)), costs=valid.filter(r=>finite(r.cost_per_task_usd)&&r.cost_per_task_usd>=0);
    $("reasoningChartNote").textContent=`图表与表格可横向滚动。${entries[0]?.releaseName} · ${metric}：${valid.length}/${rows.length} 个配置有分数，${costs.length} 个同时有 AA 加权成本。选中 ${selected?.effort}；实心点为选中档，外圈为该维度最高分（可并列）。横轴档位等距只表顺序；不同厂商不等预算。${key!=="__ii__" ? "所选子评测/领域没有同口径专属费用，已隐藏成本图；不以综合成本代替。" : ""}`;
    // Fit the y-axis to the measured range so small effort gains stay visible.
    const scores=valid.map(r=>r.score), lo=scores.length ? Math.max(0,Math.floor((Math.min(...scores)-3)/5)*5) : 0;
    const ceiling=scores.length ? Math.max(lo+10,Math.ceil((Math.max(...scores)+2)/5)*5) : 10, step=(ceiling-lo)/5;
    const w=620,h=340,m={left:65,right:35,top:35,bottom:65}, y=v=>h-m.bottom-(v-lo)/(ceiling-lo)*(h-m.top-m.bottom);
    const axis=()=>{
      const parts=[];
      for(let tick=lo;tick<=ceiling+1e-9;tick+=step) parts.push(`<line x1="${m.left}" x2="${w-m.right}" y1="${y(tick)}" y2="${y(tick)}" stroke="#e3e9e1"/><text x="${m.left-10}" y="${y(tick)+4}" text-anchor="end" font-size="11">${fmt(tick,1)}</text>`);
      parts.push(`<text x="${m.left}" y="18" font-size="12" fill="#165e54">${esc(metric)}${lo>0?`（纵轴从 ${lo} 起）`:""}</text>`);return parts;
    };
    const node=(r,x,cy,offset=-15,compact=false)=>`<g class="reasoning-dot" role="button" tabindex="0" aria-pressed="${r.selected}" data-variant="${esc(r.variant)}" data-score="${r.score}" aria-label="${esc(r.effort+"，"+metric+" "+fmt(r.score,2)+"，AA 加权成本 "+money(r.cost_per_task_usd))}"><title>${esc(r.effort+" · "+fmt(r.score,2)+" 分 · "+money(r.cost_per_task_usd)+" · "+(r.fallback||"来源未标记回退"))}</title>${r.best_for_metric?`<circle cx="${x}" cy="${cy}" r="11" fill="none" stroke="${color}" stroke-width="1.5"/>`:""}<circle cx="${x}" cy="${cy}" r="${r.selected?7:5}" fill="${r.selected?color:"#fffef9"}" stroke="${color}" stroke-width="2"/><text x="${x}" y="${cy+offset}" text-anchor="middle" font-size="11" fill="${color}">${esc(r.effort)}${compact ? "" : " · "+fmt(r.score,2)}</text></g>`;
    const measuredIndices=rows.map(r=>capabilityEfforts.indexOf(r.effort));
    const firstEffort=Math.min(...measuredIndices), lastEffort=Math.max(...measuredIndices);
    const xEffort=index=>firstEffort===lastEffort ? (m.left+w-m.right)/2 : m.left+(index-firstEffort)*(w-m.left-m.right)/(lastEffort-firstEffort);
    const x=i=>xEffort(measuredIndices[i]);
    const curve=axis();let path="",previous=false,previousEffort=-1;
    rows.forEach((r,i)=>{if(!finite(r.score)){previous=false;return;}const effortIndex=capabilityEfforts.indexOf(r.effort);path+=`${previous && effortIndex===previousEffort+1?"L":"M"}${x(i)},${y(r.score)} `;previous=true;previousEffort=effortIndex;});
    curve.push(`<path d="${path}" fill="none" stroke="${color}" stroke-width="2"/>`);
    rows.forEach((r,i)=>{curve.push(`<text x="${x(i)}" y="${h-40}" text-anchor="middle" font-size="11">${esc(r.effort)}</text>`);if(finite(r.score))curve.push(node(r,x(i),y(r.score)));else curve.push(`<text x="${x(i)}" y="${h-75}" text-anchor="middle" font-size="11">无数据</text>`);});
    for(let index=firstEffort;index<=lastEffort;index++) {
      if(!measuredIndices.includes(index)) curve.push(`<text x="${xEffort(index)}" y="${h-40}" text-anchor="middle" font-size="11">${esc(capabilityEfforts[index])}</text><text x="${xEffort(index)}" y="${h-75}" text-anchor="middle" font-size="11">无数据</text>`);
    }
    curve.push(`<text x="${w/2}" y="${h-10}" text-anchor="middle" font-size="12">同一模型的已测档位（等距，不代表投入倍数）</text>`);
    const cost=axis(), maxCost=Math.max(.01,...costs.map(r=>r.cost_per_task_usd))*1.12, cx=v=>m.left+v/maxCost*(w-m.left-m.right);
    for(let i=0;i<=4;i++){const v=i*maxCost/4;cost.push(`<text x="${cx(v)}" y="${h-40}" text-anchor="middle" font-size="11">${money(v)}</text>`);}
    costs.forEach((r,i)=>cost.push(node(r,cx(r.cost_per_task_usd),y(r.score),i%2 ? 24 : -18,true)));
    if(!costs.length)cost.push(`<text x="${w/2}" y="${h/2}" text-anchor="middle">无同口径费用，不补估算散点</text>`);
    cost.push(`<text x="${w/2}" y="${h-10}" text-anchor="middle" font-size="12">AA 智能指数加权单任务成本（USD）</text>`);
    [["reasoningCurve",curve],["reasoningCost",cost]].forEach(([id,parts])=>{const svg=$(id);svg.setAttribute("viewBox",`0 0 ${w} ${h}`);svg.innerHTML=`<title>${esc(entries[0]?.releaseName+" · "+metric)}</title>`+parts.join("");});
    const showCost=costs.length>0;
    $("reasoningEvidenceTable").innerHTML=table(["已测档位 / 来源配置","官方得分","相对上一已测档分差",...(showCost?["AA 加权成本 / 增量"]:[]),"选档标记"],rows.map(r=>`<tr data-variant="${esc(r.variant)}"><th>${r.source_url ? link(r.source_url,r.effort) : esc(r.effort)+'<span class="task-detail">无该指标来源 · 无测量</span>'}<span class="task-detail">${esc(r.fallback||"来源未标记回退")}</span></th><td>${finite(r.score)?fmt(r.score,2):"无数据"}</td><td>${finite(r.delta_score)?`${r.delta_score>0?"+":""}${fmt(r.delta_score,2)}（${esc(r.previous_measured_effort)} → ${esc(r.effort)}）`:"无可比相邻值"}</td>${showCost?`<td>${money(r.cost_per_task_usd)}<span class="task-detail">增量 ${finite(r.delta_cost_usd)?(r.delta_cost_usd>0?"+":"")+money(r.delta_cost_usd):"未提供"}</span></td>`:""}<td>${[r.selected?"当前选中":"",r.representative_by_overall_ii?"AA 智能指数最高代表档":"",r.best_for_metric?"本维度最高（可并列）":""].filter(Boolean).join(" · ")||"—"}</td></tr>`).join(""));
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
    $("reasoningMetric").innerHTML=`<option value="__ii__">AA 智能指数</option>`+reasoningEvals.map(name=>`<option value="eval:${esc(name)}">${esc(name)}（原始 %）</option>`).join("")+DATA.aa_capability_indexes.domains.map(d=>`<option value="${d.key}">${esc(d.label)}</option>`).join("");
    ["reasoningRelease","reasoningMetric"].forEach(id=>$(id).addEventListener("change",renderReasoningCharts));
    $("reasoningSelected").addEventListener("change",()=>{effortView.selectedSlug=$("reasoningSelected").value;renderReasoningCharts();});
    $("exportReasoningEvidence").addEventListener("click",()=>exportCSV(effortRows(reasoningEntries().filter(e=>e.releaseSlug===$("reasoningRelease").value),$("reasoningMetric").value,effortView.selectedSlug),"同模型推理档位-官方能力与AA加权成本-2026-10-19.csv"));
  }
  if ($("practicalEvidence")) {
    const evidence=DATA.practical_evidence, sources=new Map(evidence.sources.map(s=>[s.id,s]));
    $("practicalEvidence").innerHTML=`<div class="section-heading"><h2>第二层：实战能力 · 第三方证据</h2><p>目录复核 ${esc(evidence.reviewed_at)}；复核日不是评测日。保留原有五站参考，以下独立来源只链接与记录方法；没有核验的配置级数字标待补充。不同单位与 harness 不合成。</p></div><div class="reasoning-chart-grid">${evidence.cards.map(c=>`<article class="card"><h3>${esc(c.title)}</h3><p><strong>${esc(c.metric)}</strong></p><p>${esc(c.boundary)}</p><p>${c.sources.map(id=>{const s=sources.get(id);return link(s.source_url,s.name)+"（"+esc(s.evidence_type)+"）";}).join(" · ")}</p></article>`).join("")}</div><details class="card"><summary>来源目录与可比性记录（7 个来源）</summary><p>证据类型：${evidence.evidence_types.map(esc).join(" / ")}。未知字段明确保留 null / 未提供；来源已有置信区间才展示。转载授权未明仅提供链接和精简事实。</p>${evidence.sources.map(s=>`<article><h3>${link(s.source_url,s.name)} · ${link(s.methodology_url,"方法 / 运行记录")} ${s.additional_urls.map(url=>link(url,"代码")).join(" · ")}</h3><p>${esc(s.boundary)}</p><p class="small">版本：${esc(s.version)}；原始单位：${esc(s.raw_unit)}；证据：${esc(s.evidence_type)}；状态：${esc(s.status)}。<br>来源采集日：未提供；评测日：未提供；模型 / effort / harness / 预算 / 次数 / 置信区间：未提供（需配置级记录核验）。目录复核：${esc(s.directory_reviewed_at)}。</p></article>`).join("")}</details>`;
  }
  // Advice is version-specific prior evidence, never another measured curve or score.
  function renderTaskAdvice() {
    const guidance=DATA.task_effort_guidance, modelId=$("adviceModel").value, taskType=$("adviceTask").value;
    const selected=guidance.recommendations.find(r=>r.modelId===modelId && r.taskType===taskType);
    $("adviceMatrix").innerHTML=table(["版本 / 原生档位",...guidance.tasks.map(t=>esc(t.label))],guidance.models.map(m=>`<tr><th scope="row">${esc(m.name)}</th>${guidance.tasks.map(t=>{
      const r=guidance.recommendations.find(r=>r.modelId===m.modelId && r.taskType===t.id);
      return `<td data-label="${esc(t.label)}"><button type="button" class="effort-chip" data-advice-model="${m.modelId}" data-advice-task="${t.id}" aria-pressed="${r===selected}" aria-label="${esc(m.name+' · '+t.label+' · '+r.label+' '+r.nativeEffort)}"><code>${esc(r.nativeEffort)}</code><span>${esc(r.label)}</span></button></td>`;
    }).join("")}</tr>`).join(""));
    $("adviceMatrix").querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>{
      $("adviceModel").value=b.dataset.adviceModel;$("adviceTask").value=b.dataset.adviceTask;
      renderTaskAdvice();
      $("adviceMatrix").querySelector(`[data-advice-model="${b.dataset.adviceModel}"][data-advice-task="${b.dataset.adviceTask}"]`)?.focus();
    }));
    if(!selected) {
      $("adviceDetail").innerHTML='<h4>暂无版本级建议</h4><p>此版本尚无四任务起点记录，不继承厂商或家族先验。未建立任务最优结论。</p>';
      return;
    }
    const m=guidance.models.find(m=>m.modelId===modelId), task=guidance.tasks.find(t=>t.id===taskType);
    const index=m.supportedEfforts.indexOf(selected.nativeEffort), up=m.supportedEfforts[index+1], down=m.supportedEfforts[index-1];
    const highIndex=m.supportedEfforts.indexOf('high'), upper=m.supportedEfforts.slice(highIndex+1);
    $("adviceDetail").innerHTML=`<h4>${esc(m.name)} · ${esc(task.label)} · ${esc(selected.label)} <code>${esc(selected.nativeEffort)}</code></h4>
      <p><span class="evidence-badge">${esc(selected.evidenceType)}</span> · 未建立任务最优结论 · 核对 ${selected.checkedAt}</p>
      <p>${selected.caveats.map(esc).join(' ')}</p>
      <p>${link(selected.sourceUrl,'起点参考来源（不证明任务最优）')} · 样本 ${selected.sampleSize ?? '未提供'} · harness ${esc(selected.harness || '未提供')}</p>
      <div class="advice-adjustments"><p><strong>升档条件：</strong>补齐复现信息后，若存在跨模块根因、竞态、约束冲突或边界测试缺口，可试 ${up ? `<code>${up}</code>` : '该版本已无更高支持档位'}，逐档验收。high 仍有具体缺口时，${upper.length ? '仅按支持范围试 '+upper.map(e=>`<code>${e}</code>`).join(' / ') : '不猜测额外档位，拆分任务或换模型'}。</p>
      <p><strong>降档条件：</strong>单文件或模板任务、需求明确且测试稳定，可${down ? '试 <code>'+down+'</code>' : '保留当前最低支持档位'}；验收未退步才保留。${modelId==='claude-fable-5-1' ? '日常 medium 仅是验证后的降档候选；low 可能少检索而依赖记忆。' : ''}</p></div>
      <p class="small">原生支持：${m.supportedEfforts.map(esc).join(' / ')}。${m.officialDefault ? '官方默认 '+esc(m.officialDefault)+' 不等于四类任务最优。' : '未核验官方默认或最佳档位。'}费用比较完整成功交付（含失败重试），延迟比较任务完成时间，不用 tokens/s 代替。</p>
      <h4>支撑证据与覆盖边界</h4><ul>${selected.support.map(e=>`<li><strong>${esc(e.evidenceType)}</strong> · ${link(e.sourceUrl,'来源')}<p>${esc(e.statement)}</p><p class="small">覆盖：${esc(e.scope)}；样本 ${e.sampleSize ?? '未提供'}；harness ${esc(e.harness || '未提供')}。</p></li>`).join('')}</ul>`;
    const pm=(DATA.model_effort_profiles?.models||[]).find(x=>x.guidanceId===modelId);
    if(pm){
      const axis={complex:"complex",daily_code:"coding",repository_bug:"coding",design:"planning"}[taskType]||null;
      $("adviceDetail").insertAdjacentHTML("beforeend",`<p><button class="inline-button" data-profile-open="${esc(pm.id)}">在模型档案中看 ${esc(m.name)} 全部任务 →</button></p>`);
      $("adviceDetail").querySelector("[data-profile-open]").addEventListener("click",()=>{mpView.model=pm.id;mpView.task=axis;showPanel("profiles");$("report-nav").scrollIntoView({block:"start"});});
    }
  }
  if($("adviceModel")) {
    const guidance=DATA.task_effort_guidance;
    const releases=new Map(DATA.aa_release_series.releases.map(r=>[r.releaseSlug,r.name]));
    $("adviceModel").innerHTML=[...releases].map(([id,name])=>`<option value="${esc(id)}">${esc(name)}</option>`).join('');
    $("adviceTask").innerHTML=guidance.tasks.map(t=>`<option value="${t.id}">${esc(t.label)}</option>`).join('');
    $("adviceModel").value=$("reasoningRelease").value;
    $("adviceRules").innerHTML=guidance.rules.map(r=>`<li>${esc(r.text)}</li>`).join('');
    ["adviceModel","adviceTask"].forEach(id=>$(id).addEventListener('change',renderTaskAdvice));
    $("exportAdvice").addEventListener('click',()=>exportCSV(guidance.recommendations,'任务档位建议与证据-2026-10-20.csv'));
    renderTaskAdvice();
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
      if (item.scaleModel) parts.push(`<g data-scale-label="${esc(item.scaleModel)}">`);
      if (item.dim) parts.push(`<g opacity="0.18">`);
      if (Math.abs(item.ly - item.cy) > 3 || item.lx - item.cx > 12) {
        parts.push(`<line x1="${item.cx + 4}" y1="${item.cy}" x2="${item.lx - 2}" y2="${item.ly}" stroke="${item.col}" stroke-width="0.95" opacity="0.65"/>`);
      }
      parts.push(`<text x="${item.lx}" y="${item.ly + 3.5}" font-size="${item.isSel ? 12 : 11}" font-weight="${item.isSel ? 700 : 600}" fill="${item.isSel ? "#111827" : "#1f2937"}" style="paint-order:stroke;stroke:#ffffff;stroke-width:3.5px;stroke-linejoin:round">${esc(item.text)}</text>`);
      if (item.dim) parts.push("</g>");
      if (item.scaleModel) parts.push("</g>");
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
      shortLabel: "AA-Briefcase 知识工作",
      title: "AA-Briefcase v1.1 知识工作（原始 Elo）vs. 单任务成本",
      yLabel: "知识工作（AA-Briefcase v1.1 · 原始 Elo）",
      unit: " Elo",
      digits: 0,
      yrange: [650, 1880],
      yTicks: [800, 1000, 1200, 1400, 1600, 1800],
      attractiveY: 1450,
      attractiveX: 1.10,
      subnote: "本报告任务视图（AA-Briefcase knowledge work）：直接展示 AA-Briefcase v1.1 原始 Elo，不是架构设计能力成绩。Sonnet 5.5 max {{aa:claude-sonnet-5-5:max:planning:0}}、Opus 5.5 max {{aa:claude-opus-5-5:max:planning:0}}；Grok high {{aa:grok-4-7:high:planning:0}} → xhigh {{aa:grok-4-7:xhigh:planning:0}}，成本 ${{aa:grok-4-7:high:costPerTask:2}} → ${{aa:grok-4-7:xhigh:costPerTask:2}}。Elo 只作同基准相对比较，不能换算为能力百分比。",
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
      shortLabel: "AA 智能指数",
      title: "AA 智能指数（10 项全量 v4.3.2）vs. 单任务成本",
      yLabel: "AA 智能指数 v4.3.2（分）",
      unit: " 分",
      digits: 1,
      yrange: [14, 64],
      yTicks: [20, 30, 40, 50, 60],
      attractiveY: 42.5,
      attractiveX: 1.10,
      subnote: "直接使用快照中的 AA 智能指数 v4.3.2（10 项评测）。留档方法的分类权重为 Agents 30%、Coding 20%、Scientific Reasoning 20%、General 30%；不由本报告的任务合成分重建。显示其他市场参考模型时，可叠加全部 30 个发布版本（94 个配置）；不同子评测保留自己的单位与口径。",
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

  // Quadrant bounds come from the data: median score of every measured effort for this task, and
  // either the median cost or a personal budget. Hand-set constants used to favor the cheapest family.
  function taskQuadrant(taskDef, activeReleases) {
    const pts = activeReleases.flatMap(r => r.variants).filter(v => finite(v.costPerTask) && v.costPerTask > 0 && finite(taskDef.getScore(v)));
    const mode = $("taskQuadMode")?.value || "median";
    const medCost = medianOf(pts.map(v => v.costPerTask)), medScore = medianOf(pts.map(v => taskDef.getScore(v)));
    const budget = mode === "median" ? medCost : Number(mode);
    return {x: finite(budget) ? budget : taskDef.attractiveX, y: finite(medScore) ? medScore : taskDef.attractiveY, byBudget: mode !== "median", medCost};
  }
  function renderTaskCategoryCards(taskDef, activeReleases, quad = taskQuadrant(taskDef, activeReleases)) {
    const el = $("taskCategoryCards");
    if (!el) return;
    const allVars = activeReleases.flatMap(rel => rel.variants.map(v => ({rel, v, score:taskDef.getScore(v)}))).filter(x => finite(x.score) && finite(x.v.costPerTask));
    if (!allVars.length) { el.innerHTML = ""; return; }
    const bestOverall = [...allVars].sort((a,b) => (b.score - a.score) || (a.v.costPerTask - b.v.costPerTask))[0];
    const inQuad = allVars.filter(x => x.v.costPerTask <= quad.x && x.score >= quad.y);
    const bestQuad = (inQuad.length ? inQuad : allVars.filter(x => x.v.costPerTask <= quad.x)).sort((a,b) => (b.score - a.score) || (a.v.costPerTask - b.v.costPerTask))[0] || bestOverall;
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
        desc: `耗时 ${fmt(bestOverall.v.timePerTaskMinutes, 2)} 分钟 · AA 智能指数 ${fmt(bestOverall.v.intelligenceIndex, 1)}`
      },
      {
        title: `优选象限冠军（Most Attractive ≤ ${money(quad.x)}）`,
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
    el.innerHTML = `<div class="topline"><h3><span class="swatch" style="display:inline-block;background:${rel.color};margin-right:7px"></span>${esc(rel.name)} · 全推理档位 × 主流任务实测明细（当前档位：${esc(v.effort)}）</h3><span class="tag">${esc(rel.vendor)} · ${rel.variants.length} 个已测档位 · ${v.evalSourceUrl ? link(v.evalSourceUrl, "AA 比较页来源") : "AA v4.3.2"}</span></div><div class="numbers"><div><b>${fmt(score, taskDef.digits)}${taskDef.unit}</b><span>当前维度：${esc(taskDef.shortLabel)}</span></div><div><b>${fmt(v.intelligenceIndex, 1)}</b><span>AA 智能指数</span></div><div><b>${money(v.costPerTask)}</b><span>单任务加权成本</span></div><div><b>${fmt(v.timePerTaskMinutes, 2)} 分钟</b><span>每任务推算耗时（${fmt(v.outputTokensPerTask, 0)} tok）</span></div></div><div class="table-scroll" style="margin-top:10px">${table(["推理档位","当前维度得分 / 升档差分","AA 智能指数","复杂问题：HLE / CritPt","编程工程：Terminal / SciCode","规划与代理：Briefcase / GDPval / AutoBench","知识与文档：LCR / PDF / Omniscience","单任务成本 / 耗时 / 输出 Token"], rowsHtml)}</div>`;
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
    const quad = taskQuadrant(taskDef, activeReleases);
    renderTaskCategoryCards(taskDef, activeReleases, quad);
    if ($("taskQuadHint")) $("taskQuadHint").textContent = `左上浅绿区域为 Most attractive quadrant：分数 ≥ 本任务全部档位的中位数 ${fmt(quad.y, taskDef.digits)}${taskDef.unit}，单任务成本 ≤ ${money(quad.x)}${quad.byBudget ? "（按你的预算）" : "（全部档位成本中位数）"} · 点击圆点或胶囊聚焦该模型`;

    $("taskEffortPills").innerHTML = activeReleases.map(r => {
      const col = getReleaseColor(r, colorMode);
      const topV = bestTaskVariant(r, taskDef) || r.variants[r.variants.length - 1];
      const sc = taskDef.getScore(topV);
      return `<button type="button" class="pill-btn ${r.releaseSlug === taskEffortState.selectedReleaseId ? "is-active" : ""}" data-task-pill="${esc(r.releaseSlug)}"><span class="swatch" style="background:${col}"></span>${esc(r.shortName || r.name)} <span class="small">(${fmt(sc, taskDef.digits)}${taskDef.unit})</span></button>`;
    }).join("") + (taskEffortState.focus ? `<button type="button" class="pill-btn pill-reset" id="taskFocusReset">显示全部模型</button>` : "");
    $("taskEffortPills").querySelectorAll("[data-task-pill]").forEach(btn => btn.addEventListener("click", () => {
      const same = taskEffortState.focus && taskEffortState.selectedReleaseId === btn.dataset.taskPill;
      taskEffortState.selectedReleaseId = btn.dataset.taskPill;
      taskEffortState.selectedVariantSlug = null;
      taskEffortState.focus = !same;
      renderTaskEffortChart();
    }));
    $("taskFocusReset")?.addEventListener("click", () => { taskEffortState.focus = false; renderTaskEffortChart(); });

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
      qx: x(Math.min(Math.max(quad.x, lo), hi)),
      qy: y(Math.min(Math.max(quad.y, ymin), ymax)),
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
      parts.push(`<polyline points="${frontier.map(p => `${x(p.v.costPerTask)},${y(p.score)}`).join(" ")}" fill="none" stroke="#111827" stroke-width="2.1" stroke-dasharray="2.5 3.5" opacity="${taskEffortState.focus ? 0.35 : 1}"/>`);
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
      const focused = taskEffortState.focus && isSel, dimmed = taskEffortState.focus && !isSel;
      const linePts = pts.map(p => `${x(p.v.costPerTask)},${y(p.score)}`).join(" ");
      const poly = pts.length > 1
        ? (focused ? `<polyline class="release-halo" points="${linePts}" fill="none" stroke="#fffef9" stroke-width="9" stroke-linejoin="round" stroke-linecap="round"/>` : "") +
          `<polyline class="release-line" points="${linePts}" fill="none" stroke="${col}" stroke-width="${focused ? 4 : isSel ? 3.2 : 2.1}" stroke-linejoin="round" opacity="${isSel ? 1 : 0.82}"/>` +
          `<polyline class="release-hit" points="${linePts}" fill="none" stroke="transparent" stroke-width="12" stroke-linejoin="round"/>`
        : "";
      const dots = pts.map((p, idx) => {
        const cx = x(p.v.costPerTask), cy = y(p.score);
        const isPrimary = p.v === bestTaskVariant(rel, taskDef) || pts.length === 1;
        const r = isPrimary ? (isSel ? 6.8 : 5.6) : (isSel ? 5.2 : 4.3);
        const effTag = isSel && pts.length > 1 ? `<text class="effort-tag" x="${cx}" y="${focused && idx % 2 ? cy + r + 13 : cy - r - 4}" text-anchor="middle" font-size="${focused ? 11 : 9.5}" font-weight="700" fill="${col}">${esc(EFFORT_SHORT[p.v.effort] || p.v.effort)}${focused ? " · " + fmt(p.score, taskDef.digits) : ""}</text>` : "";
        return `<g class="task-dot" tabindex="0" role="button" data-task-rel="${esc(rel.releaseSlug)}" data-task-var="${esc(p.v.slug)}" aria-label="${esc(p.v.name + "，" + taskDef.shortLabel + " " + fmt(p.score, taskDef.digits) + taskDef.unit + "，成本 " + money(p.v.costPerTask))}"><title>${esc(p.v.name + " · " + taskDef.shortLabel + " " + fmt(p.score, taskDef.digits) + taskDef.unit + " · 单任务 " + money(p.v.costPerTask) + " · 耗时 " + fmt(p.v.timePerTaskMinutes, 2) + "m")}</title><circle cx="${cx}" cy="${cy}" r="${r}" fill="${isPrimary ? col : "#ffffff"}" stroke="${col}" stroke-width="${isPrimary ? 2.2 : 1.9}"/>${effTag}</g>`;
      }).join("");
      parts.push(`<g class="release-series ${isSel ? "is-highlighted" : ""} ${focused ? "is-focused" : ""} ${dimmed ? "is-dimmed" : ""}" data-series="${esc(rel.releaseSlug)}">${poly}${dots}</g>`);
      const labelPt = [...pts].sort((a,b) => b.score - a.score || a.v.costPerTask - b.v.costPerTask)[0];
      const suffix = focusEffort !== "all" ? ` (${labelPt.v.effort})` : "";
      topLabels.push({rel, col, v:labelPt.v, score:labelPt.score, text:(rel.shortName || rel.name) + suffix, cx:x(labelPt.v.costPerTask), cy:y(labelPt.score), ly:y(labelPt.score), isSel, dim:dimmed});
    });

    renderSmartLabels(parts, topLabels, {width, height, margin, minGap:15, xSpan:135});

    svg.innerHTML = parts.join("");
    svg.querySelectorAll(".task-dot").forEach(dot => {
      const select = () => {
        taskEffortState.selectedReleaseId = dot.dataset.taskRel;
        taskEffortState.selectedVariantSlug = dot.dataset.taskVar;
        taskEffortState.focus = true;
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
    ["taskEffortMode", "taskEffortFocus", "taskColorMode", "taskEffortBackdrop", "taskQuadMode"].forEach(id => $(id)?.addEventListener("change", renderTaskEffortChart));
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

  // BEGIN SCALING_MATH
  const OSWORLD_SWEEP_PROTOCOL = "osworld-2.0-offline-v2026.08.08-partial";
  function osworldSweepPoints(sweep) {
    return sweep.series.flatMap(s=>sweep.efforts.map((effort,i)=>({
      id:s.modelId+":"+effort, modelId:s.modelId, model:s.model, effort,
      score:s.scores[i], cost:s.costUsdPerTask[i], protocolId:sweep.protocolId,
      benchmark:sweep.benchmark, release:sweep.release, subset:sweep.subset,
      metric:sweep.metric, scoreUnit:sweep.scoreUnit, costDefinition:sweep.costDefinition,
      sourceUrl:sweep.source, provenance:sweep.provenance, checkedAt:sweep.checkedAt,
      harness:sweep.harness, maxSteps:sweep.maxSteps, runs:sweep.runs, ci:sweep.ci
    })));
  }
  function scalingRows(points, efforts) {
    return efforts.map((effort,i)=>{
      const p=points.find(p=>p.effort===effort), previous=points.find(p=>p.effort===efforts[i-1]);
      const score=finite(p?.score) ? p.score : null, cost=finite(p?.cost) ? p.cost : null;
      return {effort,score,cost,sourceUrl:p?.sourceUrl || null,
        deltaScore:finite(score) && finite(previous?.score) ? score-previous.score : null,
        deltaCost:finite(cost) && finite(previous?.cost) ? cost-previous.cost : null,
        deltaCostPct:finite(cost) && finite(previous?.cost) && previous.cost>0 ? (cost-previous.cost)/previous.cost*100 : null};
    });
  }
  function scalingPath(points, efforts, x, y) {
    let path="", previous=-2;
    efforts.forEach((effort,i)=>{
      const p=points.find(p=>p.effort===effort);
      if(!finite(p?.score)) { previous=-2; return; }
      path+=`${previous===i-1 ? "L" : "M"}${x(i)},${y(p.score)} `;previous=i;
    });
    return path.trim();
  }
  function observedAlternatives(points, current) {
    if(current.protocolId!==OSWORLD_SWEEP_PROTOCOL || !finite(current.score) || !finite(current.cost) || current.cost<0) return [];
    const scope=["protocolId","benchmark","release","subset","metric","scoreUnit","costDefinition","sourceUrl","provenance","harness","maxSteps","runs","statistic"];
    const alternatives=points.filter(p=>p.id!==current.id && scope.every(k=>p[k]===current[k]) &&
      finite(p.score) && finite(p.cost) && p.cost>=0 && p.score>=current.score && p.cost<=current.cost &&
      (p.score>current.score || p.cost<current.cost));
    const tie=(a,b)=>a.id.localeCompare(b.id);
    const cheapest=[...alternatives].sort((a,b)=>a.cost-b.cost || b.score-a.score || tie(a,b))[0];
    const highest=[...alternatives].sort((a,b)=>b.score-a.score || a.cost-b.cost || tie(a,b))[0];
    return [...new Map([cheapest,highest].filter(Boolean).map(p=>[p.id,p])).values()];
  }
  // END SCALING_MATH

  // Enhance the existing cross-model chart; pinned and transient emphasis are separate.
  const scalingState={pinned:null,hover:null,focused:null};
  const scalingIsOS = () => $("effortScalingTask").value==="osworld2";
  function scalingContext() {
    const isOS=scalingIsOS(), sweep=DATA.computer_use_evidence.openaiSweep;
    const taskKey=$("effortScalingTask").value;
    const task=isOS ? {shortLabel:"OSWorld 2.0 · offline · v2026.08.08 · 部分得分（partial reward）",unit:"%",digits:2,yLabel:"部分得分（partial reward · %）",yrange:[0,100],yTicks:[0,20,40,60,80,100]} : TASK_DEFINITIONS[taskKey] || TASK_DEFINITIONS.complex;
    const efforts=isOS ? sweep.efforts : EFFORT_ORDER;
    const osPoints=osworldSweepPoints(sweep);
    const active=DATA.aa_release_series.releases.filter(r=>r.variants.some(v=>v.taskScores) || (isOS && osPoints.some(p=>p.modelId===r.releaseSlug)));
    const fam=$("effortScalingFamily").value;
    const models=active.filter(r=>fam==="all" || r.vendor===fam).map(r=>({...r,points:isOS ? osPoints.filter(p=>p.modelId===r.releaseSlug) :
      r.variants.map(v=>({effort:v.effort,score:task.getScore(v),cost:taskKey==="intelligenceIndex" ? v.costPerTask : null,sourceUrl:v.evalSourceUrl || r.sourceUrl}))}));
    return {isOS,sweep,task,efforts,models};
  }
  function renderScalingDetail(context=scalingContext()) {
    const {models,efforts,task,isOS}=context, id=scalingState.pinned;
    const model=models.find(r=>r.releaseSlug===id) || DATA.aa_release_series.releases.find(r=>r.releaseSlug===id);
    const points=models.find(r=>r.releaseSlug===id)?.points || [];
    if(!id) { $("effortScalingDetail").innerHTML='<p>总览：点击模型图例或选择模型可固定高亮，并在此查看原始分数与相邻档位差分。悬停或键盘聚焦只临时强调。</p>';return; }
    const valid=points.filter(p=>finite(p.score)), rows=scalingRows(points,efforts);
    const text=valid.length===0 ? "此口径暂无数据；不补零、不推断档位。" : valid.length===1 ? "仅 1 个已测点，不能建立档位曲线或上升结论。" : "只连接相邻且有实测分数的档位；缺档不连线、不计算跨档差分。";
    $("effortScalingDetail").innerHTML=`<h4>${esc(model?.name || id)} · ${esc(task.shortLabel)}</h4><p>${text}</p><div class="table-scroll">${table(["原生档位","原始分数","相邻档位分差","同口径 USD/task","相邻成本变化","该指标来源"],rows.map(r=>`<tr data-effort="${r.effort}"><th>${r.effort}</th><td>${finite(r.score)?fmt(r.score,2)+task.unit:'无数据'}</td><td>${finite(r.deltaScore)?(r.deltaScore>0?'+':'')+fmt(r.deltaScore,2)+(task.unit==='%'?' pp':task.unit):'无可比相邻值'}</td><td>${finite(r.cost)?(isOS?'$'+fmt(r.cost,4):money(r.cost)):'未提供'}</td><td>${finite(r.deltaCostPct)?(r.deltaCostPct>0?'+':'')+fmt(r.deltaCostPct,2)+'%':'未提供'}</td><td>${r.sourceUrl && finite(r.score)?link(r.sourceUrl,'原始来源'):'无该指标来源'}</td></tr>`).join(''))}</div><p class="small">${isOS?'厂商自报（provider-reported）；费用是同次评测的 USD/task，不是每成功任务成本或本机实际账单；重复次数、harness、最大步数和置信区间均未提供。':'AA 原始单位各守口径；任务视图含既有自定义合成项，不能与具名子评测混同。只有 AA 智能指数保留其综合加权成本。'} 分差中性展示，不强制单调，不代表显著性。</p>`;
  }
  function updateScalingEmphasis() {
    const effective=scalingState.focused || scalingState.hover || scalingState.pinned;
    $("effortScalingChart").dataset.pinned=scalingState.pinned || '';
    $("effortScalingChart").dataset.emphasis=effective || '';
    $("effortScalingLegend").querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.scaleModel===scalingState.pinned)));
    $("effortScalingChart").querySelectorAll('[data-scale-series]').forEach(g=>{
      const active=g.dataset.scaleSeries===effective;
      g.style.opacity=effective && !active ? '.2' : '1';
      g.querySelector('path')?.setAttribute('stroke-width',active?'4':'1.8');
      g.querySelectorAll('circle').forEach(c=>{c.setAttribute('r',active?'7':'4.5');c.setAttribute('fill',active?g.dataset.color:'#fffef9');});
      g.querySelectorAll('.scaling-dot').forEach(d=>d.setAttribute('aria-pressed',String(g.dataset.scaleSeries===scalingState.pinned)));
      g.querySelectorAll('.scaling-score').forEach(t=>t.setAttribute('opacity',active?'1':'0'));
    });
    $("effortScalingChart").querySelectorAll('[data-scale-label]').forEach(label=>{
      label.style.opacity=effective && label.dataset.scaleLabel!==effective ? '.2' : '1';
    });
    $("effortScalingTable").querySelectorAll('[data-scaling-row]').forEach(r=>r.classList.toggle('recommended-controller',r.dataset.scalingRow===scalingState.pinned));
    $("effortScalingModel").value=scalingState.pinned || '';
  }
  function pinScalingModel(id) {
    scalingState.pinned=id && id!==scalingState.pinned ? id : null;
    scalingState.hover=null;scalingState.focused=null;
    updateScalingEmphasis();renderScalingDetail();
  }
  function bindScalingInteractions() {
    const nodes=document.querySelectorAll('#effortScalingLegend [data-scale-model],#effortScalingChart .scaling-dot');
    nodes.forEach(n=>{
      const id=n.dataset.scaleModel || n.dataset.scaleRel;
      n.addEventListener('pointerenter',()=>{scalingState.hover=id;updateScalingEmphasis();});
      n.addEventListener('pointerleave',()=>{scalingState.hover=null;updateScalingEmphasis();});
      n.addEventListener('focus',()=>{scalingState.focused=id;updateScalingEmphasis();});
      n.addEventListener('blur',()=>{scalingState.focused=null;updateScalingEmphasis();});
      n.addEventListener('click',()=>pinScalingModel(id));
      if(n.classList.contains('scaling-dot')) n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();pinScalingModel(id);}});
    });
  }
  function renderEffortScalingChart() {
    const svg=$("effortScalingChart");if(!svg)return;
    const context=scalingContext(),{models,efforts,task,isOS,sweep}=context;
    scalingState.hover=null;scalingState.focused=null;
    if(scalingState.pinned && !models.some(r=>r.releaseSlug===scalingState.pinned) && $("effortScalingFamily").value!=='all') scalingState.pinned=null;
    $("effortScalingModel").innerHTML='<option value="">总览 · 不固定高亮</option>'+DATA.aa_release_series.releases.filter(r=>$("effortScalingFamily").value==="all" || r.vendor===$("effortScalingFamily").value).map(r=>`<option value="${r.releaseSlug}">${esc(r.name)}</option>`).join('');
    $("effortScalingLegend").innerHTML=models.map(r=>`<button type="button" class="aa-legend-item" data-scale-model="${r.releaseSlug}" aria-pressed="false"><span class="aa-vendor-dot" style="background:${r.color}"></span>${esc(r.shortName || r.name)}${r.points.some(p=>finite(p.score))?'':' · 此口径暂无数据'}</button>`).join('');
    $("effortScalingScope").innerHTML=`${esc(task.shortLabel)}。原生档位是离散类别，不同模型的同名档位不等预算、不代表连续强度；不假定 non-reasoning 是每款模型的起点。${isOS?'厂商自报（provider-reported）。non-reasoning 未测，不补点。'+link(sweep.source,'发布页来源'):'缺少分数不连线。'}`;
    const width=Math.max(760,Math.round(svg.getBoundingClientRect().width || 1100)), height=440,m={left:68,right:145,top:40,bottom:60};
    const x=i=>m.left+i/Math.max(1,efforts.length-1)*(width-m.left-m.right);
    const [min,max]=task.yrange, y=v=>height-m.bottom-(v-min)/(max-min)*(height-m.top-m.bottom);
    svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.setAttribute('height',height);
    const parts=[`<title>各模型在已测推理档位下的成绩 · ${esc(task.shortLabel)}</title>`];
    task.yTicks.forEach(t=>parts.push(`<line x1="${m.left}" x2="${width-m.right}" y1="${y(t)}" y2="${y(t)}" stroke="#e3e9e1"/><text x="${m.left-10}" y="${y(t)+4}" text-anchor="end" class="tick">${t}</text>`));
    efforts.forEach((eff,i)=>parts.push(`<text x="${x(i)}" y="${height-35}" text-anchor="middle" class="tick">${eff}</text>`));
    parts.push(`<text x="${m.left}" y="20" class="axis-label">${esc(task.yLabel)}</text><text x="${width/2}" y="${height-10}" text-anchor="middle" class="axis-label">已测原生档位 · 离散类别 · 同名不等预算</text>`);
    const labels=[];
    models.forEach(r=>{
      const points=r.points.filter(p=>finite(p.score)).sort((a,b)=>efforts.indexOf(a.effort)-efforts.indexOf(b.effort));if(!points.length)return;
      const path=scalingPath(r.points,efforts,x,y);
      parts.push(`<g data-scale-series="${r.releaseSlug}" data-color="${r.color}" role="group" aria-label="${esc(r.name)}"><path d="${path}" fill="none" stroke="${r.color}" stroke-width="1.8"/>${points.map(p=>`<g class="scaling-dot" tabindex="0" role="button" aria-pressed="false" data-scale-rel="${r.releaseSlug}" data-effort="${p.effort}" data-score="${p.score}" aria-label="${esc(r.name+' · '+p.effort+' · '+fmt(p.score,2)+task.unit)}"><title>${esc(r.name+' · '+p.effort+' · '+fmt(p.score,2)+task.unit+(finite(p.cost)?' · 同评测 USD/task '+p.cost:''))}</title><circle cx="${x(efforts.indexOf(p.effort))}" cy="${y(p.score)}" r="4.5" fill="#fffef9" stroke="${r.color}" stroke-width="2"/><text class="scaling-score" x="${x(efforts.indexOf(p.effort))}" y="${y(p.score)-12}" text-anchor="middle" font-size="11" fill="${r.color}" opacity="0">${fmt(p.score,2)}</text></g>`).join('')}</g>`);
      const last=points[points.length-1];
      labels.push({scaleModel:r.releaseSlug,text:r.shortName || r.name,col:r.color,cx:x(efforts.indexOf(last.effort)),cy:y(last.score),isSel:false});
    });
    renderSmartLabels(parts,labels,{width,height,margin:m,minGap:18,xSpan:145});
    svg.innerHTML=parts.join('');
    $("effortScalingTable").innerHTML=table(['模型 · 点击图例固定高亮',...efforts],models.map(r=>`<tr data-scaling-row="${r.releaseSlug}"><th>${esc(r.name)}</th>${scalingRows(r.points,efforts).map(p=>`<td>${finite(p.score)?fmt(p.score,2)+task.unit:'无数据'}</td>`).join('')}</tr>`).join(''));
    bindScalingInteractions();updateScalingEmphasis();renderScalingDetail(context);
  }
  if($("effortScalingTask")) {
    ['effortScalingTask','effortScalingFamily'].forEach(id=>$(id).addEventListener('change',renderEffortScalingChart));
    $("effortScalingModel").addEventListener('change',()=>pinScalingModel($("effortScalingModel").value));
    $("resetScalingHighlight").addEventListener('click',()=>{scalingState.pinned=null;scalingState.hover=null;scalingState.focused=null;updateScalingEmphasis();renderScalingDetail();});
    $("exportEffortScaling").addEventListener('click',()=>{
      const {models,efforts,task,isOS,sweep}=scalingContext();
      const rows=models.map(r=>{
        const out={model:r.name,task_dimension:task.shortLabel};
        scalingRows(r.points,efforts).forEach(p=>{out[p.effort+'_score']=p.score;out[p.effort+'_cost_usd']=p.cost;});
        if(isOS) Object.assign(out,{benchmark:sweep.benchmark,release:sweep.release,subset:sweep.subset,metric:sweep.metric,score_unit:sweep.scoreUnit,cost_definition:sweep.costDefinition,provenance:r.points.some(p=>finite(p.score))?sweep.provenance:'未测',source_url:r.points.some(p=>finite(p.score))?sweep.source:null,harness:sweep.harness,max_steps:sweep.maxSteps,runs:sweep.runs,ci:sweep.ci,checked_at:sweep.checkedAt});
        return out;
      });
      exportCSV(rows,'各模型已测档位成绩-2026-10-20.csv');
    });
  }

  function renderComputerUseEvidence() {
    const evidence=DATA.computer_use_evidence,a=evidence.anthropicMax,g=evidence.geminiReference;
    const refs=a.sourceRefs.map(s=>`${link(s.sourceUrl,'系统卡 pp. '+s.pages[0]+'–'+s.pages[s.pages.length-1])}（原文名称 ${esc(s.originalBenchmarkName)}）`).join(' · ');
    $("computerUseEvidence").innerHTML=`<section class="card computer-use-panel" id="computerUseMax"><h3>${esc(a.displayLabel)}</h3><p>独立 max 单点 · 厂商自报（provider-reported）。与上方 OpenAI 2.0 offline 曲线分开；按版本日期与完整协议识别，保留各文档的原始命名。</p><div class="table-scroll">${table(['模型','已测档位','部分得分（partial reward）','严格成功率（strict success rate）'],a.rows.map(r=>`<tr data-computer-model="${r.modelId}"><th>${esc(r.model)}</th><td>max · 单点</td><td>${fmt(r.partialRewardPct,1)}%</td><td>${fmt(r.strictSuccessRatePct,1)}%</td></tr>`).join(''))}</div><p>仅 max 档，不能建立 effort 曲线。部分得分与严格成功率分别保留，不互换。</p><details open><summary>来源与完整协议 · 核对 ${a.checkedAt}</summary><p>${refs}</p><p>${a.release} 全套 ${a.tasks} 任务；${a.resolution}；${a.maxSteps} action steps；${a.runs} 次独立运行的均值；grader ${esc(a.grader)}；所有截图保留；100k-token 服务端压缩。费用与置信区间未提供。</p></details></section>
      <section class="card computer-use-panel" id="computerUseGemini"><h3>独立参考 · Gemini 4 Argon</h3><p>厂商自报（provider-reported）：${esc(g.benchmark)} · ${esc(g.subset)} · ${esc(g.release)} · 部分得分（partial reward）<strong>${fmt(g.partialRewardPct,1)}%</strong>。</p><p><strong>3 次运行取最大值</strong>，不同于均值，单独参考，不叠加到其他曲线或替代组合。最高 thinking 设置的原生 effort 未核验，保持未知。</p><p>500 steps · 1080p · screenshot + pyautogui · Gemini CUA harness · batch tools / compaction。费用与置信区间未提供；核对 ${g.checkedAt}。</p><p>${g.sources.map(url=>link(url,'原始来源')).join(' · ')}</p></section>
      <section class="card computer-use-panel" id="computerUseGrok"><h3>Grok 4.7 · Computer Use</h3><p>${esc(evidence.grokReference.status)}；不填零，不据此断言不支持。</p><p>${link(evidence.grokReference.sourceUrl,'厂商发布页')} · 核对 ${evidence.grokReference.checkedAt}</p></section><p class="method-note">桌面 Computer Use 与 WebArena 等浏览器任务属于不同任务类。旧 OSWorld-Verified 二元成功率、以上不同版本、统计量，以及部分得分与严格成功率这两个指标分别参考，不拼成通用 Computer Use 总分。</p>`;
  }
  function renderObservedConfig(id) {
    const sweep=DATA.computer_use_evidence.openaiSweep,points=osworldSweepPoints(sweep),current=points.find(p=>p.id===id);
    if(!current)return;
    const alternatives=observedAlternatives(points,current), series=points.filter(p=>p.modelId===current.modelId);
    const row=scalingRows(series,sweep.efforts).find(r=>r.effort===current.effort);
    const signed=v=>(v>0?'+':'')+fmt(v,2);
    const relation=p=>p.modelId!==current.modelId ? '跨模型切换配置' : sweep.efforts.indexOf(p.effort)<sweep.efforts.indexOf(current.effort) ? '同模型较低档替代' : '同模型切换配置';
    $("pitfallObservedDetail").innerHTML=`<h4>${esc(current.model)} · ${current.effort} · 部分得分 ${fmt(current.score,2)}% · $${fmt(current.cost,4)}/task</h4><p>${finite(row.deltaScore)?'相邻档位 → 当前档：分数 '+signed(row.deltaScore)+' pp；成本 '+signed(row.deltaCostPct)+'%（以前一档成本为分母）。':'起始已测档：没有前一档可比差分。'}</p>${alternatives.length?`<p><strong>本次评测中存在更优替代</strong> · 最多列两项：达到当前分数的最低费用配置、当前预算内最高分配置；相同配置去重。</p><ul>${alternatives.map(p=>`<li data-alternative="${p.id}"><strong>${relation(p)}</strong>：${esc(p.model)} · ${p.effort}，${fmt(p.score,2)}%，$${fmt(p.cost,4)}/task；分数 ${signed(p.score-current.score)} pp，费用节省 ${current.cost>0?fmt((current.cost-p.cost)/current.cost*100,2)+'%':'不适用'}（以当前配置费用为分母）。</li>`).join('')}</ul>`:'<p>本组观测未发现同时更便宜且不低分的替代。仅报告相邻分数增量和追加成本，不判定任务最优或低性价比。</p>'}`;
  }
  function renderPitfallGuide() {
    const evidence=DATA.computer_use_evidence,sweep=evidence.openaiSweep,points=osworldSweepPoints(sweep);
    const cards=(items)=>items.map(c=>`<article class="experience-card" data-experience-card="${esc(c.id)}"><h4>${esc(c.title)}</h4><p><strong>坑：</strong>${esc(c.pitfall)}</p><p><strong>动作：</strong>${esc(c.alternativeAction)}</p><details><summary>来源与适用边界</summary><p>${esc(c.evidenceType)} · 核对 ${esc(c.checkedAt)}</p><p>模型：${esc(c.modelScope)}；任务：${esc(c.taskScope)}；版本：${esc(c.versionScope)}。</p><ul>${c.caveats.map(text=>`<li>${esc(text)}</li>`).join('')}</ul><ul>${c.sources.map(s=>`<li>${link(s.sourceUrl,s.label)}<p class="small">${esc(s.sourceType)} · ${esc(s.caveats)}</p></li>`).join('')}</ul></details></article>`).join('');
    $("pitfallGuide").innerHTML=`<h3>避坑指南</h3><p>实测参考、多源经验和待验证提醒分层；不做模型黑名单，不与任务经验起点合成分数。</p><section id="pitfallObserved"><h4>实测参考 · 可替代组合</h4><p>仅限 OSWorld 2.0 · offline · v2026.08.08 · 部分得分（partial reward），15 个完整分数/费用点，厂商自报。按原始精度判断分数不低且费用不高、至少一项严格改善；显示时才舍入。${link(sweep.source,'发布页来源')}</p><label>当前配置<select id="pitfallConfig">${points.map(p=>`<option value="${p.id}">${esc(p.model)} · ${p.effort}</option>`).join('')}</select></label><div id="pitfallObservedDetail" aria-live="polite"></div><p class="method-note">仅是本次评测的已发布观测；缺少置信区间与重复次数元数据，0.15 pp 等小差异也不能推断显著优越。没有延迟数据，不声称更快。USD/task 不是每成功任务费用或本地账单；分数是 partial reward，不是成功率。缺少费用不能判断更便宜。跨模型只比较配置，不推断品牌档次。</p><details><summary>全部 15 个配置的观测状态</summary><div class="table-scroll">${table(['配置','部分得分 %','同评测 USD/task','观测状态'],points.map(p=>`<tr data-observed-config="${p.id}"><th>${esc(p.model)} · ${p.effort}</th><td>${fmt(p.score,2)}</td><td>$${fmt(p.cost,4)}</td><td>${observedAlternatives(points,p).length?'本次评测中存在更优替代':'未发现同时更便宜且不低分的替代'}</td></tr>`).join(''))}</div></details></section><section id="pitfallExperience"><h4>多源经验参考</h4>${evidence.pitfallExperience.cards.length?cards(evidence.pitfallExperience.cards):'<p>待补充核验文案。需要至少两个独立原始来源收敛；同一文章的转载不计作两个来源。暂无满足条件的经验卡。</p>'}</section><section id="pitfallReminders"><h4>待验证提醒</h4>${evidence.pitfallReminders.cards.length?cards(evidence.pitfallReminders.cards):'<p>待补充核验：需明确模型、任务、版本、适用条件与替代行动；当前未形成提醒卡。</p>'}</section>`;
    $("pitfallConfig").value='gpt-6-1-sol:xhigh';
    $("pitfallConfig").addEventListener('change',()=>renderObservedConfig($("pitfallConfig").value));
    renderObservedConfig($("pitfallConfig").value);
  }
  renderComputerUseEvidence();renderPitfallGuide();

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
    $("releaseDetail").innerHTML = `<div class="topline"><h3><span class="swatch" style="display:inline-block;background:${rel.color};margin-right:7px"></span>${esc(rel.name)}（当前选中档位：${esc(v.effort)}）</h3><span class="tag">${esc(rel.vendor)} · 共 ${rel.variants.length} 个档位点 · 发布 ${esc(rel.releaseDate || "2026")}</span></div><div class="numbers"><div><b>${fmt(v.intelligenceIndex,1)}</b><span>AA 智能指数</span></div><div><b>${money(v.costPerTask)}</b><span>单任务总成本</span></div><div><b>${fmt(v.timePerTaskMinutes,2)} 分钟</b><span>每任务平均耗时</span></div><div><b>${fmt(v.outputTokensPerTask,0)}</b><span>每任务输出 Token（思考 ${fmt(tb.reasoning,0)}）</span></div></div>${stackBar}<div class="table-scroll" style="margin-top:10px">${table(["同版本已测档位","AA 智能指数","单任务总成本","输入拆分：非缓存 / 缓存读 / 缓存写","输出拆分：思考 / 答案","每任务输出 Token","每任务耗时 / 吞吐"], rowsHtml)}</div>`;
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

    const parts = [`<title>按模型发布版本划分的 AA 智能指数 与 ${esc(xMeta.label)}</title>`];
    drawAAPlotChrome(parts, {
      width,
      height,
      margin,
      // Same rule as the overview chart: split at the medians of the plotted active points.
      qx: x(Math.min(Math.max(medianOf(activePoints.map(p => p.v[xKey])) || xMeta.attractiveX, lo), hi)),
      qy: y(Math.min(Math.max(medianOf(activePoints.map(p => p.v.intelligenceIndex)) || 42.5, ymin), ymax)),
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
    parts.push(`<text x="${margin.left}" y="18" class="axis-label">AA 智能指数（分）</text><text x="${(margin.left + width - margin.right)/2}" y="${height - 12}" text-anchor="middle" class="axis-label">${esc(xMeta.label)} · 对数刻度</text>`);

    backdropReleases.forEach(rel => {
      const col = getReleaseColor(rel, colorMode);
      const pts = filterVars(rel);
      if (viewMode === "trajectories" && pts.length > 1) {
        parts.push(`<polyline points="${pts.map(v => `${x(v[xKey])},${y(v.intelligenceIndex)}`).join(" ")}" fill="none" stroke="${col}" stroke-width="1.3" opacity="0.28"/>`);
      }
      pts.forEach(v => {
        parts.push(`<circle cx="${x(v[xKey])}" cy="${y(v.intelligenceIndex)}" r="3.6" fill="${col}" opacity="0.42"><title>${esc(v.name + " · AA 智能指数 " + fmt(v.intelligenceIndex,1) + " · " + fmt(v[xKey],3))}</title></circle>`);
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
        return `<g class="release-dot" tabindex="0" role="button" data-rel-id="${esc(rel.releaseSlug)}" data-var-id="${esc(v.slug)}" aria-label="${esc(v.name + "，AA 智能指数 " + fmt(v.intelligenceIndex,1))}"><title>${esc(v.name + " · AA 智能指数 " + fmt(v.intelligenceIndex,1) + " · 单任务 " + money(v.costPerTask) + " · 耗时 " + fmt(v.timePerTaskMinutes,2) + "m")}</title><circle cx="${cx}" cy="${cy}" r="${r}" fill="${v.isTopVariant ? col : "#ffffff"}" stroke="${col}" stroke-width="${v.isTopVariant ? 2.2 : 1.8}"/></g>`;
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
  // Personal effort sweet-spot matrix: lowest-cost measured effort within a tolerance of each model's best score.
  const sweetTasks=[
    {key:"ii",label:"综合",sub:"AA 智能指数",get:v=>v.intelligenceIndex,elo:false},
    {key:"coding",label:"编程",sub:"Terminal-Bench + SciCode",get:v=>v.taskScores?.coding,elo:false},
    {key:"complex",label:"复杂推理",sub:"HLE + CritPt",get:v=>v.taskScores?.complex,elo:false},
    {key:"automation",label:"工具自动化",sub:"AutomationBench",get:v=>v.taskScores?.automation,elo:false},
    {key:"agentic",label:"知识工作交付",sub:"GDPval Elo",get:v=>v.taskScores?.agentic,elo:true},
    {key:"planning",label:"方案规划",sub:"Briefcase Elo",get:v=>v.taskScores?.planning,elo:true},
    {key:"knowledge",label:"长文档 · 事实",sub:"LCR / PDF / Omniscience",get:v=>v.taskScores?.knowledge,elo:false}
  ];
  // Minimum gain per doubling of cost, as a share of the column's score spread across all measured configs.
  const sweetTolerance={thrifty:{share:.20,label:"省钱"},balanced:{share:.12,label:"均衡"},performance:{share:.06,label:"性能优先"}};
  const vendorOrder=["Anthropic","OpenAI","Google","xAI"];
  const sweetView={model:null,task:null};
  const sweetReleases=()=>(DATA.aa_release_series?.releases||[]).filter(r=>r.variants.some(v=>v.taskScores))
    .sort((a,b)=>(vendorOrder.indexOf(a.vendor)-vendorOrder.indexOf(b.vendor))||((b.maxIntelligenceIndex||0)-(a.maxIntelligenceIndex||0)));
  const sweetSpan=new Map();
  function sweetThreshold(task,tol,releases){
    if(!sweetSpan.has(task.key)){
      const vals=releases.flatMap(r=>r.variants.map(task.get)).filter(finite);
      sweetSpan.set(task.key,vals.length?Math.max(...vals)-Math.min(...vals):0);
    }
    return tol.share*sweetSpan.get(task.key);
  }
  // Shared knee search over [{score,cost}]: returns the chosen item or null when no costs exist.
  function upperHull(items){
    const pts=items.filter(x=>finite(x.cost)&&x.cost>0&&finite(x.score)).map(x=>({x,lx:Math.log2(x.cost)})).sort((a,b)=>a.lx-b.lx||b.x.score-a.x.score);
    const hull=[];
    pts.forEach(p=>{
      if(hull.length&&p.lx===hull[hull.length-1].lx) return;
      while(hull.length>=2){const a=hull[hull.length-2],b=hull[hull.length-1];if((b.x.score-a.x.score)*(p.lx-a.lx)<=(p.x.score-a.x.score)*(b.lx-a.lx))hull.pop();else break;}
      hull.push(p);
    });
    return hull;
  }
  function kneeOf(items,threshold){
    const hull=upperHull(items);
    if(!hull.length) return null;
    let cur=hull[0];
    for(const next of hull.slice(1)){if((next.x.score-cur.x.score)/(next.lx-cur.lx)<threshold)break;cur=next;}
    return cur.x;
  }
  // Knee rule: walk the upper hull of (log2 cost, score) from the cheapest effort and keep
  // stepping up while each step still gains at least `threshold` points per doubling of cost.
  function sweetPick(release,task,tol,releases){
    const vs=release.variants.map(v=>({v,score:task.get(v),cost:v.costPerTask})).filter(x=>finite(x.score)).sort((a,b)=>a.v.effortOrder-b.v.effortOrder);
    if(!vs.length) return null;
    const best=Math.max(...vs.map(x=>x.score)), top=vs[vs.length-1], peak=vs.find(x=>x.score===best);
    const threshold=sweetThreshold(task,tol,releases);
    const pick=kneeOf(vs,threshold)||peak;
    return {vs,best,pick,top,peak,threshold,topDrop:vs.length>1&&top.score<best-(task.elo?10:0.5),single:vs.length===1};
  }
  function sweetCheaper(task,pick,releases,selfSlug){
    if(!finite(pick.cost)) return null;
    let alt=null;
    releases.forEach(r=>{if(r.releaseSlug===selfSlug) return;r.variants.forEach(v=>{const sc=task.get(v);if(finite(sc)&&finite(v.costPerTask)&&sc>=pick.score&&v.costPerTask<=pick.cost*0.6&&(!alt||v.costPerTask<alt.cost))alt={release:r,v,score:sc,cost:v.costPerTask};});});
    return alt;
  }
  // A pick is dominated when another model's measured effort scores at least as high for no more money (and is strictly better on one).
  function sweetDominated(task,pick,releases,selfSlug){
    if(!finite(pick.cost)) return false;
    return releases.some(r=>r.releaseSlug!==selfSlug&&r.variants.some(v=>{const sc=task.get(v);return finite(sc)&&finite(v.costPerTask)&&sc>=pick.score&&v.costPerTask<=pick.cost&&(sc>pick.score||v.costPerTask<pick.cost);}));
  }
  // Reference picks shown next to the benchmark knee: official/guide starting effort and community measurements.
  const guideTask={complex:["complex"],coding:["daily_code","repository_bug"],planning:["design"]};
  const guideTaskLabel={complex:"复杂问题",daily_code:"日常代码",repository_bug:"修 bug",design:"方案设计"};
  function sweetRefs(release,task,tol){
    const g=DATA.task_effort_guidance, model=(g?.models||[]).find(m=>m.modelId===release.releaseSlug);
    const recs=(g?.recommendations||[]).filter(r=>r.modelId===release.releaseSlug);
    const out={official:null,community:[]};
    const official=(guideTask[task.key]||[]).map(id=>recs.find(r=>r.taskType===id&&r.evidenceType!=="社区实测")).filter(Boolean);
    if(official.length){
      const r=official[0];
      out.official={effort:r.nativeEffort,kind:model?.officialDefault?"官方":"经验",url:r.support?.[0]?.sourceUrl||r.sourceUrl,
        note:official.map(x=>`${guideTaskLabel[x.taskType]} ${x.nativeEffort}`).join(" · ")+"；"+(r.caveats?.[0]||""),taskSpecific:true};
    } else if(model?.officialDefault){
      out.official={effort:model.officialDefault,kind:"官方",url:model.sourceUrl,note:`官方默认档位 ${model.officialDefault}（不分任务）。`,taskSpecific:false};
    }
    (guideTask[task.key]||[]).forEach(id=>recs.filter(r=>r.taskType===id&&r.evidenceType==="社区实测").forEach(r=>out.community.push({effort:r.nativeEffort,label:`${guideTaskLabel[id]}${/[a-z]$/i.test(guideTaskLabel[id])?" ":""}实测`,url:r.sourceUrl,note:(r.support||[]).find(x=>x.evidenceType==="社区实测")?.statement||r.caveats?.[0]||"",n:r.sampleSize})));
    if(task.key==="coding"){
      const rows=DATA.rows.filter(x=>x.benchmark==="coding"&&x.model===release.name&&finite(x.score));
      if(rows.length>1){
        const spread=(()=>{const v=DATA.rows.filter(x=>x.benchmark==="coding"&&finite(x.score)).map(x=>x.score);return Math.max(...v)-Math.min(...v);})();
        const k=kneeOf(rows.map(x=>({effort:x.effort,score:x.score,cost:x.cost_usd,row:x})),tol.share*spread);
        if(k) out.community.push({effort:k.effort,label:"Vulcan",url:k.row.source_url,n:k.row.n,
          note:`Vulcan 编码 ${k.row.n} 题，${k.effort} 通过 ${fmt(k.score,1)}%，每次尝试 ${money(k.cost)}；同一拐点规则。${rows.some(x=>x.variant==="mixed_fallback")?"部分档位含回退配置。":""}`,
          rows});
      }
    }
    return out;
  }
  function sweetAdvice(pick,refs){
    const order=["non-reasoning","minimal","low","medium","high","xhigh","max"];
    const o=refs.official, comm=refs.community;
    if(!o&&!comm.length) return "";
    const same=comm.filter(c=>c.effort===pick), diff=comm.filter(c=>c.effort!==pick);
    const commText=(same.length?`社区实测（${same.map(c=>c.label).join("、")}）也指向 ${pick}。`:"")+(diff.length?`社区实测（${diff.map(c=>c.label+" "+c.effort).join("、")}）与拐点不同，值得用自己的任务对比。`:"");
    if(!o) return `评测拐点是 ${pick}。${commText}`;
    if(o.effort===pick) return `${o.kind}起点与评测拐点都是 ${pick}，直接用它。${commText}`;
    const up=order.indexOf(pick)>order.indexOf(o.effort);
    return (up ? `从${o.kind} ${o.effort} 起步；交付不达标时再升到评测拐点 ${pick}，不要直接跳到更高档。`
               : `${o.kind}起点是 ${o.effort}，评测拐点在更低的 ${pick}；需求明确、测试稳定时可以降到 ${pick} 省钱。`)+commText;
  }
  const sweetFmt=(task,value)=>fmt(value,task.elo?0:1);
  const sparkline=(res,task)=>{
    const w=64,h=20,lo=Math.min(...res.vs.map(x=>x.score)),hi=Math.max(...res.vs.map(x=>x.score)),n=res.vs.length;
    const px=i=>n===1?w/2:3+i*(w-6)/(n-1), py=sc=>hi===lo?h/2:h-3-(sc-lo)/(hi-lo)*(h-6);
    const d=res.vs.map((x,i)=>`${i?"L":"M"}${px(i).toFixed(1)},${py(x.score).toFixed(1)}`).join("");
    return `<svg class="ss-spark" viewBox="0 0 ${w} ${h}" aria-hidden="true"><path d="${d}"/>${res.vs.map((x,i)=>`<circle cx="${px(i).toFixed(1)}" cy="${py(x.score).toFixed(1)}" r="${x===res.pick?3.2:1.8}" class="${x===res.pick?"on":""}"/>`).join("")}</svg>`;
  };
  function renderSweetSpot(){
    const host=$("sweetMatrix"); if(!host) return;
    const tol=sweetTolerance[$("sweetTolerance")?.value]||sweetTolerance.balanced, releases=sweetReleases();
    const defaults=new Map((DATA.task_effort_guidance?.models||[]).map(m=>[m.modelId,m.officialDefault]));
    const colBest=new Map(sweetTasks.map(t=>[t.key,releases.map(r=>sweetPick(r,t,tol,releases)).filter(Boolean)]));
    const heat=(task,score)=>{const all=colBest.get(task.key).map(x=>x.pick.score),lo=Math.min(...all),hi=Math.max(...all);return hi===lo?0.5:(score-lo)/(hi-lo);};
    const head=`<tr><th scope="col">模型</th>${sweetTasks.map(t=>`<th scope="col">${esc(t.label)}<span class="task-detail">${esc(t.sub)}</span></th>`).join("")}</tr>`;
    const body=releases.map(r=>`<tr><th scope="row"><span class="swatch" style="background:${esc(r.color)}"></span>${esc(r.shortName||r.name)}<span class="task-detail">${esc(r.vendor)}${defaults.get(r.releaseSlug)?` · 默认 ${esc(defaults.get(r.releaseSlug))}`:""}</span></th>${sweetTasks.map(t=>{
      const res=sweetPick(r,t,tol,releases); if(!res) return `<td class="ss-empty">—</td>`;
      const alt=sweetCheaper(t,res.pick,releases,r.releaseSlug), sel=sweetView.model===r.releaseSlug&&sweetView.task===t.key;
      const frontier=!sweetDominated(t,res.pick,releases,r.releaseSlug);
      const refs=sweetRefs(r,t,tol), refList=[refs.official?{tag:refs.official.kind,e:refs.official.effort}:null,...refs.community.map(c=>({tag:"社区",e:c.effort}))].filter(Boolean);
      const agree=refList.length&&refList.every(x=>x.e===res.pick.v.effort);
      const refLine=refList.length?`<span class="ss-refs">${refList.map(x=>`<span class="${x.e===res.pick.v.effort?"same":""}">${esc(x.tag)} ${esc(x.e)}${x.e===res.pick.v.effort?" ✓":""}</span>`).join("")}</span>`:"";
      const flags=[agree&&refList.length>1?`<span class="ss-flag agree">共识</span>`:"",frontier?`<span class="ss-flag front">性价比前沿</span>`:"",res.topDrop?`<span class="ss-flag warn">顶档回落</span>`:"",res.single?`<span class="ss-flag info">仅测 ${esc(res.pick.v.effort)}</span>`:""].join("");
      return `<td class="ss-cell${sel?" selected":""}${frontier?" frontier":alt?" dominated":""}" style="--heat:${heat(t,res.pick.score).toFixed(2)}" tabindex="0" role="button" aria-pressed="${sel}" data-ss-model="${esc(r.releaseSlug)}" data-ss-task="${t.key}" aria-label="${esc(`${r.shortName||r.name} ${t.label} 甜蜜点 ${res.pick.v.effort}，${sweetFmt(t,res.pick.score)}，${money(res.pick.cost)}`)}"><span class="ss-top"><b class="ss-effort e-${esc(res.pick.v.effort)}">${esc(res.pick.v.effort)}</b>${sparkline(res,t)}</span><span class="ss-meta">${sweetFmt(t,res.pick.score)} · ${finite(res.pick.cost)?money(res.pick.cost):"费用未测"}</span>${refLine}${flags}</td>`;}).join("")}</tr>`).join("");
    host.innerHTML=`<table class="sweet-table"><thead>${head}</thead><tbody>${body}</tbody></table>`;
    host.querySelectorAll(".ss-cell").forEach(cell=>{
      const open=()=>{sweetView.model=cell.dataset.ssModel;sweetView.task=cell.dataset.ssTask;renderSweetSpot();renderSweetDetail();host.querySelector(`[data-ss-model="${sweetView.model}"][data-ss-task="${sweetView.task}"]`)?.focus();};
      cell.addEventListener("click",open);cell.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();open();}});
    });
    $("sweetRule").textContent=`规则（${tol.label}）：从最便宜的档位往上升，只要成本每翻一倍，分数还能提升本列全部配置分差的 ${Math.round(tol.share*100)}% 以上，就继续升档；第一次低于这个门槛就停下，停下的那一档就是甜蜜点。成本统一用 AA 综合单任务成本。`;
    renderSweetDetail();
  }
  function renderSweetDetail(){
    const box=$("sweetDetail"); if(!box) return;
    const r=sweetReleases().find(x=>x.releaseSlug===sweetView.model), t=sweetTasks.find(x=>x.key===sweetView.task);
    if(!r||!t){box.innerHTML=`<p class="muted">点矩阵中的格子，查看该模型在这项任务上每一档的分数、成本和边际收益。</p>`;return;}
    const all=sweetReleases(), tol=sweetTolerance[$("sweetTolerance")?.value]||sweetTolerance.balanced, res=sweetPick(r,t,tol,all), alt=sweetCheaper(t,res.pick,all,r.releaseSlug);
    const rows=res.vs.map((x,i)=>{const prev=res.vs[i-1];const ds=prev?x.score-prev.score:null,dc=prev&&finite(x.cost)&&finite(prev.cost)?x.cost-prev.cost:null;
      const dbl=finite(ds)&&finite(dc)&&prev.cost>0&&x.cost>prev.cost?ds/Math.log2(x.cost/prev.cost):null;
      const tag=[x===res.pick?"甜蜜点":"",x===res.peak?"最高分":"",x===res.top&&res.topDrop?"顶档回落":""].filter(Boolean).join(" · ");
      return `<tr class="${x===res.pick?"is-pick":""}"><th>${esc(x.v.effort)}</th><td>${sweetFmt(t,x.score)}</td><td class="${ds>0?"delta-positive":ds<0?"delta-negative":""}">${finite(ds)?(ds>0?"+":"")+sweetFmt(t,ds):"—"}</td><td>${money(x.cost)}</td><td>${finite(dc)?(dc>0?"+":"")+money(dc):"—"}</td><td>${finite(ds)&&finite(dc)&&dc>0?sweetFmt(t,ds/dc)+" / $":"—"}</td><td class="${finite(dbl)?(dbl>=res.threshold?"delta-positive":"delta-negative"):""}">${finite(dbl)?(dbl>0?"+":"")+sweetFmt(t,dbl):"—"}</td><td>${tag||""}</td></tr>`;}).join("");
    box.innerHTML=`<h3>${esc(r.shortName||r.name)} · ${esc(t.label)}</h3><p class="small muted">${esc(t.sub)}${t.elo?"（Elo，只用于同一基准内比较）":""}</p><div class="table-scroll"><table class="sweet-detail-table"><thead><tr><th>档位</th><th>分数</th><th>比上一档</th><th>单任务成本</th><th>多花</th><th>每多花 $1 得分</th><th>成本每翻倍得分</th><th>标记</th></tr></thead><tbody>${rows}</tbody></table></div><p class="small muted">升档门槛：成本每翻一倍至少 +${sweetFmt(t,res.threshold)}（本列分差的 ${Math.round(tol.share*100)}%）。绿色表示这一步达到门槛，红色表示没有达到。</p>${(()=>{const refs=sweetRefs(r,t,tol),advice=sweetAdvice(res.pick.v.effort,refs);
      const items=[`<li><b>评测拐点 ${esc(res.pick.v.effort)}</b>：AA 逐档数据，规则见矩阵上方。</li>`,
        refs.official?`<li><b>${esc(refs.official.kind)}${refs.official.taskSpecific?"起点":"默认"} ${esc(refs.official.effort)}</b>：${esc(refs.official.note)} ${refs.official.url?link(refs.official.url,"来源"):""}</li>`:`<li><b>官方</b>：未核验到官方默认档位。</li>`,
        ...refs.community.map(c=>`<li><b>社区 · ${esc(c.label)} ${esc(c.effort)}</b>${c.n?`（n=${c.n}）`:""}：${esc(c.note)} ${c.url?link(c.url,"来源"):""}${c.rows?`<span class="task-detail">逐档通过率：${c.rows.slice().sort((a,b)=>capabilityEfforts.indexOf(a.effort)-capabilityEfforts.indexOf(b.effort)).map(x=>`${esc(x.effort)} ${fmt(x.score,1)}% / ${money(x.cost_usd)}`).join(" · ")}</span>`:""}</li>`)];
      return `<div class="ss-refs-detail"><h4>参考依据</h4><ul>${items.join("")}</ul>${advice?`<p class="ss-advice"><b>建议做法：</b>${esc(advice)}</p>`:""}</div>`;})()}${alt?`<p class="ss-alt-note">有更省的替代：<strong>${esc(alt.release.shortName||alt.release.name)} ${esc(alt.v.effort)}</strong> 得分 ${sweetFmt(t,alt.score)}，不低于当前甜蜜点，成本 ${money(alt.cost)}（当前为 ${money(res.pick.cost)}）。</p>`:""}`;
    const pm=(DATA.model_effort_profiles?.models||[]).find(m=>m.aaRelease===r.releaseSlug);
    if(pm){
      box.insertAdjacentHTML("beforeend",`<p><button class="inline-button" data-profile-open="${esc(pm.id)}">在模型档案中看 ${esc(r.shortName||r.name)} 全部任务 →</button></p>`);
      box.querySelector("[data-profile-open]").addEventListener("click",e=>{mpView.model=e.currentTarget.dataset.profileOpen;mpView.task=t.key;showPanel("profiles");$("report-nav").scrollIntoView({block:"start"});});
    }
  }
  if($("sweetTolerance")) $("sweetTolerance").addEventListener("change",renderSweetSpot);
  if($("toggleNotes")) $("toggleNotes").addEventListener("click",event=>{
    const full=document.body.classList.toggle("notes-full");
    event.currentTarget.setAttribute("aria-pressed",String(full));
    event.currentTarget.textContent=full?"收起口径说明":"展开全部口径说明";
  });

  // ---------- Model profile (模型档案): one model, every task × native effort ----------
  // Measured picks reuse the overview knee (kneeOf / sweetThreshold), so both views always agree.
  const MP=DATA.model_effort_profiles||{models:[],evidence:[],taskAxis:[]};
  const mpEffortOrder=["none","minimal","low","medium","high","xhigh","max"];
  const mpNorm=e=>e==="non-reasoning"?"none":e;
  const mpEffortLabel=e=>e==="none"?"none（关推理）":e;
  const mpView={model:"claude-opus-5-5",task:null};
  const mpCat=id=>DATA.models.find(m=>m.id===id);
  const mpEntry=id=>MP.models.find(m=>m.id===id);
  const mpTol=()=>sweetTolerance[$("profileTolerance")?.value]||sweetTolerance.balanced;
  function mpEfforts(entry,cat){
    const listed=[...new Set((String(cat.efforts||"").replace(/（.*?）/g,"").match(/\b(none|minimal|low|medium|high|xhigh|max)\b/g)||[]))];
    const pending=(entry.effortDiscrepancy?.extraEfforts||[]).filter(e=>!listed.includes(e));
    return {listed,pending};
  }
  // Generic knee over measured points; falls back to the best score (lowest effort on ties) when costs are missing.
  function mpPick(points,threshold,elo){
    const pts=points.filter(p=>finite(p.score));
    if(!pts.length) return null;
    const best=Math.max(...pts.map(p=>p.score)), peak=pts.find(p=>p.score===best), top=pts[pts.length-1];
    return {pick:kneeOf(pts,threshold)||peak,peak,top,topDrop:pts.length>1&&top.score<best-(elo?10:0.5),single:pts.length===1,threshold};
  }
  const mpSpread=values=>{const v=values.filter(finite);return v.length?Math.max(...v)-Math.min(...v):0;};
  const mpSort=pts=>pts.sort((a,b)=>mpEffortOrder.indexOf(a.effort)-mpEffortOrder.indexOf(b.effort));
  // Every benchmark series for one model. Each series keeps its own unit, cost definition and source.
  function mpSeries(entry,cat){
    const out=[], all=sweetReleases(), rel=(DATA.aa_release_series?.releases||[]).find(r=>r.releaseSlug===entry.aaRelease);
    if(rel){
      sweetTasks.forEach(t=>{
        const points=mpSort(rel.variants.filter(v=>finite(t.get(v))).map(v=>({effort:mpNorm(v.effort),score:t.get(v),cost:v.costPerTask,time:finite(v.timePerTaskSeconds)?v.timePerTaskSeconds:null,fallback:v.fallbackLabel||null,url:v.evalSourceUrl||rel.sourceUrl})));
        if(!points.length) return;
        out.push({task:t.key,key:"aa-"+t.key,bench:t.key==="ii"?"AA 智能指数":`AA · ${t.sub}`,unit:t.elo?"Elo":"分",elo:t.elo,digits:t.elo?0:1,costLabel:"AA 单任务成本",
          url:rel.sourceUrl,points,spread:sweetThreshold(t,{share:1},all),threshold:tol=>sweetThreshold(t,tol,all)});
      });
    }
    const rowSeries=(bench,task,key,label,costLabel)=>{
      const pool=DATA.rows.filter(r=>r.benchmark===bench&&finite(r.score));
      const mine=pool.filter(r=>r.model===cat.name);
      const points=mpSort(mine.filter(r=>mpEffortOrder.includes(mpNorm(r.effort))&&r.variant!=="unverified"&&r.variant!=="ultra_harness").map(r=>({effort:mpNorm(r.effort),score:r.score,cost:r.cost_usd,time:finite(r.time_s)?r.time_s:finite(r.minutes_per_task_all_runs)?r.minutes_per_task_all_runs*60:null,fallback:r.variant==="mixed_fallback"?"含回退配置":null,url:r.source_url,n:r.n})));
      const others=mine.length-points.length;
      if(!points.length&&!others) return;
      const spread=mpSpread(pool.map(r=>r.score));
      out.push({task,key,bench:label,unit:bench==="coding"?"% 通过":"分",elo:false,digits:1,costLabel,url:mine[0]?.source_url,points,others,
        spread,threshold:tol=>tol.share*spread});
    };
    rowSeries("coding","coding","vulcan","Vulcan 编码 23 题","每次尝试费用");
    rowSeries("writing","writing","tonebench","ToneBench 英文写作","每篇费用");
    const cu=DATA.computer_use_evidence;
    if(cu){
      const sweep=cu.openaiSweep, s=sweep?.series?.find(x=>entry.cuIds.includes(x.modelId));
      if(s){
        const pool=sweep.series.flatMap(x=>x.scores);
        out.push({task:"computer_use",key:"cu-openai",bench:`${sweep.benchmark} · ${sweep.subset} · ${sweep.metric}`,unit:"%",elo:false,digits:2,costLabel:"厂商报告单任务费用",url:sweep.source,
          points:sweep.efforts.map((e,i)=>({effort:e,score:s.scores[i],cost:s.costUsdPerTask[i],url:sweep.source})),spread:mpSpread(pool),threshold:tol=>tol.share*mpSpread(pool)});
      }
      const am=cu.anthropicMax, ar=am?.rows?.find(x=>entry.cuIds.includes(x.modelId));
      if(ar) out.push({task:"computer_use",key:"cu-anthropic",bench:`${am.displayLabel} · partial reward`,unit:"%",elo:false,digits:1,costLabel:"未披露",url:am.sourceRefs?.[0]?.sourceUrl,
        points:[{effort:am.nativeEffort,score:ar.partialRewardPct,cost:null,url:am.sourceRefs?.[0]?.sourceUrl,note:`strict success ${fmt(ar.strictSuccessRatePct,1)}%`}],threshold:()=>0});
      const gr=cu.geminiReference;
      if(gr&&entry.cuIds.includes(gr.modelId)) out.push({task:"computer_use",key:"cu-gemini",bench:`${gr.benchmark} · ${gr.subset} · ${gr.statistic}`,unit:"%",elo:false,digits:1,costLabel:"未披露",url:gr.sources?.[0],
        points:[],unplaced:`最高 thinking 设置（原生档位未核验）partial reward ${fmt(gr.partialRewardPct,1)}%，不放入档位列。`,threshold:()=>0});
    }
    return out;
  }
  const mpSeriesCache=new Map();
  const mpSeriesOf=entry=>{if(!mpSeriesCache.has(entry.id))mpSeriesCache.set(entry.id,mpSeries(entry,mpCat(entry.id)));return mpSeriesCache.get(entry.id);};
  const mpReleaseDate=entry=>(DATA.aa_release_series?.releases||[]).find(r=>r.releaseSlug===entry.aaRelease)?.releaseDate||null;
  // Pitfalls, all within one benchmark series:
  //  cost      a step that at least doubles the cost but gains less than 12% of the benchmark's score spread;
  //  regress   a higher effort that scores below a cheaper, lower effort of the same model;
  //  upgrade   a newer model of the same product line scores at least as high for no more money;
  //  dominated another same-vendor model does the same.
  const MP_COST_RATIO=2, MP_COST_SHARE=sweetTolerance.balanced.share, MP_TIE_SHARE=0.03, MP_OVERTHINK_RATIO=1.5;
  function mpPitfalls(entry){
    const cat=mpCat(entry.id), mine=mpSeriesOf(entry), out=[];
    mine.forEach(s=>{
      const tol=s.elo?10:0.5;
      s.points.forEach((p,i)=>{
        const lower=s.points.slice(0,i), prev=lower[lower.length-1];
        if(lower.length){
          const ref=lower.reduce((b,x)=>x.score>b.score?x:b,lower[0]);
          if(p.score<ref.score-tol) out.push({kind:"regress",s,p,ref});
        }
        if(prev&&finite(p.cost)&&finite(prev.cost)&&prev.cost>0&&p.cost/prev.cost>=MP_COST_RATIO&&p.score-prev.score<MP_COST_SHARE*s.spread) out.push({kind:"cost",s,p,ref:prev});
        if(prev&&finite(p.time)&&finite(prev.time)&&prev.time>0&&p.time/prev.time>=MP_OVERTHINK_RATIO&&p.score-prev.score<MP_TIE_SHARE*s.spread) out.push({kind:"overthink",s,p,ref:prev});
      });
    });
    // Comprehensive same-vendor dominance, judged per effort across every series both models measured with costs.
    const others=MP.models.filter(m=>m.id!==entry.id&&mpCat(m.id)?.vendor===cat.vendor), myDate=mpReleaseDate(entry);
    const at=(series,e)=>series.points.find(x=>x.effort===e);
    mpEffortOrder.filter(e=>mine.some(s=>at(s,e))).forEach(e=>{
      const mineAt=mine.filter(s=>{const p=at(s,e);return p&&finite(p.cost);});
      let best=null;
      others.forEach(o=>{
        const theirs=mpSeriesOf(o);
        mpEffortOrder.filter(f=>theirs.some(s=>at(s,f))).forEach(f=>{
          const shared=mineAt.map(s=>({s,p:at(s,e),q:(()=>{const t=theirs.find(x=>x.key===s.key);const q=t&&at(t,f);return q&&finite(q.cost)?q:null;})()})).filter(x=>x.q);
          if(!shared.length) return;
          if(!shared.every(x=>x.q.score>=x.p.score&&x.q.cost<=x.p.cost)) return;
          if(!shared.some(x=>x.q.score>x.p.score||x.q.cost<x.p.cost)) return;
          const c={o,f,shared}, cost=shared[0].q.cost;
          if(!best||shared.length>best.shared.length||shared.length===best.shared.length&&(cost<best.shared[0].q.cost||cost===best.shared[0].q.cost&&(o.id<best.o.id||o.id===best.o.id&&mpEffortOrder.indexOf(f)<mpEffortOrder.indexOf(best.f)))) best=c;
        });
      });
      if(!best) return;
      const altDate=mpReleaseDate(best.o), upgrade=best.o.line===entry.line&&myDate&&altDate&&altDate>myDate;
      out.push({kind:upgrade?"upgrade":"dominated",config:true,effort:e,alt:best.o,f:best.f,shared:best.shared});
    });
    return out;
  }
  // Better alternatives for one effort of one model, per benchmark series:
  //  cheaper  = lowest-cost config scoring at least as high and costing strictly less;
  //  stronger = highest-scoring config costing no more and scoring strictly higher.
  const mpAltView={effort:null,scope:"vendor"};
  function mpAlternatives(entry,effort,scope){
    const vendor=mpCat(entry.id).vendor, pool=MP.models.filter(m=>scope==="all"||mpCat(m.id)?.vendor===vendor);
    const ord=e=>mpEffortOrder.indexOf(e);
    return mpSeriesOf(entry).map(s=>{
      const p=s.points.find(x=>x.effort===effort);
      if(!p||!finite(p.cost)) return null;
      const cands=[];
      pool.forEach(o=>(mpSeriesOf(o).find(x=>x.key===s.key)?.points||[]).forEach(q=>{if(finite(q.cost)&&!(o.id===entry.id&&q.effort===effort)) cands.push({o,q});}));
      const tie=(a,b)=>a.o.id<b.o.id?-1:a.o.id>b.o.id?1:ord(a.q.effort)-ord(b.q.effort);
      const cheaper=cands.filter(c=>c.q.score>=p.score&&c.q.cost<p.cost).sort((a,b)=>a.q.cost-b.q.cost||b.q.score-a.q.score||tie(a,b))[0]||null;
      const stronger=cands.filter(c=>c.q.cost<=p.cost&&c.q.score>p.score).sort((a,b)=>b.q.score-a.q.score||a.q.cost-b.q.cost||tie(a,b))[0]||null;
      // Unbounded: ignore cost, treat scores within 3% of the spread of the top as a tie, then take the fastest
      // (the cheapest when timing is missing). The current config competes too.
      const all=[...cands,{o:entry,q:p}], topScore=Math.max(...all.map(c=>c.q.score)), ties=all.filter(c=>c.q.score>=topScore-MP_TIE_SHARE*s.spread);
      const timed=ties.every(c=>finite(c.q.time)), top=all.slice().sort((a,b)=>b.q.score-a.q.score||a.q.cost-b.q.cost||tie(a,b))[0];
      const unbounded=ties.slice().sort((a,b)=>(timed?a.q.time-b.q.time:a.q.cost-b.q.cost)||b.q.score-a.q.score||tie(a,b))[0];
      return {s,p,cheaper,stronger,unbounded,top,timed};
    }).filter(Boolean);
  }
  function mpAltCell(x,c,mode,entry){
    if(!c) return '<span class="muted">无更优</span>';
    const s=x.s,u=s.unit==="%"||s.unit==="% 通过"?"%":" "+s.unit, alt=mpCat(c.o.id), self=c.o.id===entry.id;
    const delta=mode==="cheaper"?(x.p.cost>0?`省 ${Math.round((1-c.q.cost/x.p.cost)*100)}%`:""):`+${fmt(c.q.score-x.p.score,s.digits)}${u}`;
    return `<b>${esc(self?"同模型":alt.short||alt.name)} ${esc(c.q.effort)}</b>${self?'<span class="mp-tag">降档/换档</span>':""}<span class="mp-cost">${mpFmt(s,c.q.score)}${esc(u)} · ${money(c.q.cost)} · ${esc(delta)}</span>`;
  }
  // Community voices: text-only context for dimensions the benchmarks miss; never used in calculations.
  function mpVoices(modelId,task,any){
    return (DATA.community_consensus?.items||[]).filter(x=>x.modelIds.includes(modelId)&&(any||(task?x.tasks.includes(task):x.tasks.includes("all"))));
  }
  const mpVoiceList=items=>`<ul class="mp-voices">${items.map(x=>`<li><span class="evidence-badge basis-official">社区主流声音 · ${esc(x.stance)}</span>${esc(x.statement)} <b>动作：</b>${esc(x.action)}<span class="task-detail">${esc(x.agreement)} · ${x.sources.map(s=>link(s.url,s.label)).join(" · ")} · 检索摘要，原页尚未逐条核对 · ${esc(x.checkedAt)}</span></li>`).join("")}</ul>`;
  function mpUnboundedCell(x,entry){
    const c=x.unbounded, s=x.s, u=s.unit==="%"||s.unit==="% 通过"?"%":" "+s.unit;
    const isSelf=c.o.id===entry.id&&c.q===x.p, alt=mpCat(c.o.id), name=c.o.id===entry.id?"同模型":alt.short||alt.name;
    const speed=x.timed?`${mpSec(c.q.time)}`:"无耗时数据，按费用";
    const head=isSelf?`<b>当前就是</b>`:`<b>${esc(name)} ${esc(c.q.effort)}</b>`;
    const diff=isSelf?"":` · ${c.q.score>=x.p.score?"+":""}${fmt(c.q.score-x.p.score,s.digits)}${esc(u)}`;
    const topNote=x.top!==c&&x.top.q.score>c.q.score?`<span class="task-detail">最高分 ${esc((x.top.o.id===entry.id?"同模型":mpCat(x.top.o.id).short||mpCat(x.top.o.id).name))} ${esc(x.top.q.effort)} ${mpFmt(s,x.top.q.score)}${esc(u)}，只高 ${fmt(x.top.q.score-c.q.score,s.digits)}${x.timed&&finite(x.top.q.time)&&c.q.time>0?`，慢 ${fmt(x.top.q.time/c.q.time,1)} 倍`:""}</span>`:"";
    return `${head}<span class="mp-cost">${mpFmt(s,c.q.score)}${esc(u)} · ${money(c.q.cost)} · ${esc(speed)}${diff}</span>${topNote}`;
  }
  // When not to default to the top effort even without a budget. Measured signals come from this page's data.
  function renderProfileScenarios(entry,pits){
    const box=$("profileScenarioList"); if(!box) return;
    const cc=DATA.community_consensus, rel=(DATA.aa_release_series?.releases||[]).find(r=>r.releaseSlug===entry.aaRelease);
    const ttfa=(rel?.variants||[]).filter(v=>finite(v.ttfaSeconds)).sort((x,y)=>x.effortOrder-y.effortOrder);
    const signal=sc=>{
      if(sc.measure==="overthink"||sc.measure==="regress"){
        const hit=pits.filter(x=>x.kind===sc.measure);
        return hit.length?`本模型实测：${hit.length} 处，例如 ${hit.slice(0,3).map(x=>`${mpSeriesName(x.s)} ${x.ref.effort}→${x.p.effort}`).join("；")}。`:"本模型在本页数据中未发现。";
      }
      if(sc.measure==="ttfa"){
        if(ttfa.length<2) return "本模型缺少逐档首字等待数据。";
        const lo=ttfa[0],hi=ttfa[ttfa.length-1];
        return `本模型实测首字等待：${mpNorm(lo.effort)} ${fmt(lo.ttfaSeconds,1)} 秒 → ${mpNorm(hi.effort)} ${fmt(hi.ttfaSeconds,1)} 秒（${ttfa.map(v=>`${mpNorm(v.effort)} ${fmt(v.ttfaSeconds,1)}s`).join(" · ")}）。`;
      }
      return "";
    };
    box.innerHTML=(cc?.maxEffortScenarios||[]).map(sc=>{const sig=signal(sc);
      return `<li data-scenario="${esc(sc.id)}"><b>${esc(sc.title)}</b>：${esc(sc.why)}<span class="task-detail">怎么识别：${esc(sc.signal)}</span><span class="mp-scn-action"><b>怎么做：</b>${esc(sc.action)}</span>${sig?`<span class="mp-scn-signal${sig.startsWith("本模型实测")?" hit":""}">${esc(sig)}</span>`:""}<span class="task-detail">${sc.sources.map(x=>`${esc(x.type)} · ${link(x.url,x.label)}`).join(" ； ")}</span></li>`;}).join("");
  }
  function renderProfileAlternatives(a){
    const box=$("profileAltTable"); if(!box) return;
    const efforts=mpEffortOrder.filter(e=>a.series.some(s=>s.points.some(p=>p.effort===e&&finite(p.cost))));
    const sel=$("profileAltEffort");
    if(!efforts.length){sel.innerHTML="";box.innerHTML='<p class="small muted">这款模型没有带费用的实测档位，无法比较替代。</p>';$("profileAltSummary").textContent="";return;}
    // Default to the official default effort (what most calls use), then the overall sweet spot.
    if(!efforts.includes(mpAltView.effort)){const ii=a.series.find(s=>s.key==="aa-ii"),sw=ii?.res.balanced?.pick.effort;mpAltView.effort=efforts.includes(a.cat.default_effort)?a.cat.default_effort:sw&&efforts.includes(sw)?sw:efforts[0];}
    sel.innerHTML=efforts.map(e=>`<option value="${esc(e)}">${esc(mpEffortLabel(e))}</option>`).join("");sel.value=mpAltView.effort;
    $("profileAltScope").value=mpAltView.scope;
    const rows=mpAlternatives(a.entry,mpAltView.effort,mpAltView.scope);
    const nC=rows.filter(r=>r.cheaper).length,nS=rows.filter(r=>r.stronger).length,nT=rows.filter(r=>!(r.unbounded.o.id===a.entry.id&&r.unbounded.q===r.p)).length;
    $("profileAltSummary").textContent=`${a.cat.name} · ${mpAltView.effort}：在 ${rows.length} 项有费用的评测里，${nC} 项能在分数不降的情况下更省钱，${nS} 项能在不加预算的情况下拿到更高分，${nT} 项不看预算时推荐换别的配置（范围：${mpAltView.scope==="all"?"四家全部活跃型号":"同厂商活跃型号"}，含本模型其它档位）。`;
    box.innerHTML=`<table class="mp-alt-table"><thead><tr><th scope="col">任务 · 评测</th><th scope="col">当前 ${esc(mpAltView.effort)}</th><th scope="col">同分最省<span class="task-detail">分数不低于当前，费用最低</span></th><th scope="col">同预算最强<span class="task-detail">费用不超过当前，分数最高</span></th><th scope="col">不限预算推荐<span class="task-detail">与最高分打平的配置里最快的</span></th></tr></thead><tbody>${rows.map(x=>{const u=x.s.unit==="%"||x.s.unit==="% 通过"?"%":" "+x.s.unit;
      return `<tr data-alt-series="${esc(x.s.key)}" data-cheaper="${x.cheaper?esc(x.cheaper.o.id+"|"+x.cheaper.q.effort):""}" data-stronger="${x.stronger?esc(x.stronger.o.id+"|"+x.stronger.q.effort):""}" data-unbounded="${esc(x.unbounded.o.id+"|"+x.unbounded.q.effort)}"><th scope="row">${esc(mpSeriesName(x.s))}</th><td>${mpFmt(x.s,x.p.score)}${esc(u)}<span class="mp-cost">${money(x.p.cost)}</span></td><td>${mpAltCell(x,x.cheaper,"cheaper",a.entry)}</td><td>${mpAltCell(x,x.stronger,"stronger",a.entry)}</td><td>${mpUnboundedCell(x,a.entry)}</td></tr>`;}).join("")}</tbody></table>`;
    const cc=DATA.community_consensus, voices=mpVoices(a.entry.id,null,true);
    $("profileAltCoverage").innerHTML=`<p class="small"><b>这张表看不到的：</b>${(cc?.uncoveredDimensions||[]).map(esc).join("、")}。这些维度没有带费用的公开评测，所以“更优替代”不会因为它们推荐更贵的型号。${voices.length?"下面是社区对这款模型的主流看法，只作参考，不参与计算：":"这款模型暂未整理社区主流声音。"}</p>${voices.length?mpVoiceList(voices):""}`;
  }
  function mpAnalyse(entry){
    const cat=mpCat(entry.id), efforts=mpEfforts(entry,cat), series=mpSeriesOf(entry);
    series.forEach(s=>{s.res={};Object.entries(sweetTolerance).forEach(([k,tol])=>{s.res[k]=mpPick(s.points,s.threshold(tol),s.elo);});});
    const measured=new Set(series.flatMap(s=>s.points.map(p=>p.effort)));
    const cols=mpEffortOrder.filter(e=>efforts.listed.includes(e)||efforts.pending.includes(e)||measured.has(e));
    return {entry,cat,efforts,series,cols};
  }
  const mpEvidence=(modelId,task)=>(MP.evidence||[]).filter(x=>x.modelIds.includes(modelId)&&(task?x.tasks.includes(task):x.tasks.includes("all")));
  const mpPresetKey=()=>$("profileTolerance")?.value||"balanced";
  // Starting effort: task-specific guide record > task-scoped evidence > model-wide evidence > official default.
  function mpStart(a,task){
    const axis=(MP.taskAxis||[]).find(t=>t.id===task), g=DATA.task_effort_guidance;
    const recs=(g?.recommendations||[]).filter(r=>r.modelId===a.entry.guidanceId&&(axis?.guideTasks||[]).includes(r.taskType));
    if(recs.length){const r=recs.find(x=>x.evidenceType!=="社区实测")||recs[0];
      return {effort:r.nativeEffort,kind:r.evidenceType,note:recs.map(x=>`${guideTaskLabel[x.taskType]||x.taskType} ${x.nativeEffort}（${x.evidenceType}）`).join(" · "),url:r.support?.[0]?.sourceUrl||r.sourceUrl};}
    const scoped=mpEvidence(a.entry.id,task).find(x=>x.efforts?.start);
    if(scoped) return {effort:scoped.efforts.start,kind:scoped.kind,note:scoped.statement,url:scoped.url};
    const wide=mpEvidence(a.entry.id,null).find(x=>x.efforts?.start);
    if(wide) return {effort:wide.efforts.start,kind:wide.kind,note:"适用于全部任务的证据（见本页底部）。",url:null};
    const d=a.cat.default_effort;
    if(d&&mpEffortOrder.includes(d)) return {effort:d,kind:"官方默认",note:`官方默认 ${d}，不分任务。`,url:a.cat.source};
    return null;
  }
  function mpCardAdvice(start,pick,thrifty,perf,ev,single){
    const idx=e=>mpEffortOrder.indexOf(e), parts=[];
    if(start&&pick){
      if(start.effort===pick) parts.push(`起步档与甜蜜点都是 ${pick}，直接用它。`);
      else if(idx(pick)>idx(start.effort)) parts.push(`从 ${start.effort} 起步；交付不达标时先升到甜蜜点 ${pick}，不要直接跳到最高档。`);
      else parts.push(`起步档是 ${start.effort}，甜蜜点在更低的 ${pick}；需求明确、测试稳定时可以降到 ${pick} 省钱。`);
    } else if(start) parts.push(`${single?`本报告只有 ${single} 单点，看不出升档收益`:"本报告没有这项任务的逐档实测"}；先按 ${start.effort} 起步，用自己的样本对比相邻一档。`);
    else if(pick) parts.push(`甜蜜点是 ${pick}；没有核验到官方起步档。`);
    if(thrifty&&pick&&thrifty!==pick) parts.push(`预算紧时可退到 ${thrifty}（省钱门槛下的甜蜜点）。`);
    if(perf&&pick&&perf!==pick) parts.push(`追求上限时最多到 ${perf}（性能优先门槛下的甜蜜点）。`);
    const avoid=ev.find(x=>x.efforts?.avoid);
    if(avoid) parts.push(`有证据提示慎用 ${avoid.efforts.avoid}。`);
    return parts.join("");
  }
  function mpFmt(s,v){return finite(v)?fmt(v,s.digits):"—";}
  const mpSec=v=>!finite(v)?"耗时未测":v>=90?`${fmt(v/60,1)} 分钟`:`${fmt(v,0)} 秒`;
  // Every model shows the same benchmark rows per task (missing ones read "未测"), so a number in one
  // row is never compared with a different benchmark in the same position for another model.
  function mpRowsFor(task,series){
    const aa=sweetTasks.find(t=>t.key===task);
    const fixed=[...(aa?[{key:"aa-"+task,bench:task==="ii"?"AA 智能指数":`AA · ${aa.sub}`,unit:aa.elo?"Elo":"分"}]:[]),
      ...(task==="coding"?[{key:"vulcan",bench:"Vulcan 编码 23 题",unit:"% 通过"}]:[]),
      ...(task==="writing"?[{key:"tonebench",bench:"ToneBench 英文写作",unit:"分"}]:[])];
    const rows=fixed.map(f=>series.find(s=>s.key===f.key)||{...f,placeholder:true,points:[]});
    series.filter(s=>!fixed.some(f=>f.key===s.key)).forEach(s=>rows.push(s));
    if(task==="computer_use"&&!rows.length) rows.push({key:"cu",bench:"OSWorld（各厂商协议不同）",unit:"%",placeholder:true,points:[]});
    return rows;
  }
  const mpUnitText=s=>s.unit==="% 通过"?"通过率 %":s.unit==="%"?"%":s.unit;
  const mpPitMeta={cost:{label:"费用刺客",short:"刺客",rule:"相邻两档成本至少翻倍，分数提升却不到该评测分差的 12%（均衡门槛）。"},
    overthink:{label:"过度思考",short:"慢",rule:"相邻两档耗时涨到 1.5 倍以上，分数提升却不到该评测分差的 3%（视为打平）。不看预算时也不值得等。"},
    regress:{label:"档位倒退",short:"倒退",rule:"更高档的分数比同模型某个更低档还低（超过 0.5 分 / 10 Elo）。点估计，未做显著性检验。"},
    upgrade:{label:"新一代更省",short:"换新更省",rule:"同一产品线、发布更晚的型号的某一档，在双方都测过的所有评测上分数都不低、费用都不高（至少一项更好）。常见情形：升级型号、降低档位反而更便宜。"},
    dominated:{label:"被同家其它型号全面超越",short:"同家更省",rule:"同一厂商其它活跃型号的某一档，在双方都测过的所有评测上分数都不低、费用都不高（至少一项更好）。"}};
  const mpTaskLabel=id=>((MP.taskAxis||[]).find(t=>t.id===id)||{}).label||id;
  const mpSeriesName=s=>`${mpTaskLabel(s.task)} · ${s.bench}`;
  function mpPitText(x){
    const s=x.s,p=x.p,u=s.unit==="%"||s.unit==="% 通过"?"%":" "+s.unit;
    if(x.kind==="cost") return `<b>${esc(mpSeriesName(s))}</b> ${esc(x.ref.effort)}→${esc(p.effort)}：成本 ${money(x.ref.cost)}→${money(p.cost)}（×${fmt(p.cost/x.ref.cost,1)}），分数只多 ${fmt(p.score-x.ref.score,s.digits)}${esc(u)}，不到该评测分差的 12%（${fmt(MP_COST_SHARE*s.spread,s.digits)}${esc(u)}）。`;
    if(x.kind==="overthink") return `<b>${esc(mpSeriesName(s))}</b> ${esc(x.ref.effort)}→${esc(p.effort)}：耗时 ${mpSec(x.ref.time)}→${mpSec(p.time)}（×${fmt(p.time/x.ref.time,1)}），分数只多 ${fmt(p.score-x.ref.score,s.digits)}${esc(u)}，在打平范围（${fmt(MP_TIE_SHARE*s.spread,s.digits)}${esc(u)}）内。`;
    if(x.kind==="regress") return `<b>${esc(mpSeriesName(s))}</b> ${esc(p.effort)} 得 ${mpFmt(s,p.score)}${esc(u)}，低于更低档 ${esc(x.ref.effort)} 的 ${mpFmt(s,x.ref.score)}${esc(u)}${finite(p.cost)&&finite(x.ref.cost)&&p.cost>x.ref.cost?`，却多花 ${money(p.cost-x.ref.cost)}`:""}。${p.fallback||x.ref.fallback?"含回退配置；":""}点估计，未做显著性检验。`;
    return "";
  }
  function mpConfigText(x){
    const alt=mpCat(x.alt.id), ex=x.shared[0], s=ex.s, u=s.unit==="%"||s.unit==="% 通过"?"%":" "+s.unit, save=ex.p.cost>0?Math.round((1-ex.q.cost/ex.p.cost)*100):0;
    return `<b>${esc(x.effort)}</b> → 换 <b>${esc(alt.name)} ${esc(x.f)}</b>：在 ${x.shared.length} 项共同评测上分数都不低、费用都不高${x.shared.length===1?"（仅 1 项共同评测，证据较弱）":""}。例：${esc(mpSeriesName(s))} ${mpFmt(s,ex.p.score)}→${mpFmt(s,ex.q.score)}${esc(u)}，${money(ex.p.cost)}→${money(ex.q.cost)}${save>0?`（省 ${save}%）`:""}。<span class="task-detail">共同评测：${x.shared.map(y=>esc(mpSeriesName(y.s))).join("、")}</span>`;
  }
  const mpCardPit=x=>`${x.p.effort} ${mpPitMeta[x.kind].label}`;
  // Worked example of the sweet-spot rule on one of this model's series.
  function mpExplain(a,tol){
    const s=a.series.find(x=>x.key==="aa-ii"&&x.points.length>1)||a.series.find(x=>x.points.filter(p=>finite(p.cost)).length>1);
    const general=`<p><b>甜蜜点是什么？</b>和“选档速查”里的甜蜜点是同一个东西，也就是<strong>边际收益拐点</strong>：从最便宜的已测档往上，每升一档看“成本每翻一倍，分数多涨多少”；只要不低于门槛就继续升，第一次低于门槛就停，停下的那一档就是甜蜜点。它回答“再多花钱还值不值”，不是“哪一档分数最高”。</p>
      <p><b>省钱 / 均衡 / 性能优先怎么定？</b>门槛 = 该评测里所有模型、所有已测档位的最高分减最低分（分差）× 比例：<strong>省钱 20%、均衡 12%、性能优先 6%</strong>。比例越小，越愿意为小幅提升多花钱，甜蜜点就越往高档走。比例是个人偏好预设，不是统计结论；成本只比较同一评测的相对费用。</p>`;
    if(!s) return general+`<p class="small muted">这款模型没有带费用的逐档曲线，无法演示计算过程。</p>`;
    const hull=upperHull(s.points), thr=s.threshold(tol), u=s.unit==="%"||s.unit==="% 通过"?"%":" "+s.unit;
    const skipped=s.points.filter(p=>finite(p.cost)&&!hull.some(h=>h.x===p)).map(p=>p.effort);
    let stopped=false;
    const steps=hull.slice(1).map((b,i)=>{const a0=hull[i],gain=b.x.score-a0.x.score,per=gain/(b.lx-a0.lx),ok=!stopped&&per>=thr;
      const verdict=stopped?'<span class="muted">（已停，不再比较）</span>':ok?'<span class="delta-positive">≥ 门槛，继续升</span>':'<span class="delta-negative">＜ 门槛，停在 '+esc(a0.x.effort)+'</span>';
      if(!ok) stopped=true;
      return `<li>${esc(a0.x.effort)} → ${esc(b.x.effort)}：成本 ×${fmt(b.x.cost/a0.x.cost,2)}，分数 ${gain>=0?"+":""}${fmt(gain,s.digits)}${esc(u)}，每翻一倍 ${per>=0?"+":""}${fmt(per,2)}${esc(u)} ${verdict}</li>`;}).join("");
    const pick=s.res[mpPresetKey()]?.pick.effort;
    return general+`<p><b>以 ${esc(a.cat.name)} 的${esc(mpSeriesName(s))}为例：</b>该评测分差 ${fmt(s.spread,2)}${esc(u)}，成本每翻一倍至少要涨 省钱 ${fmt(s.threshold(sweetTolerance.thrifty),2)} / 均衡 ${fmt(s.threshold(sweetTolerance.balanced),2)} / 性能优先 ${fmt(s.threshold(sweetTolerance.performance),2)}${esc(u)}。当前（${esc(tol.label)}）：</p><ol class="mp-steps">${steps}</ol>
      <p class="small">→ 甜蜜点 <b class="ss-effort e-${esc(pick)}">${esc(pick)}</b>。${skipped.length?`${skipped.map(esc).join("、")} 比某个更便宜的档还差或不划算，不在“上凸包”上，先被跳过。`:""}每行只在同一评测内比较；不同评测的分数、单位与费用口径不混算。</p>`;
  }
  function renderModelProfile(){
    const host=$("profileGrid"); if(!host||!MP.models.length) return;
    const entry=mpEntry(mpView.model)||MP.models[0]; mpView.model=entry.id;
    if($("profileModel").value!==entry.id) $("profileModel").value=entry.id;
    document.querySelectorAll("[data-mp-quick]").forEach(b=>{const on=b.dataset.mpQuick===entry.id;b.classList.toggle("is-active",on);b.setAttribute("aria-pressed",String(on));});
    const a=mpAnalyse(entry), cat=a.cat, key=mpPresetKey(), tol=mpTol(), tier=(MP.tiers||[]).find(t=>t.id===entry.tier);
    const pits=mpPitfalls(entry), showPits=$("profilePitfalls")?.checked!==false;
    const pitsAt=(s,p)=>pits.filter(x=>!x.config&&x.s.key===s.key&&x.p===p);
    const configPit=e=>pits.find(x=>x.config&&x.effort===e);
    const multi=a.series.filter(s=>s.points.length>1).length, single=a.series.filter(s=>s.points.length===1).length;
    const tasksCovered=new Set(a.series.filter(s=>s.points.length).map(s=>s.task));
    const fallback=a.series.some(s=>s.points.some(p=>p.fallback));
    const price=finite(cat.input)?`$${fmt(cat.input)} / $${fmt(cat.output)} 每百万 token（输入 / 输出）`:"未提供";
    $("profileHeader").innerHTML=`<div class="mp-head"><div><span class="eyebrow">${esc(cat.vendor)} · ${esc(tier?.label||"")}</span><h3>${link(cat.source,cat.name)}</h3><p class="small muted">${esc(cat.role||"")}${cat.lifecycle==="Deprecated"?" · <strong>已弃用</strong>":""}</p></div>
      <dl class="mp-facts"><div><dt>原生档位</dt><dd>${a.efforts.listed.length?a.efforts.listed.map(e=>`<span class="mp-chip e-${esc(e)}">${esc(e)}</span>`).join(""):esc(cat.efforts)}${a.efforts.pending.map(e=>`<span class="mp-chip pending" title="待核验">${esc(e)}?</span>`).join("")}</dd></div>
      <div><dt>官方默认</dt><dd>${esc(cat.default_effort||"未提供")}</dd></div><div><dt>Standard 单价</dt><dd>${price}</dd></div><div><dt>上下文</dt><dd>${finite(cat.context)?fmt(cat.context,0)+" tokens":"未提供"}</dd></div>
      <div><dt>证据覆盖</dt><dd>${tasksCovered.size} / ${(MP.taskAxis||[]).length} 类任务有实测 · ${multi} 条逐档曲线 · ${single} 个单点</dd></div></dl></div>
      ${entry.effortDiscrepancy?`<p class="mp-note warn">档位待核验：${esc(entry.effortDiscrepancy.note)} ${entry.effortDiscrepancy.sources.map((u,i)=>link(u,"来源"+(i+1))).join(" · ")}</p>`:""}
      ${fallback?`<p class="mp-note">AA 逐档记录标有 Default Fallback 或回退配置，回退比例未披露；分差是点估计。</p>`:""}
      ${!multi?`<p class="mp-note warn">这款模型没有任何一项逐档曲线，下表只能显示单点或空白；选档主要依赖官方默认与经验证据，不补造曲线。</p>`:""}
      ${mpVoices(entry.id,null).length?`<div class="mp-voice-box"><h4>社区主流声音</h4>${mpVoiceList(mpVoices(entry.id,null))}</div>`:""}
      <div class="mp-links">${entry.aaRelease&&sweetReleases().some(r=>r.releaseSlug===entry.aaRelease)?`<button class="inline-button" data-mp-jump="overview">在选档速查矩阵中定位 →</button>`:""}${entry.aaRelease&&$("reasoningRelease")&&[...$("reasoningRelease").options].some(o=>o.value===entry.aaRelease)?`<button class="inline-button" data-mp-jump="reasoning">看同模型档位曲线 →</button>`:""}</div>`;
    $("profileHeader").querySelectorAll("[data-mp-jump]").forEach(b=>b.addEventListener("click",()=>{
      if(b.dataset.mpJump==="overview"){sweetView.model=entry.aaRelease;sweetView.task="ii";showPanel("overview");renderSweetSpot();$("sweetMatrix")?.scrollIntoView({block:"start"});}
      else {$("reasoningRelease").value=entry.aaRelease;$("reasoningRelease").dispatchEvent(new Event("change"));showPanel("reasoning");$("reasoningCharts")?.scrollIntoView({block:"start"});}
    }));
    // Grid: task rows × effort columns.
    const head=`<tr><th scope="col">任务 · 评测</th>${a.cols.map(e=>`<th scope="col" class="mp-col"><b class="ss-effort e-${esc(e)}">${esc(mpEffortLabel(e))}</b>${e===cat.default_effort?'<span class="mp-tag def">默认</span>':""}${a.efforts.pending.includes(e)?'<span class="mp-tag pend">待核验</span>':""}${!a.efforts.listed.includes(e)&&!a.efforts.pending.includes(e)?'<span class="mp-tag">目录未列</span>':""}${(()=>{const c=configPit(e);return c?`<span class="mp-pit k-${c.kind}" data-mp-config-pit="${c.kind}" title="${esc(`${mpPitMeta[c.kind].label}：可换 ${mpCat(c.alt.id).name} ${c.f}`)}"${showPits?"":" hidden"}>${esc(mpPitMeta[c.kind].short)}</span>`:"";})()}</th>`).join("")}</tr>`;
    const body=(MP.taskAxis||[]).map(t=>{
      const ss=mpRowsFor(t.id,a.series.filter(s=>s.task===t.id)), start=mpStart(a,t.id);
      const label=(s,i)=>`<th scope="row"${i===0?"":' class="mp-sub"'}>${i===0?`<span class="mp-task">${esc(t.label)}</span>`:""}<span class="mp-bench">${esc(s?s.bench:t.sub)}${s?`（${esc(mpUnitText(s))}）`:""}</span>${s?.others?`<span class="task-detail">另有 ${s.others} 个未注明/编排配置</span>`:""}</th>`;
      if(!ss.length) return `<tr class="mp-row empty${mpView.task===t.id?" selected":""}" data-mp-task="${t.id}">${label(null,0)}${a.cols.map(e=>`<td class="mp-cell ${start?.effort===e?"is-start":""}">${start?.effort===e?'<span class="mp-mark start" title="起步档">起步</span>':'<span class="muted">未测</span>'}</td>`).join("")}</tr>`;
      return ss.map((s,i)=>{
        if(s.placeholder) return `<tr class="mp-row empty${mpView.task===t.id?" selected":""}" data-mp-task="${t.id}">${label(s,i)}${a.cols.map(e=>{const isStart=i===0&&start?.effort===e;return `<td class="mp-cell${isStart?" is-start":""}">${isStart?'<span class="mp-mark start" title="起步档">起步</span>':""}<span class="muted">未测</span></td>`;}).join("")}</tr>`;
        const r=s.res[key], lo=Math.min(...s.points.map(p=>p.score)), hi=Math.max(...s.points.map(p=>p.score));
        const cells=a.cols.map(e=>{
          const p=s.points.find(x=>x.effort===e), idx=s.points.indexOf(p), prev=idx>0?s.points[idx-1]:null;
          const isStart=i===0&&start?.effort===e;
          if(!p) return `<td class="mp-cell ${a.efforts.listed.includes(e)||a.efforts.pending.includes(e)?"":"unsupported"}${isStart?" is-start":""}">${isStart?'<span class="mp-mark start" title="起步档">起步</span>':""}<span class="muted">${a.efforts.listed.includes(e)||a.efforts.pending.includes(e)?"未测":"—"}</span></td>`;
          const dbl=prev&&finite(p.cost)&&finite(prev.cost)&&prev.cost>0&&p.cost>prev.cost?(p.score-prev.score)/Math.log2(p.cost/prev.cost):null;
          const heat=hi===lo?0.5:(p.score-lo)/(hi-lo);
          const here=pitsAt(s,p), kinds=[...new Set(here.map(x=>x.kind))];
          const pitTags=showPits?kinds.map(k=>`<span class="mp-pit k-${k}" title="${esc(mpPitMeta[k].rule)}">${esc(mpPitMeta[k].short)}</span>`).join(""):"";
          const marks=[r&&r.pick===p?'<span class="mp-mark pick" title="当前门槛下的甜蜜点">甜蜜点</span>':"",r&&r.peak===p&&s.points.length>1&&r.pick!==p?'<span class="mp-mark peak" title="实测最高分">最高</span>':"",isStart?'<span class="mp-mark start" title="起步档">起步</span>':""].join("");
          return `<td class="mp-cell has${r&&r.pick===p?" is-pick":""}${isStart?" is-start":""}" data-mp-effort="${esc(e)}" data-mp-pit="${kinds.join(" ")}" style="--heat:${heat.toFixed(2)}" aria-label="${esc(`${t.label} ${s.bench} ${e}：${mpFmt(s,p.score)} ${s.unit}，${finite(p.cost)?money(p.cost):"费用未测"}`)}"><span class="mp-score">${mpFmt(s,p.score)}</span><span class="mp-cost">${finite(p.cost)?money(p.cost):"费用未测"}${finite(p.time)?` · ${mpSec(p.time)}`:""}</span>${finite(dbl)?`<span class="mp-dbl ${dbl>=r.threshold?"delta-positive":"delta-negative"}" title="成本每翻一倍的得分变化">${dbl>0?"+":""}${fmt(dbl,s.digits)}/×2</span>`:""}${p.note?`<span class="task-detail">${esc(p.note)}</span>`:""}${marks}${pitTags}</td>`;
        }).join("");
        return `<tr class="mp-row${mpView.task===t.id?" selected":""}" data-mp-task="${t.id}" data-mp-series="${esc(s.key)}" data-mp-pick="${esc(r?.pick.effort||"")}">${label(s,i)}${cells}</tr>`;
      }).join("");
    }).join("");
    host.innerHTML=`<table class="mp-table"><caption class="sr-only">${esc(cat.name)} 各任务在各原生档位的实测分数与成本</caption><thead>${head}</thead><tbody>${body}</tbody></table>`;
    host.querySelectorAll("tr[data-mp-task]").forEach(tr=>tr.addEventListener("click",ev=>{
      const cell=ev.target.closest("td[data-mp-effort]");
      mpView.task=tr.dataset.mpTask;
      if(cell){mpAltView.effort=cell.dataset.mpEffort;renderModelProfile();$("profileAltCard")?.scrollIntoView({block:"nearest"});return;}
      renderModelProfile();$("profileCard-"+mpView.task)?.scrollIntoView({block:"nearest"});}));
    $("profileRule").innerHTML=mpExplain(a,tol);
    renderProfileScenarios(entry,pits);
    renderProfileAlternatives(a);
    // Pitfall guide.
    $("profilePitfallsCard").hidden=!showPits;
    const avoidEv=(MP.evidence||[]).filter(x=>x.modelIds.includes(entry.id)&&x.efforts?.avoid);
    $("profilePitfallList").innerHTML=["cost","overthink","regress","upgrade","dominated"].map(k=>{
      const items=pits.filter(x=>x.kind===k).map(x=>x.config?`<li data-mp-pit-kind="${k}" data-key="config" data-effort="${esc(x.effort)}" data-alt="${esc(x.alt.id)}" data-alt-effort="${esc(x.f)}">${mpConfigText(x)}</li>`:`<li data-mp-pit-kind="${k}" data-key="${esc(x.s.key)}" data-effort="${esc(x.p.effort)}">${mpPitText(x)}</li>`);
      if(k==="cost") avoidEv.forEach(x=>items.push(`<li data-mp-pit-kind="evidence"><span class="evidence-badge">证据 · ${esc(x.kind)}</span>慎用 <b>${esc(x.efforts.avoid)}</b>：${esc(x.statement)} ${link(x.url,"来源")}<span class="task-detail">检索摘要，原页未直接打开</span></li>`));
      const head=`<h4>${esc(mpPitMeta[k].label)} <span class="mp-count">${items.length}</span></h4><p class="small muted">${esc(mpPitMeta[k].rule)}</p>`;
      if(!items.length) return `<section class="mp-pit-group" data-group="${k}">${head}<p class="small muted">本模型未发现。</p></section>`;
      const first=items.slice(0,6).join(""), rest=items.slice(6);
      return `<section class="mp-pit-group" data-group="${k}">${head}<ul>${first}</ul>${rest.length?`<details><summary>再看 ${rest.length} 条</summary><ul>${rest.join("")}</ul></details>`:""}</section>`;
    }).join("");
    // Task cards.
    $("profileCards").innerHTML=(MP.taskAxis||[]).map(t=>{
      const ss=a.series.filter(s=>s.task===t.id), main=ss.find(s=>s.points.length>1)||ss.find(s=>s.points.length)||null;
      const r=main?.res[key], start=mpStart(a,t.id), ev=mpEvidence(entry.id,t.id);
      const pick=r&&!r.single?r.pick.effort:null, thrifty=main?.res.thrifty&&!main.res.thrifty.single?main.res.thrifty.pick.effort:null, perf=main?.res.performance&&!main.res.performance.single?main.res.performance.pick.effort:null;
      const ceil=ev.find(x=>x.efforts?.ceiling)?.efforts.ceiling;
      const rows=[
        `<div><dt>起步档</dt><dd>${start?`<b class="ss-effort e-${esc(start.effort)}">${esc(start.effort)}</b><span class="mp-kind">${esc(start.kind)}</span>`:'<span class="muted">未核验</span>'}</dd></div>`,
        `<div><dt>甜蜜点</dt><dd>${pick?`<b class="ss-effort e-${esc(pick)}">${esc(pick)}</b><span class="mp-kind">${esc(main.bench)}</span>`:r?.single?`<span class="muted">仅测 ${esc(r.pick.effort)} 单点</span>`:'<span class="muted">无逐档实测</span>'}</dd></div>`,
        `<div><dt>降档候选</dt><dd>${thrifty&&thrifty!==pick?`<b class="ss-effort e-${esc(thrifty)}">${esc(thrifty)}</b><span class="mp-kind">省钱门槛</span>`:'<span class="muted">—</span>'}</dd></div>`,
        `<div><dt>升档上限</dt><dd>${perf&&perf!==pick?`<b class="ss-effort e-${esc(perf)}">${esc(perf)}</b><span class="mp-kind">性能优先门槛</span>`:ceil?`<b class="ss-effort e-${esc(ceil)}">${esc(ceil)}</b><span class="mp-kind">经验证据</span>`:'<span class="muted">—</span>'}</dd></div>`];
      const cardPits=showPits?pits.filter(x=>!x.config&&x.s.task===t.id):[];
      const flags=[r?.topDrop?'<span class="ss-flag warn">顶档回落</span>':"",ss.some(s=>s.points.some(p=>p.fallback))?'<span class="ss-flag info">含回退</span>':""].join("");
      const others=ss.filter(s=>s!==main&&(s.points.length||s.unplaced)).map(s=>{const rr=s.res[key];return `<li>${esc(s.bench)}：${s.unplaced?esc(s.unplaced):rr?.single?`仅 ${esc(rr.pick.effort)} 单点 ${mpFmt(s,rr.pick.score)}${s.unit}`:`甜蜜点 <b>${esc(rr.pick.effort)}</b>（${mpFmt(s,rr.pick.score)}${s.unit}，${finite(rr.pick.cost)?money(rr.pick.cost):"费用未测"}）`} ${s.url?link(s.url,"来源"):""}</li>`;}).join("");
      return `<article class="mp-card${mpView.task===t.id?" selected":""}" id="profileCard-${t.id}"><header><h4>${esc(t.label)}</h4><span class="small muted">${esc(t.sub)}</span>${flags}</header><dl class="mp-ladder">${rows.join("")}</dl>
        <p class="mp-advice">${esc(mpCardAdvice(start,pick,thrifty,perf,ev,r?.single?r.pick.effort:null))}</p>
        ${others?`<ul class="mp-others">${others}</ul>`:""}
        ${mpVoices(entry.id,t.id).filter(x=>!x.tasks.includes("all")).length?`<div class="mp-card-voice">${mpVoiceList(mpVoices(entry.id,t.id).filter(x=>!x.tasks.includes("all")))}</div>`:""}
        ${cardPits.length?`<p class="mp-pits"><b>避坑：</b>${[...new Set(cardPits.map(mpCardPit))].map(esc).join(" · ")}</p>`:""}
        ${ev.length?`<details class="mp-ev"><summary>相关证据 ${ev.length} 条</summary><ul>${ev.map(x=>`<li><span class="evidence-badge">${esc(x.kind)}</span>${esc(x.statement)} <b>动作：</b>${esc(x.action)} ${link(x.url,"来源")}${x.via?" · "+link(x.via,"转述"):""}<span class="task-detail">${x.verification==="search-summary"?"检索摘要，原页未直接打开":""} · ${esc(x.checkedAt)}</span></li>`).join("")}</ul></details>`:""}
        ${start?.note&&start.kind!=="官方默认"?`<p class="small muted">起步依据：${esc(start.note)} ${start.url?link(start.url,"来源"):""}</p>`:""}</article>`;
    }).join("");
    const wide=mpEvidence(entry.id,null);
    $("profileEvidence").innerHTML=wide.length?`<h4>适用于全部任务的证据</h4><ul>${wide.map(x=>`<li><span class="evidence-badge">${esc(x.kind)}</span>${esc(x.statement)} <b>动作：</b>${esc(x.action)} ${link(x.url,"来源")}<span class="task-detail">${x.verification==="search-summary"?"检索摘要，原页未直接打开":""} · ${esc(x.checkedAt)}</span></li>`).join("")}</ul>`:`<p class="small muted">暂无适用于全部任务的补充证据。</p>`;
  }
  function mpExportRows(){
    const a=mpAnalyse(mpEntry(mpView.model)), out=[], pits=mpPitfalls(a.entry);
    a.series.forEach(s=>s.points.forEach(p=>out.push({model:a.cat.name,model_id:a.entry.id,task:(MP.taskAxis.find(t=>t.id===s.task)||{}).label,benchmark:s.bench,effort:p.effort,
      native_supported:a.efforts.listed.includes(p.effort)?"是":a.efforts.pending.includes(p.effort)?"待核验":"目录未列",official_default:p.effort===a.cat.default_effort,
      score:p.score,unit:s.unit,cost_usd:p.cost,cost_definition:s.costLabel,fallback:p.fallback,
      knee_thrifty:s.res.thrifty?.pick.effort,knee_balanced:s.res.balanced?.pick.effort,knee_performance:s.res.performance?.pick.effort,
      start_effort:mpStart(a,s.task)?.effort,start_basis:mpStart(a,s.task)?.kind,
      pitfalls:pits.filter(x=>x.config?x.effort===p.effort:x.s.key===s.key&&x.p===p).map(x=>mpPitMeta[x.kind].label+(x.config?`→${mpCat(x.alt.id).name} ${x.f}`:"")).join("；"),source_url:p.url||s.url})));
    return out;
  }
  if($("profileModel")){
    const vendors=["Anthropic","OpenAI","Google","xAI"];
    $("profileModel").innerHTML=vendors.map(v=>`<optgroup label="${v}">${MP.models.filter(m=>mpCat(m.id)?.vendor===v).map(m=>{const c=mpCat(m.id),t=(MP.tiers||[]).find(x=>x.id===m.tier);return `<option value="${esc(m.id)}">${esc(c.name)} · ${esc(t?.label||"")}${c.lifecycle==="Deprecated"?" · 已弃用":""}</option>`;}).join("")}</optgroup>`).join("");
    const setModel=id=>{mpView.model=id;mpView.task=null;mpAltView.effort=null;renderModelProfile();if(!$("profiles").hidden)history.replaceState(null,"","#profiles?m="+encodeURIComponent(id));};
    $("profileModel").addEventListener("change",e=>setModel(e.target.value));
    $("profileTolerance").addEventListener("change",renderModelProfile);
    $("profilePitfalls").addEventListener("change",renderModelProfile);
    $("profileAltEffort").addEventListener("change",e=>{mpAltView.effort=e.target.value;renderModelProfile();});
    $("profileAltScope").addEventListener("change",e=>{mpAltView.scope=e.target.value;renderModelProfile();});
    $("profileQuick").innerHTML=MP.models.filter(m=>m.tier==="main").map(m=>`<button type="button" class="pill-btn" data-mp-quick="${esc(m.id)}">${esc(mpCat(m.id).short||mpCat(m.id).name)}</button>`).join("");
    $("profileQuick").querySelectorAll("[data-mp-quick]").forEach(b=>b.addEventListener("click",()=>{$("profileModel").value=b.dataset.mpQuick;setModel(b.dataset.mpQuick);}));
    $("exportProfile").addEventListener("click",()=>exportCSV(mpExportRows(),`模型档案-${mpView.model}-${MP.checkedAt}.csv`));
  }

  // BEGIN MARKET_MATH
  function usesLongContextPrice(model, input) {
    return finite(model.tier_threshold) && (model.tier_inclusive ? input >= model.tier_threshold : input > model.tier_threshold);
  }
  function marketRows(board, query, vendor, sort) {
    const needle = query.trim().toLocaleLowerCase();
    return board.rows.filter(row => (vendor === "all" || row.vendor === vendor) &&
      `${row.model} ${row.vendor} ${row.configuration}`.toLocaleLowerCase().includes(needle))
      .slice().sort((a,b) => {
        if (sort === "cost") {
          if (finite(a.cost_usd) !== finite(b.cost_usd)) return finite(a.cost_usd) ? -1 : 1;
          if (finite(a.cost_usd) && a.cost_usd !== b.cost_usd) return a.cost_usd - b.cost_usd;
        }
        if (finite(a.score) !== finite(b.score)) return finite(a.score) ? -1 : 1;
        return (b.score ?? 0) - (a.score ?? 0);
      });
  }
  function marketExportRows(board, rows) {
    return rows.map(row => ({...row, source:board.name, metric:board.metric, unit:board.unit,
      version:board.version, cost_basis:board.cost_basis, source_updated_at:board.source_updated_at,
      checked_at:board.checked_at, source_url:board.source_url}));
  }
  // END MARKET_MATH

  // Store only a display preference; the report stays entirely offline.
  const themeMedia = window.matchMedia("(prefers-color-scheme: dark)");
  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme === "auto" ? (themeMedia.matches ? "dark" : "light") : theme;
    $("themeSelect").value = theme;
  }
  let savedTheme = "auto";
  try { savedTheme = localStorage.getItem("observatory-theme") || "auto"; } catch (_) { /* Storage is optional. */ }
  applyTheme(["auto","light","dark"].includes(savedTheme) ? savedTheme : "auto");
  $("themeSelect").addEventListener("change", event => {
    applyTheme(event.target.value);
    try { localStorage.setItem("observatory-theme", event.target.value); } catch (_) { /* Storage is optional. */ }
  });
  themeMedia.addEventListener("change", () => { if ($("themeSelect").value === "auto") applyTheme("auto"); });

  const market = DATA.market_snapshot;
  const marketState = {board:"aa", expanded:false};
  const currentMarketBoard = () => market.boards.find(board => board.id === marketState.board);
  const currentMarketRows = () => marketRows(currentMarketBoard(), $("marketSearch").value, $("marketVendor").value, $("marketSort").value);
  const marketScore = (board, row) => `${fmt(row.score,board.precision)}${finite(row.interval) ? ` <small>±${fmt(row.interval,2)}</small>` : ""}<span class="score-unit">${esc(board.unit)}</span>`;
  function renderMarket() {
    const board = currentMarketBoard(), rows = currentMarketRows();
    const visible = marketState.expanded ? rows : rows.slice(0,8);
    const maxScore = Math.max(...board.rows.map(row => row.score).filter(finite),1);
    $("boardButtons").querySelectorAll("button").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.board === board.id)));
    $("boardTitle").textContent = board.metric;
    $("boardMeta").textContent = `${board.version} · 来源更新 ${board.source_updated_at || "未披露"} · 核验 ${board.checked_at}`;
    $("boardSource").href = board.source_url;
    $("boardNote").textContent = board.note;
    $("boardSelection").textContent = board.selection;
    $("boardCostBasis").textContent = board.cost_basis;
    $("marketSort").options[0].textContent = board.id === "openrouter" ? "用量从高到低" : "分数从高到低";
    $("marketSort").options[1].disabled = !board.cost_label;
    const costHeader = board.cost_label ? `${esc(board.cost_label)}<small>USD / ${board.id === "livebench" ? "成功任务" : "任务"}</small>` : "费用<small>本视图未提供</small>";
    $("marketTable").innerHTML = rows.length ? `<table class="market-table"><caption class="sr">${esc(board.name)} · ${esc(board.metric)} · 当前选录，非跨站总榜</caption><thead><tr><th scope="col">序号</th><th scope="col">模型 / 测试配置</th><th scope="col">${esc(board.id === "openrouter" ? "用量" : "得分")}</th><th scope="col">${costHeader}</th><th scope="col">${esc(board.extra_label)}</th></tr></thead><tbody>${visible.map((row,i) => {
      const extra = row[board.extra_key];
      return `<tr><td class="row-number">${String(i+1).padStart(2,"0")}</td><th scope="row"><span class="market-model">${esc(row.model)}</span><span class="market-config">${esc(row.vendor)} <span aria-hidden="true">/</span> ${esc(row.configuration)}${row.source_rank ? ` · 来源 #${row.source_rank}` : ""}</span></th><td class="market-score" data-label="${esc(board.id === "openrouter" ? "用量" : "得分")}"><b>${marketScore(board,row)}</b><span class="score-track" aria-hidden="true"><span style="width:${Math.max(0,Math.min(100,100*row.score/maxScore))}%"></span></span></td><td class="market-cost" data-label="${esc(board.cost_label || "费用")}">${finite(row.cost_usd) ? money(row.cost_usd) : '<span class="missing-value">—<span class="sr">未提供</span></span>'}</td><td class="market-extra" data-label="${esc(board.extra_label)}">${typeof extra === "string" ? esc(extra) : finite(extra) ? fmt(extra,2) : "—"}${extra != null && board.extra_unit ? `<small>${esc(board.extra_unit)}</small>` : ""}</td></tr>`;
    }).join("")}</tbody></table>` : '<div class="market-empty"><b>没有匹配的模型</b><p>试试模型简称，或重置筛选查看本次选录。</p></div>';
    $("marketCount").textContent = `显示 ${visible.length} / ${rows.length} 项 · 本榜选录 ${board.rows.length} 项`;
    $("marketMore").hidden = rows.length <= 8;
    $("marketMore").textContent = marketState.expanded ? "收起列表 ↑" : `显示全部 ${rows.length} 项 ↓`;
    $("marketMore").setAttribute("aria-expanded", String(marketState.expanded));
    $("exportMarket").disabled = !rows.length;
  }
  function selectMarketBoard(id) {
    if (!market.boards.some(board => board.id === id)) return;
    marketState.board = id;
    marketState.expanded = false;
    const board = currentMarketBoard(), previous = $("marketVendor").value;
    const vendors = [...new Set(board.rows.map(row => row.vendor))].sort();
    $("marketVendor").innerHTML = '<option value="all">全部厂商</option>' + vendors.map(vendor => `<option value="${esc(vendor)}">${esc(vendor)}</option>`).join("");
    $("marketVendor").value = vendors.includes(previous) ? previous : "all";
    if (!board.cost_label) $("marketSort").value = "score";
    renderMarket();
  }
  function renderMarketIntro() {
    $("snapshotDate").textContent = market.reviewed_at;
    $("reviewDate").textContent = `${market.reviewed_at} 核验`;
    document.querySelector(".edition b").textContent = market.reviewed_at.slice(5).replace("-", " / ");
    $("heroStats").innerHTML = [[market.boards.length,"主流榜单"],[DATA.models.length,"规格型号"],[Object.keys(DATA.aa_effort_evals.variants).length,"已测档位"],[market.boards.reduce((n,b)=>n+b.rows.length,0),"榜单选录"]].map(([value,label]) => `<span><b>${value}</b>${label}</span>`).join("");
    $("heroSignals").innerHTML = market.highlights.map(item => {
      const board = market.boards.find(b => b.id === item.board_id), row = board.rows.find(r => r.id === item.row_id);
      return `<button class="signal-row" data-market-board="${esc(board.id)}"><span class="signal-kind">${esc(item.label)}</span><span class="signal-model"><b>${esc(row.model)}</b><small>${esc(item.caption)}</small></span><strong>${fmt(row.score,board.precision)}<span>${esc(board.unit)}</span></strong><span class="signal-arrow" aria-hidden="true">↗</span></button>`;
    }).join("");
    $("heroSignals").querySelectorAll("button").forEach(button => button.addEventListener("click", () => {
      showPanel("overview"); $("marketSearch").value=""; $("marketVendor").value="all"; $("marketSort").value="score";
      selectMarketBoard(button.dataset.marketBoard); $("latestBenchmarks").scrollIntoView({block:"start"});
    }));
    $("boardButtons").innerHTML = market.boards.map(board => `<button data-board="${esc(board.id)}" aria-pressed="false">${esc(board.short)}</button>`).join("");
    $("boardButtons").querySelectorAll("button").forEach(button => button.addEventListener("click", () => selectMarketBoard(button.dataset.board)));
    $("marketUpdates").innerHTML = market.changes.map((change,i) => `<div class="research-update"><span class="update-index">0${i+1}</span><div><h4>${esc(change.title)}</h4><p>${esc(change.body)}</p></div></div>`).join("");
    $("priceCalendar").innerHTML = DATA.models.filter(model => model.promo_end && finite(model.future_input)).map(model => `<div class="price-event"><time datetime="${esc(model.promo_end)}">${esc(model.promo_end)}</time><b>${esc(model.name)}</b><p>输入 / 输出：${money(model.input)} / ${money(model.output)}<br>结束后 ${money(model.future_input)} / ${money(model.future_output)}<small>USD / 百万 token · ${link(model.price_source,"官方价格")}</small></p></div>`).join("");
    $("officialChecks").innerHTML = '<span class="small">官方价格 · 本期已核验</span>' + market.official_sources.map(source => `<a href="${esc(source.url)}" target="_blank" rel="noopener" title="${esc(source.note)}"><span aria-hidden="true">✓</span> ${esc(source.vendor)} <span class="check-date">${esc(source.checked_at)}</span><span aria-hidden="true">↗</span></a>`).join("");
  }
  $("marketSearch").addEventListener("input", () => {marketState.expanded=false;renderMarket();});
  ["marketVendor","marketSort"].forEach(id => $(id).addEventListener("change", () => {marketState.expanded=false;renderMarket();}));
  $("marketMore").addEventListener("click", () => {marketState.expanded=!marketState.expanded;renderMarket();});
  $("marketReset").addEventListener("click", () => {$("marketSearch").value="";$("marketVendor").value="all";$("marketSort").value="score";marketState.expanded=false;renderMarket();});
  $("exportMarket").addEventListener("click", () => exportCSV(marketExportRows(currentMarketBoard(),currentMarketRows()),`模型观测-${marketState.board}-${market.reviewed_at}.csv`));
  document.querySelectorAll("[data-scroll]").forEach(button => button.addEventListener("click", () => {showPanel("overview");$(button.dataset.scroll)?.scrollIntoView({block:"start"});}));
  renderMarketIntro();selectMarketBoard("aa");
  renderSweetSpot();renderReasoningCharts();renderTaskEffortChart();renderEffortScalingChart();renderPanorama();renderClaudeCatalog();renderProfiles();renderCapIndexChart();renderSpecs();renderDeltas();changeGroup("general");showPanel(location.hash.slice(1)||"overview",false);
})();
