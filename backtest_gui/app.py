# ============================================================
# 必须在所有其他 import 之前设置 hikyuu 的 DLL 路径并加载
# 原因：hikyuu 包含 C++ 扩展（DLL/PYD），Python 3.8+ 在 Windows 上
# 加载 DLL 时只识别 os.add_dll_directory() 注册的路径，不读系统 PATH
# ============================================================
import os
import sys

# 你的 hikyuu DLL 目录（根据 pip show hikyuu 的 Location 拼出）
_HKU_CPP = r'C:\Users\123\AppData\Local\Programs\Python\Python311\Lib\site-packages\hikyuu\cpp'

if os.path.isdir(_HKU_CPP):
    os.add_dll_directory(_HKU_CPP)
    os.environ['PATH'] = _HKU_CPP + os.pathsep + os.environ.get('PATH', '')

HKU_AVAILABLE = False
HKU_ERROR = ""
sm = None
_StockManager = None
_SYS_Simple = None
_SG_Flex = None
_EMA = None
_CLOSE = None
_MM_FixedCount = None
_ST_FixedPercent = None
_crtTM = None
_TC_FixedA2017 = None
_Query = None
_Datetime = None

try:
    from hikyuu import (
        StockManager, SYS_Simple, SG_Flex, EMA, CLOSE,
        MM_FixedCount, ST_FixedPercent, crtTM, TC_FixedA2017,
        Query, Datetime, load_hikyuu
    )
    _StockManager = StockManager
    _SYS_Simple = SYS_Simple
    _SG_Flex = SG_Flex
    _EMA = EMA
    _CLOSE = CLOSE
    _MM_FixedCount = MM_FixedCount
    _ST_FixedPercent = ST_FixedPercent
    _crtTM = crtTM
    _TC_FixedA2017 = TC_FixedA2017
    _Query = Query
    _Datetime = Datetime

    # 关键：必须显式调用 load_hikyuu() 才能加载股票数据
    # 如果不调用，StockManager 里没有数据，get_stock() 永远返回 NULL
    load_hikyuu(
        stock_list=["all"],
        ktype_list=["day"],
        load_history_finance=False,
        load_weight=False,
        start_spot=False
    )
    # load_hikyuu 后重新获取 sm 实例
    sm = StockManager.instance()
    HKU_AVAILABLE = True
    HKU_ERROR = ""
except Exception as e:
    HKU_AVAILABLE = False
    HKU_ERROR = repr(e)
    sm = None


def get_hikyuu_status():
    if HKU_AVAILABLE:
        try:
            # 诊断信息：检查数据是否真的加载了
            stock_count = sum(1 for _ in sm)
            data_dir = sm.data_dir
            return (
                f"✅ Hikyuu 已连接，可以进行回测\n\n"
                f"已加载股票数：{stock_count}\n"
                f"数据目录：{data_dir}"
            )
        except Exception:
            return "✅ Hikyuu 已连接，可以进行回测"
    else:
        py_path = sys.executable
        return f"❌ Hikyuu 未连接\n\nPython路径：{py_path}\n\n错误信息：{HKU_ERROR}"


