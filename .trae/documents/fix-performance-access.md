# 修复 Hikyuu Performance 访问错误

## 当前状态
- Hikyuu GUI 工具可以启动，能识别到 "浦发银行"
- 但点击 "开始回测" 报错：`'hikyuu.cpp.core311.Performance' object has no attribute 'get'`
- 错误位置：app.py 第 237-238 行的 `get_perf()` 函数，使用了 `performance.get(key)`，但 Performance 是 C++ 对象，没有 `.get()` 方法

## 问题分析
- `sys.tm.get_performance()` 返回的是 C++ 层的 `Performance` 对象
- 该对象**不是 Python 字典**，不支持 `.get()` 方法
- 该对象实际支持的访问方式：
  1. `performance.names()` - 返回所有指标名（list of str）
  2. `performance.values()` - 返回所有指标值（list of float）
  3. `performance.to_df()` - 直接转成 DataFrame（最简单）
  4. `getattr(performance, name)` - 按属性名访问
  5. `performance[name]` - 按索引访问

## 修复方案
**采用 Hikyuu 官方提供的 `to_df()` 方法**，最简单稳定。

### 具体改动
**文件**：`/workspace/backtest_gui/app.py`
**位置**：第 236 行附近（`run_backtest` 函数内）

#### 改前（错误代码）
```python
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
```

#### 改后（正确代码）
```python
# 用 Hikyuu 提供的 to_df() 方法
perf_df_raw = sys.tm.get_performance().to_df()
# 转成字典方便用 key 访问
perf_dict = dict(zip(perf_df_raw['name'], perf_df_raw['value']))

def get_perf(key, default="--"):
    return perf_dict.get(key, default)
```

## 验证步骤
1. 双击 `start_fixed.bat` 启动
2. 在网页输入 `600000`（浦发银行）
3. 点击 "开始回测"
4. 期望结果：
   - 不再报错
   - 绩效概览标签页显示 8 项指标
   - K线图、交易记录、资金曲线三个标签页都有内容

## 风险评估
- 低风险：`to_df()` 是 Hikyuu 官方 API
- 兼容性好：之前在 Jupyter 中已经验证过 `get_performance()` 能用，`to_df()` 是更简单的封装
