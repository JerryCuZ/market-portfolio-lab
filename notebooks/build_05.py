"""Author lesson 05; execution and publication are separate reviewed steps."""
from pathlib import Path
import nbformat as nbf
path = Path(__file__).with_name('05_allocation_constraints.ipynb')
nb = nbf.read(path, as_version=4)
cells = []
def md(s): cells.append(nbf.v4.new_markdown_cell(s))
def code(s): cells.append(nbf.v4.new_code_cell(s))
md('''# 第五课：配置稳定性与执行约束

已经理解 ERC 的你，现在要学习如何把理论配置变成可检查的执行规则。

本课依次研究：① 风险估计窗口；② 单资产目标上限；③ 调仓门槛；④ 账目核对与取舍。重点不是选历史冠军，而是看每个假设改变了什么。

**预先固定的教学参数**：63／126／252 个交易日，50% 单资产目标上限，3 个百分点调仓门槛。没有优化或搜索这些参数；历史已被观察，不是样本外证据。继续使用原快照，让方法比较不被数据刷新混淆。''')
code('''from pathlib import Path
import sys, os, json, hashlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
ROOT = Path.cwd()
if not (ROOT/'src').exists(): ROOT = ROOT.parent
sys.path.insert(0, str(ROOT/'src'))
from market_data import load_snapshot
from risk_models import equal_risk_schedule, cap_weights, risk_contributions
from portfolio import simulate, reconcile
SNAPSHOT = os.environ.get('MARKET_LAB_SNAPSHOT', '20261007T234808781424Z')
frames, manifest = load_snapshot(SNAPSHOT)
prices = pd.DataFrame({s:f['Adj Close'] for s,f in frames.items()})
assets = list(prices.columns)
OUT = ROOT/'reports'/('05_'+SNAPSHOT)
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'figure.figsize':(11,4), 'axes.grid':True, 'grid.alpha':.2})
full = {n:equal_risk_schedule(prices,n)[0] for n in [63,126,252]}
START = max(s.index[0] for s in full.values())
schedules = {f'erc_{n}':s.loc[START:].copy() for n,s in full.items()}
base = schedules['erc_126']
assert all(s.index.equals(base.index) for s in schedules.values())
trading = {s:f.loc[START:].copy() for s,f in frames.items()}
print('快照：', SNAPSHOT, '；行情截至：', prices.index[-1].date())
print('统一模拟区间：', START.date(), '至', prices.index[-1].date(), '；月度机会：', len(base))
print('最长窗口需要更长预热期，所有实验从同一天投入相同本金。不能直接与第四课的全区间数值比较。')''')
md('''## 1. 回看窗口：估计风险时参考多久的历史？

63／126／252 个交易日大约对应一季／半年／一年。短窗口通常更快响应新变化，也可能更容易受短期噪声影响；长窗口更平滑，但可能混入已经变化的市场关系。哪一个更好不能仅凭一次回测决定。

每次目标只用执行日前已经结束的收益计算协方差。这里的“稳定性”用相邻两个月目标权重差的绝对值之和衡量。例如从 20/60/20 到 25/55/20，变化合计为 10 个百分点。这不是实际换手率，因为真实持仓还会随价格漂移。''')
code('''stability = pd.DataFrame({name: {
    'mean_target_change_pp': s[assets].diff().abs().sum(axis=1).iloc[1:].mean()*100,
    'max_single_target': s[assets].max().max(),
} for name,s in schedules.items()}).T
display(stability.style.format({'mean_target_change_pp':'{:.2f}', 'max_single_target':'{:.2%}'}))
fig, axes = plt.subplots(3,1,figsize=(11,8),sharex=True)
for ax,asset in zip(axes,assets):
    for name,s in schedules.items(): ax.plot(s.index,s[asset]*100,label=name,alpha=.8)
    ax.set_ylabel(asset+' target (%)')
axes[0].legend(); fig.tight_layout(); plt.show()
stability.to_csv(OUT/'window_stability.csv')''')
md('''## 2. 目标上限：限制资金集中，但接受风险预算偏离

本课明确采用简单、透明的**截顶后按比例再分配**规则：超过 50% 的资产先设为 50%，剩余资金按其他资产原来的权重比例分配；若再次超限，重复操作。总权重仍为 100%。

例如 70/20/10 变成 50/33.33/16.67。不能仅截成 50/20/10（留下现金），也不能把它再整体归一化（可能重新超限）。三资产若上限小于三分之一，则无法在无现金条件下全部投满。

**这叫 ERC 加资金上限覆盖规则，不叫约束 ERC 最优解。** 它没有最小化风险预算误差，不保证等风险。目标上限也不是全天候持仓硬上限：成交后价格漂移仍可能使某资产超过 50%。''')
code('''capped = base.copy()
capped[assets] = base[assets].apply(lambda row:cap_weights(row,.5),axis=1)
# ERC diagnostics no longer describe the modified target: do not retain them.
capped = capped.drop(columns=['iterations','max_risk_share_error'],errors='ignore')
schedules['cap_50'] = capped
returns = prices.pct_change(fill_method=None)
risk_rows = []
for date in base.index:
    i = prices.index.get_loc(date)
    cov = returns.iloc[i-126:i].cov()*252
    for name,s in [('erc_126',base),('cap_50',capped)]:
        rc,vol = risk_contributions(s.loc[date,assets],cov)
        for asset,row in rc.iterrows():
            risk_rows.append(dict(date=date,policy=name,asset=asset,**row.to_dict()))
risk = pd.DataFrame(risk_rows)
print('共同区间第一次决策的资金比例与风险占比：')
display(risk[risk.date==START].set_index(['policy','asset'])[['capital_weight','risk_share']].style.format('{:.2%}'))
assert capped[assets].max().max() <= .5+1e-12
assert np.allclose(capped[assets].sum(axis=1),1)
print('上限触发月份：', int((base[assets].max(axis=1)>.5).sum()), '/',len(base))
risk.to_csv(OUT/'target_risk_audit.csv',index=False)''')
md('''## 3. 调仓门槛：有了新目标，也不必每次都交易

“3 个百分点”指绝对权重差，例如实际 48%、目标 50%，差为 2 个百分点，不是相对变化 2/50=4%。

规则：首次必须买入；之后只在月度机会检查。以前一收盘的现金与份额估值，计算各资产及现金相对新目标的最大绝对偏离。**大于** 3 个百分点才调回整个目标；等于或低于门槛则不交易。每月仍更新目标，不是一直对照上次交易目标。

触发判断使用前一收盘信息；次日开盘价才用于计算成交份额，仍沿用理想化开盘成交。开盘跳空不会反过来改变前一晚的触发决定。当日分红也不会提前进入前一晚现金。我们没有逐日监控或盘中止损。

为了单独观察门槛的影响，它叠加在原始 126 日 ERC 上，**没有同时叠加 50% 上限**。减少交易可能降低费用，也会放任持仓偏离目标，甚至错过快速变化。''')
code('''results = {name:simulate(trading,s.iloc[0][assets].to_dict(),target_schedule=s)
           for name,s in schedules.items()}
results['band_3pp'] = simulate(trading,base.iloc[0][assets].to_dict(),
    target_schedule=base,rebalance_threshold=.03)
metrics = pd.DataFrame({name:r.metrics() for name,r in results.items()}).T
metrics['skipped_opportunities'] = [int((r.daily.rebalance_opportunity & ~r.daily.rebalance).sum()) for r in results.values()]
# Gross traded / prior-close NAV is an explicit two-sided convention; includes initial entry.
metrics['gross_turnover_per_year'] = [
    (r.trades.groupby('date').notional.apply(lambda x:x.abs().sum()) /
     r.daily.nav.shift(1).fillna(r.initial_cash)).sum() /
    ((r.daily.index[-1]-r.daily.index[0]).days/365.25) for r in results.values()]
cols = ['cagr','annual_volatility','max_drawdown','fees_paid','trade_days','skipped_opportunities','gross_turnover_per_year']
display(metrics[cols].style.format({'cagr':'{:.2%}','annual_volatility':'{:.2%}',
    'max_drawdown':'{:.2%}','fees_paid':'{:,.2f}','trade_days':'{:.0f}',
    'skipped_opportunities':'{:.0f}','gross_turnover_per_year':'{:.2f}'}))
print('列：年化收益／年化波动／最大回撤／费用美元／实际交易日数／跳过机会／年均双边成交额÷前日净值。')
print('成交额指标含首次建仓；费用还受净值路径影响，因此不能仅按费用比较交易频繁程度。')
metrics.to_csv(OUT/'metrics.csv')
fig,axes = plt.subplots(2,1,figsize=(11,7),sharex=True)
for name in ['erc_126','cap_50','band_3pp']:
    r = results[name]; nav = r.daily.nav
    peak = np.maximum.accumulate(np.r_[r.initial_cash,nav])[1:]
    axes[0].plot(nav.index,nav/r.initial_cash,label=name)
    axes[1].plot(nav.index,(nav/peak-1)*100,label=name)
axes[0].legend(); axes[0].set_ylabel('Growth of capital'); axes[1].set_ylabel('Drawdown (%)')
fig.tight_layout(); plt.show()
a,b = metrics.loc['erc_126'],metrics.loc['band_3pp']
display(Markdown(f'门槛规则把交易日从 **{a.trade_days:.0f}** 减到 **{b.trade_days:.0f}**，累计费用从 **${a.fees_paid:,.2f}** 变为 **${b.fees_paid:,.2f}**；年化收益差为 **{(b.cagr-a.cagr)*100:+.2f} 个百分点**。收益差同时反映持仓路径和费用变化，不等于单纯节省费用。'))''')
md('''## 4. 放弃多少跟踪精度？检查持仓而不只看收益

下面在每个交易日收盘，把真实账本权重与最近一次目标比较（现金也算一项），取最大绝对差，再汇总均值和最大值。它是配置偏离指标，不是通常指“相对基准收益波动”的 tracking error。

即使每月严格调仓，月内价格变化也会产生偏离；门槛策略还允许部分月度机会不交易。这里的 50% 只限制目标；下面同时展示实际持仓的最高权重。''')
code('''drift_rows = []
for name,r in results.items():
    s = base if name=='band_3pp' else schedules[name]
    target = s[assets].reindex(r.daily.index).ffill()
    actual = r.daily[[a+'_weight' for a in assets]].copy(); actual.columns = assets
    actual['cash'] = r.daily.cash/r.daily.nav
    target['cash'] = 1-target.sum(axis=1)
    gap = (actual-target).abs().max(axis=1)
    drift_rows.append(dict(policy=name,mean_close_gap=gap.mean(),max_close_gap=gap.max(),
        max_actual_asset_weight=actual[assets].max().max()))
drift = pd.DataFrame(drift_rows).set_index('policy')
display(drift.style.format('{:.2%}')); drift.to_csv(OUT/'holding_drift.csv')
checks = pd.DataFrame({name:reconcile(r) for name,r in results.items()}).T
assert checks.to_numpy().max()<1e-6
for name,r in results.items():
    r.daily.to_csv(OUT/(name+'_daily.csv'))
    r.trades.to_csv(OUT/(name+'_trades.csv'),index=False)
for name,s in schedules.items(): s.to_csv(OUT/(name+'_targets.csv'))
settings = dict(snapshot=SNAPSHOT,start=str(START.date()),end=str(prices.index[-1].date()),
    lookbacks=[63,126,252],cap=.5,threshold=.03,initial_cash=100000,cost_bps=5,
    cap_method='proportional redistribution; not constrained ERC',
    threshold_timing='previous close, monthly opportunities; includes cash; strict greater-than',
    source_manifest=manifest,code_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
        for p in ['src/risk_models.py','src/portfolio.py','notebooks/build_05.py']})
(OUT/'run_manifest.json').write_text(json.dumps(settings,indent=2),encoding='utf-8')
print('五种方案独立对账通过，最大误差：',checks.to_numpy().max())''')
md('''## 5. 本课结论、练习与下一步

**配置层的作用**：把研究判断转成资金和风险分配。本课新增的约束层说明如何接受现实取舍；下一阶段的信号层才研究何时、根据什么理由增减风险敞口。以后机器学习也应复用同一个执行账本。

本课没有寻找最优窗口、最优上限或最优门槛。窗口敏感性不等于样本外有效；资金集中降低不必然降低波动；减少交易也不保证改善收益。不要根据本表直接选“冠军”。

局限继续包括：修订后的历史数据、无独立样本外验证、5 bps 固定单边成本、零碎份额与理想开盘成交、分红除息日立即入账、现金零利息、无个人税费。没有在线行情或实盘指令。本节只测试窗口长度，尚未研究协方差收缩等估计方法。

**练习**：
1. 昨日收盘最大偏离 2 个百分点，今日开盘跳到 8 个百分点，3 点门槛是否触发？
2. 资金上限 50% 是否保证风险占比不超过 50%，或每天持仓不超过 50%？
3. 更换 252 日窗口后，为什么必须把其他方案的起点也延后？

**参考答案**：1. 不触发，本规则在前一收盘做判断。2. 都不保证，风险贡献使用协方差，实际资金比例还会漂移。3. 避免不同市场区间造成不公平比较；所有组合在共同起点重新从现金开始。

下一节：固定简单的趋势信号，比较“仅风险配置”和“风险配置＋趋势过滤”。先定义信号、执行时间和现金处理，再进行历史与样本外检验，不从众多参数中追逐最好曲线。''')
nb.cells = cells
nb.metadata['kernelspec'] = {'display_name':'Market & Portfolio Lab (Python 3.11)','language':'python','name':'market-portfolio-lab'}
nbf.write(nb,path)
print(path)
