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
        Query, Datetime
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
    sm = StockManager.instance()

    from hikyuu import load_hikyuu
    load_hikyuu(
        stock_list=["all"],
        ktype_list=["day"],
        load_history_finance=False,
        load_weight=False,
        start_spot=False
    )

    HKU_AVAILABLE = True
except Exception as e:
    HKU_AVAILABLE = False
    HKU_ERROR = repr(e)
    sm = None


def get_hikyuu_status():
    if HKU_AVAILABLE:
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

        my_tm = crtTM(init_cash=initial_capital, cost_func=TC_FixedA2017())
        my_sg = SG_Flex(EMA(CLOSE(), n=fast_period), slow_n=slow_period)
        my_mm = MM_FixedCount(buy_quantity)
        my_st = ST_FixedPercent(stop_loss)
        sys = SYS_Simple(tm=my_tm, sg=my_sg, mm=my_mm, st=my_st)

        full_code = normalize_stock_code(stock_code)
        stk = sm[full_code]
        sys.run(stk, Query(-backtest_days))

        performance = sys.tm.get_performance()

        def get_perf(key, default="--"):
            return performance.get(key, default)

        total_return = get_perf("未平仓帐户收益率%", "--")
        annual_return = get_perf("年化收益率%", "--")
        max_drawdown = get_perf("最大回撤%", "--")
        win_rate = get_perf("赢利交易比例%", "--")
        profit_loss_ratio = get_perf("平均赢利/平均亏损比例", "--")
        total_trades = get_perf("交易总数", "--")
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

        trades = sys.tm.get_trade_list()
        trade_data = []
        for trade in trades:
            datetime_str = trade.datetime.strftime("%Y-%m-%d")
            price = trade.price
            num = trade.number
            amount = abs(price * num)
            direction = "买入" if num > 0 else "卖出"
            profit = trade.profit
            trade_data.append({
                "日期": datetime_str,
                "方向": direction,
                "价格": round(price, 2),
                "数量": abs(int(num)),
                "金额": round(amount, 2),
                "盈亏": round(profit, 2)
            })

        trades_df = pd.DataFrame(trade_data)
        if not trades_df.empty:
            trades_df = trades_df.sort_values(by="日期", ascending=False).reset_index(drop=True)

        kdata = stk.get_kdata(Query(-backtest_days))
        kline_data = []
        for k in kdata:
            kline_data.append({
                "日期": k.datetime.strftime("%Y-%m-%d"),
                "开盘": round(k.open, 2),
                "最高": round(k.high, 2),
                "最低": round(k.low, 2),
                "收盘": round(k.close, 2),
                "成交量": k.volume
            })
        kline_df = pd.DataFrame(kline_data)

        equity_data = []
        for i in range(len(sys.tm)):
            rec = sys.tm[i]
            equity_data.append({
                "日期": rec.datetime.strftime("%Y-%m-%d"),
                "现金": round(rec.cash, 2),
                "市值": round(rec.market_value, 2),
                "总资产": round(rec.asset, 2)
            })
        equity_df = pd.DataFrame(equity_data)

        kline_fig = plot_kline(kline_df, trades_df, fast_period, slow_period)
        equity_fig = plot_equity(equity_df, initial_capital)

        return perf_md, perf_df, kline_fig, trades_df, equity_fig

    except Exception as e:
        error_md = f'<span style="color:red">**错误：回测执行失败 - {str(e)}**</span>'
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
        if stock:
            return stock.name
        return f"未找到股票: {full_code}"
    else:
        return "（未连接Hikyuu）" + stock_names.get(stock_code, "未知股票")


def normalize_stock_code(code):
    code = code.strip().lower()
    if re.match(r'^\d{6}$', code):
        for prefix in ['sh', 'sz']:
            full_code = prefix + code
            if sm and sm.get_stock(full_code):
                return full_code
        return 'sh' + code
    elif re.match(r'^(sh|sz)\d{6}$', code):
        return code
    return code


def search_stocks(query):
    """搜索匹配的股票"""
    if not HKU_AVAILABLE or not sm or not query:
        return []
    query = query.strip().lower()
    results = []
    if re.match(r'^\d{6}$', query):
        for prefix in ['sh', 'sz']:
            full_code = prefix + query
            stock = sm.get_stock(full_code)
            if stock:
                results.append((full_code, stock.name))
    elif re.match(r'^(sh|sz)\d{6}$', query):
        stock = sm.get_stock(query)
        if stock:
            results.append((query, stock.name))
    else:
        for stock in sm:
            code = stock.code
            name = stock.name
            if query in code.lower() or query in name:
                results.append((code, name))
                if len(results) >= 10:
                    break
    return results


def validate_stock(stock_code):
    if HKU_AVAILABLE:
        full_code = normalize_stock_code(stock_code)
        stock = sm.get_stock(full_code)
        if not stock:
            return False, f"本地数据中未找到该股票: {full_code}，请先下载数据"
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