# ============================================================
# 加载完 hikyuu 之后，再加载其他库
# ============================================================
import gradio as gr
import pandas as pd
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def plot_kline(kline_df, trades_df, fast_period, slow_period):
    if kline_df is None or kline_df.empty:
        return None

    fig, ax = plt.subplots(figsize=(12, 6))

    n = len(kline_df)
    x = np.arange(n)

    opens = kline_df['开盘'].values
    highs = kline_df['最高'].values
    lows = kline_df['最低'].values
    closes = kline_df['收盘'].values

    width = 0.6

    for i in range(n):
        if closes[i] >= opens[i]:
            color = 'red'
        else:
            color = 'green'

        ax.plot([x[i], x[i]], [lows[i], highs[i]], color=color, linewidth=1)

        rect_height = abs(closes[i] - opens[i])
        rect_bottom = min(opens[i], closes[i])
        rect = Rectangle((x[i] - width / 2, rect_bottom), width, rect_height,
                         facecolor=color, edgecolor=color)
        ax.add_patch(rect)

    fast_ema = kline_df['收盘'].ewm(span=fast_period, adjust=False).mean()
    slow_ema = kline_df['收盘'].ewm(span=slow_period, adjust=False).mean()

    ax.plot(x, fast_ema.values, color='orange', label=f'快线 EMA({fast_period})', linewidth=1.5)
    ax.plot(x, slow_ema.values, color='blue', label=f'慢线 EMA({slow_period})', linewidth=1.5)

    if trades_df is not None and not trades_df.empty:
        buy_trades = trades_df[trades_df['方向'] == '买入']
        sell_trades = trades_df[trades_df['方向'] == '卖出']

        date_to_idx = {date: idx for idx, date in enumerate(kline_df['日期'])}

        for _, trade in buy_trades.iterrows():
            date = trade['日期']
            if date in date_to_idx:
                idx = date_to_idx[date]
                low_price = lows[idx]
                ax.scatter(idx, low_price * 0.98, marker='^', color='red', s=100, zorder=5)

        for _, trade in sell_trades.iterrows():
            date = trade['日期']
            if date in date_to_idx:
                idx = date_to_idx[date]
                high_price = highs[idx]
                ax.scatter(idx, high_price * 1.02, marker='v', color='green', s=100, zorder=5)

    ax.set_title('K线走势图', fontsize=14, fontweight='bold')
    ax.set_ylabel('价格', fontsize=12)
    ax.set_xlabel('日期', fontsize=12)

    step = max(1, n // 10)
    ax.set_xticks(x[::step])
    ax.set_xticklabels(kline_df['日期'].values[::step], rotation=45, ha='right')

    ax.legend(loc='best')
    ax.grid(True, linestyle='--', alpha=0.3, color='lightgray')

    plt.tight_layout()
    return fig


def plot_equity(equity_df, initial_capital):
    if equity_df is None or equity_df.empty:
        return None

    fig, ax = plt.subplots(figsize=(12, 4))

    x = np.arange(len(equity_df))
    total_assets = equity_df['总资产'].values

    ax.plot(x, total_assets, color='blue', linewidth=1.5, label='总资产')

    ax.axhline(y=initial_capital, color='gray', linestyle='--', linewidth=1, label='初始资金')

    max_idx = np.argmax(total_assets)
    min_idx = np.argmin(total_assets)
    max_val = total_assets[max_idx]
    min_val = total_assets[min_idx]

    ax.annotate(f'最高点: {max_val:.2f}',
                xy=(max_idx, max_val),
                xytext=(max_idx, max_val * 1.05),
                arrowprops=dict(facecolor='red', shrink=0.05, width=1, headwidth=6),
                fontsize=10,
                ha='center',
                color='red')

    ax.annotate(f'最低点: {min_val:.2f}',
                xy=(min_idx, min_val),
                xytext=(min_idx, min_val * 0.95),
                arrowprops=dict(facecolor='green', shrink=0.05, width=1, headwidth=6),
                fontsize=10,
                ha='center',
                color='green')

    ax.set_title('资金曲线', fontsize=14, fontweight='bold')
    ax.set_ylabel('资产 (元)', fontsize=12)
    ax.set_xlabel('日期', fontsize=12)

    n = len(equity_df)
    step = max(1, n // 10)
    ax.set_xticks(x[::step])
    ax.set_xticklabels(equity_df['日期'].values[::step], rotation=45, ha='right')

    ax.legend(loc='best')
    ax.grid(True, linestyle='--', alpha=0.3, color='lightgray')

    plt.tight_layout()
    return fig


def run_backtest(stock_code, strategy, fast_period, slow_period, stop_loss, initial_capital, buy_quantity, backtest_days):
    try:
        is_valid, message = validate_stock(stock_code)
        if not is_valid:
            error_md = f'<span style="color:red">**错误：{message}**</span>'
            empty_df = pd.DataFrame()
            return error_md, empty_df, None, empty_df, None

        is_valid, message = validate_params(int(fast_period), int(slow_period), stop_loss, int(buy_quantity))
        if not is_valid:
            error_md = f'<span style="color:red">**错误：{message}**</span>'
            empty_df = pd.DataFrame()
            return error_md, empty_df, None, empty_df, None

        if not HKU_AVAILABLE:
            error_md = '<span style="color:red">**错误：Hikyuu未安装，无法进行回测**</span>'
            empty_df = pd.DataFrame()
            return error_md, empty_df, None, empty_df, None

        fast_period = int(fast_period)
        slow_period = int(slow_period)
        buy_quantity = int(buy_quantity)
        backtest_days = int(backtest_days)

        full_code = normalize_stock_code(stock_code)
        stk = sm.get_stock(full_code)
        if stk is None:
            error_md = f'<span style="color:red">**错误：无法获取股票 {full_code}，请检查股票代码是否正确或数据是否已下载**</span>'
            empty_df = pd.DataFrame()
            return error_md, empty_df, None, empty_df, None
        
        try:
            if hasattr(stk, 'is_null') and stk.is_null():
                error_md = f'<span style="color:red">**错误：股票 {full_code} 数据为空，请先下载数据**</span>'
                empty_df = pd.DataFrame()
                return error_md, empty_df, None, empty_df, None
        except Exception:
            pass

        my_tm = crtTM(init_cash=initial_capital, cost_func=TC_FixedA2017())
        my_sg = SG_Flex(EMA(CLOSE(), n=fast_period), slow_n=slow_period)
        my_mm = MM_FixedCount(buy_quantity)
        my_st = ST_FixedPercent(stop_loss)
        my_sys = SYS_Simple(tm=my_tm, sg=my_sg, mm=my_mm, st=my_st)

        my_sys.run(stk, Query(-backtest_days))

        performance = my_sys.tm.get_performance()

        def get_perf(key, default="--"):
            try:
                val = performance[key]
                if hasattr(val, '__float__'):
                    return float(val)
                return val
            except (KeyError, TypeError, Exception):
                return default

        total_return = get_perf("未平仓帐户收益率%", "--")
        annual_return = get_perf("帐户年复合收益率%", "--")
        try:
            last_date = my_sys.tm.last_datetime
            max_drawdown = -float(my_sys.tm.get_max_pull_back(last_date, Query.DAY))
        except Exception:
            max_drawdown = "--"
        win_rate = get_perf("赢利交易比例%", "--")
        profit_loss_ratio = get_perf("平均赢利/平均亏损比例", "--")
        total_trades = get_perf("已平仓交易总数", "--")
        win_trades = get_perf("赢利交易数", "--")
        lose_trades = get_perf("亏损交易数", "--")

        def fmt_pct(val):
            if val == "--":
                return "--"
            return f"{val:.2f}%"

        def fmt_num(val):
            if val == "--":
                return "--"
            return f"{val:.2f}"

        def fmt_int(val):
            if val == "--":
                return "--"
            return str(int(val))

        perf_md = f"""
## 绩效概览

| 指标 | 数值 |
|------|------|
| 总收益率 | {fmt_pct(total_return)} |
| 年化收益率 | {fmt_pct(annual_return)} |
| 最大回撤 | {fmt_pct(max_drawdown)} |
| 胜率 | {fmt_pct(win_rate)} |
| 盈亏比 | {fmt_num(profit_loss_ratio)} |
| 交易次数 | {fmt_int(total_trades)} |
| 盈利次数 | {fmt_int(win_trades)} |
| 亏损次数 | {fmt_int(lose_trades)} |
"""

        perf_df = pd.DataFrame({
            "指标": ["总收益率", "年化收益率", "最大回撤", "胜率", "盈亏比", "交易次数", "盈利次数", "亏损次数"],
            "数值": [fmt_pct(total_return), fmt_pct(annual_return), fmt_pct(max_drawdown),
                     fmt_pct(win_rate), fmt_num(profit_loss_ratio), fmt_int(total_trades),
                     fmt_int(win_trades), fmt_int(lose_trades)]
        })

        # ===== 交易记录（使用官方 to_df，已确认列名） =====
        trades_df_raw = my_sys.tm.get_trade_list().to_df()
        if not trades_df_raw.empty:
            # 只保留实际买卖交易（排除 INIT 初始化记录）
            trades_filtered = trades_df_raw[trades_df_raw['business'].isin(['BUY', 'SELL'])].copy()
            if not trades_filtered.empty:
                # 安全处理日期转换：支持 Hikyuu Datetime 和 pandas datetime
                date_list = []
                for dt_val in trades_filtered['datetime']:
                    if hasattr(dt_val, 'datetime'):
                        date_list.append(dt_val.datetime().strftime("%Y-%m-%d"))
                    else:
                        date_list.append(pd.to_datetime(dt_val).strftime("%Y-%m-%d"))
                
                trades_df = pd.DataFrame({
                    "日期": date_list,
                    "方向": trades_filtered['business'].map({'BUY': '买入', 'SELL': '卖出'}).values,
                    "价格": trades_filtered['realPrice'].round(2).values,
                    "数量": trades_filtered['number'].abs().astype(int).values,
                    "金额": (trades_filtered['realPrice'].abs() * trades_filtered['number'].abs()).round(2).values,
                    "现金余额": trades_filtered['cash'].round(2).values
                })
                trades_df = trades_df.sort_values(by="日期", ascending=False).reset_index(drop=True)
            else:
                trades_df = pd.DataFrame(columns=["日期", "方向", "价格", "数量", "金额", "现金余额"])
        else:
            trades_df = pd.DataFrame(columns=["日期", "方向", "价格", "数量", "金额", "现金余额"])

        # ===== K线数据（KRecord 属性 open/high/low/close/volume 已在 draw 模块源码确认） =====
        kdata = stk.get_kdata(Query(-backtest_days))
        kline_data = []
        for k in kdata:
            kline_data.append({
                "日期": k.datetime.datetime().strftime("%Y-%m-%d"),
                "开盘": round(k.open, 2),
                "最高": round(k.high, 2),
                "最低": round(k.low, 2),
                "收盘": round(k.close, 2),
                "成交量": k.volume
            })
        kline_df = pd.DataFrame(kline_data)

        # ===== 资金曲线（使用官方 get_funds_curve，已确认 API） =====
        # 获取K线日期列表作为资金曲线的日期
        k_dates = stk.get_datetime_list(Query(-backtest_days))
        # 用 funds_curve 获取每日总资产（返回 PriceList）
        funds_list = my_sys.tm.get_funds_curve(k_dates, Query.DAY)
        equity_data = []
        for i, dt in enumerate(k_dates):
            equity_data.append({
                "日期": dt.datetime().strftime("%Y-%m-%d"),
                "总资产": float(funds_list[i]) if i < len(funds_list) else initial_capital
            })
        equity_df = pd.DataFrame(equity_data)

        kline_fig = plot_kline(kline_df, trades_df, fast_period, slow_period)
        equity_fig = plot_equity(equity_df, initial_capital)

        return perf_md, perf_df, kline_fig, trades_df, equity_fig

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        error_md = f'<span style="color:red">**错误：回测执行失败**</span>\n\n```\n{error_detail}\n```'
        empty_df = pd.DataFrame()
        return error_md, empty_df, None, empty_df, None


def get_stock_name(stock_code):
    stock_names = {
        "sh000001": "上证指数",
        "sh600000": "浦发银行",
        "sz000001": "平安银行"
    }
    if HKU_AVAILABLE:
        code = stock_code.strip()
        full_code = normalize_stock_code(code)
        stock = sm.get_stock(full_code)
        if stock is not None:
            try:
                if hasattr(stock, 'is_null') and stock.is_null():
                    return f"未找到股票: {full_code}"
            except Exception:
                pass
            return stock.name
        return f"未找到股票: {full_code}"
    else:
        return "（未连接Hikyuu）" + stock_names.get(stock_code, "未知股票")


def normalize_stock_code(code):
    code = code.strip().lower()
    if re.match(r'^\d{6}$', code):
        for prefix in ['sh', 'sz']:
            full_code = prefix + code
            if sm:
                stk = sm.get_stock(full_code)
                if stk is not None:
                    try:
                        if hasattr(stk, 'is_null') and stk.is_null():
                            continue
                    except Exception:
                        pass
                    return full_code
        return 'sh' + code
    elif re.match(r'^(sh|sz)\d{6}$', code):
        return code
    return code


def search_stocks(query):
    """搜索匹配的股票（支持代码和名称）
    - '600000' → 匹配代码 sh600000
    - '浦发' → 匹配名称包含"浦发"的股票
    - '平安银行' → 匹配名称完全等于或包含
    """
    if not HKU_AVAILABLE or not sm or not query:
        return []
    query = query.strip()
    query_lower = query.lower()
    results = []

    # 1. 精确代码匹配（6位数字）
    if re.match(r'^\d{6}$', query):
        for prefix in ['sh', 'sz']:
            full_code = prefix + query
            stock = sm.get_stock(full_code)
            if stock:
                results.append((full_code, stock.name))
                if len(results) >= 1:
                    return results[:10]  # 精确匹配直接返回

    # 2. 完整代码匹配（带前缀）
    if re.match(r'^(sh|sz)\d{6}$', query_lower):
        stock = sm.get_stock(query_lower)
        if stock:
            return [(query_lower, stock.name)]

    # 3. 名称搜索（支持中文）
    #    遍历所有股票，匹配名称包含关键词或代码包含关键词
    for stock in sm:
        try:
            market_code = stock.market_code.lower()  # 如 "sh600000"
            name = stock.name  # 如 "浦发银行"
            # 匹配条件：名称包含关键词 或 代码包含关键词
            if query in name or query_lower in market_code:
                results.append((market_code, name))
                if len(results) >= 20:
                    break
        except Exception:
            continue

    return results[:10]


def validate_stock(stock_code):
    if HKU_AVAILABLE:
        full_code = normalize_stock_code(stock_code)
        stock = sm.get_stock(full_code)
        if stock is None:
            return False, f"本地数据中未找到该股票: {full_code}，请先下载数据"
        try:
            if hasattr(stock, 'is_null') and stock.is_null():
                return False, f"本地数据中未找到该股票: {full_code}，请先下载数据"
        except Exception:
            pass
        return True, f"验证通过: {stock.name}"
    return True, "验证通过（Hikyuu未连接）"


def validate_params(fast_period, slow_period, stop_loss, buy_quantity):
    if fast_period >= slow_period:
        return False, "快线周期必须小于慢线周期"
    if not (0.01 <= stop_loss <= 0.2):
        return False, "止损比例应在1%-20%之间"
    if buy_quantity <= 0:
        return False, "买入数量必须大于0"
    return True, "参数验证通过"


def select_sh000001():
    return "000001", get_stock_name("sh000001")


def select_sh600000():
    return "600000", get_stock_name("sh600000")


def select_sz000001():
    return "000001", get_stock_name("sz000001")


with gr.Blocks(title="Hikyuu 策略回测可视化工具") as demo:
    gr.Markdown("# Hikyuu 策略回测可视化工具")

    hikyuu_status_md = gr.Markdown(get_hikyuu_status())

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 股票选择")

            with gr.Row():
                stock_code_input = gr.Textbox(
                    label="股票代码",
                    placeholder="输入6位数字或股票名称搜索",
                    value="600000",
                    interactive=True
                )
                stock_name_label = gr.Label(
                    value="浦发银行",
                    label="股票名称"
                )

            stock_search_btn = gr.Button("搜索股票", size="sm")
            stock_dropdown = gr.Dropdown(
                label="搜索结果",
                choices=[],
                interactive=True,
                visible=False
            )

            gr.Markdown("#### 常用股票")

            with gr.Row():
                sh000001_btn = gr.Button("上证指数", size="sm")
                sh600000_btn = gr.Button("浦发银行", size="sm")
                sz000001_btn = gr.Button("平安银行", size="sm")

            gr.Markdown("### 策略选择")

            strategy_select = gr.Dropdown(
                label="策略类型",
                choices=["双均线策略"],
                value="双均线策略"
            )

            gr.Markdown("### 策略参数")

            with gr.Row():
                fast_period_slider = gr.Slider(
                    minimum=5,
                    maximum=100,
                    value=10,
                    step=1,
                    label="快线周期"
                )
                fast_period_num = gr.Number(
                    value=10,
                    label="",
                    precision=0,
                    minimum=5,
                    maximum=100
                )

            with gr.Row():
                slow_period_slider = gr.Slider(
                    minimum=10,
                    maximum=200,
                    value=30,
                    step=1,
                    label="慢线周期"
                )
                slow_period_num = gr.Number(
                    value=30,
                    label="",
                    precision=0,
                    minimum=10,
                    maximum=200
                )

            with gr.Row():
                stop_loss_slider = gr.Slider(
                    minimum=0.01,
                    maximum=0.2,
                    value=0.05,
                    step=0.01,
                    label="止损比例"
                )
                stop_loss_num = gr.Number(
                    value=0.05,
                    label="",
                    precision=2,
                    minimum=0.01,
                    maximum=0.2
                )

            initial_capital = gr.Number(
                value=100000,
                label="初始资金",
                precision=0
            )

            buy_quantity = gr.Number(
                value=100,
                label="买入数量",
                precision=0
            )

            with gr.Row():
                backtest_days_slider = gr.Slider(
                    minimum=60,
                    maximum=1000,
                    value=500,
                    step=1,
                    label="回测天数"
                )
                backtest_days_num = gr.Number(
                    value=500,
                    label="",
                    precision=0,
                    minimum=60,
                    maximum=1000
                )

            run_btn = gr.Button("开始回测", variant="primary", size="lg")

        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.Tab("绩效概览"):
                    perf_md = gr.Markdown("## 绩效概览\n\n请点击\"开始回测\"按钮运行回测。")
                    perf_df = gr.Dataframe(label="绩效指标明细")

                with gr.Tab("K线图"):
                    kline_plot = gr.Plot(label="K线走势图")

                with gr.Tab("交易记录"):
                    trades_df = gr.Dataframe(label="交易明细")

                with gr.Tab("资金曲线"):
                    equity_plot = gr.Plot(label="资金曲线")

    fast_period_slider.change(lambda x: x, inputs=fast_period_slider, outputs=fast_period_num)
    fast_period_num.change(lambda x: x, inputs=fast_period_num, outputs=fast_period_slider)

    slow_period_slider.change(lambda x: x, inputs=slow_period_slider, outputs=slow_period_num)
    slow_period_num.change(lambda x: x, inputs=slow_period_num, outputs=slow_period_slider)

    stop_loss_slider.change(lambda x: x, inputs=stop_loss_slider, outputs=stop_loss_num)
    stop_loss_num.change(lambda x: x, inputs=stop_loss_num, outputs=stop_loss_slider)

    backtest_days_slider.change(lambda x: x, inputs=backtest_days_slider, outputs=backtest_days_num)
    backtest_days_num.change(lambda x: x, inputs=backtest_days_num, outputs=backtest_days_slider)

    stock_code_input.change(get_stock_name, inputs=stock_code_input, outputs=stock_name_label)

    def handle_search(query):
        results = search_stocks(query)
        if results:
            choices = [f"{code} - {name}" for code, name in results]
            return gr.update(visible=True, choices=choices, value=None)
        else:
            return gr.update(visible=False, choices=[], value=None)

    def handle_select_dropdown(selected):
        if selected:
            code = selected.split(" - ")[0]
            return code, get_stock_name(code)
        return "", ""

    stock_search_btn.click(handle_search, inputs=stock_code_input, outputs=stock_dropdown)
    stock_code_input.submit(handle_search, inputs=stock_code_input, outputs=stock_dropdown)
    stock_dropdown.change(handle_select_dropdown, inputs=stock_dropdown, outputs=[stock_code_input, stock_name_label])

    sh000001_btn.click(select_sh000001, outputs=[stock_code_input, stock_name_label])
    sh600000_btn.click(select_sh600000, outputs=[stock_code_input, stock_name_label])
    sz000001_btn.click(select_sz000001, outputs=[stock_code_input, stock_name_label])

    run_btn.click(
        run_backtest,
        inputs=[
            stock_code_input,
            strategy_select,
            fast_period_slider,
            slow_period_slider,
            stop_loss_slider,
            initial_capital,
            buy_quantity,
            backtest_days_slider
        ],
        outputs=[
            perf_md,
            perf_df,
            kline_plot,
            trades_df,
            equity_plot
        ]
    )


if __name__ == "__main__":
    demo.launch(inbrowser=True)
