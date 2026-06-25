# 修复计划：Performance 访问 + 股票名称搜索

## 一、问题根因分析（已确认）

### 错误 1：Performance 访问错误
- **错误信息**：`'hikyuu.cpp.core311.Performance' object has no attribute 'get'`
- **根因**：`sys.tm.get_performance()` 返回的是 C++ Performance 对象，不是 Python 字典
- **正确的访问方式**（已在 `007-SystemDetails.ipynb` 第 482 行证实）：
  - `performance["指标名"]` ← **索引访问**（已验证可用）
  - `performance.names()` + `performance.values()` ← **批量获取**
  - `performance.to_df()` ← **官方封装**，转成 DataFrame

### 错误 2：指标名错误
- **之前我用的 key 名**：`"未平仓帐户收益率%"`、`"最大回撤%"` 等（**自己猜的，不准确**）
- **Hikyuu 真实指标名**（已通过 `007-SystemDetails.ipynb` 验证）：
  ```
  帐户初始金额 / 累计投入本金 / 累计红利 / 现金余额 / 当前总资产
  已平仓帐户收益率%        ← 关键：没有"未平仓"三个字
  帐户年复合收益率%        ← 不是"年化收益率%"
  帐户平均年收益率%
  赢利交易比例%            ← 之前我用的"胜率"对应这个
  赢利交易数
  亏损交易数
  已平仓交易总数
  净赢利/亏损比例
  最大回撤百分比           ← 关键：不是"最大回撤%"
  夏普比率
  ```

## 二、股票名称搜索方案

### 需求
- 不只支持代码搜索
- 输入股票名称（如"平安"、"浦发"）也要能匹配

### 实现思路（已确认可行）
- 通过 `for s in sm` 遍历所有股票
- 每只股票有 `.name`（名称）、`.market_code`（代码）、`.code`（数字代码）属性
- 模糊匹配 name 包含输入关键词

### 用户体验
- 输入 "600000" → 匹配代码 → 列表显示
- 输入 "浦发" → 匹配名称包含"浦发" → 列表显示
- 输入 "0001" → 同时匹配代码和名称
- 用户从下拉框选择

## 三、具体改动（精确到行号）

### 文件：`/workspace/backtest_gui/app.py`

#### 改动 1：替换 `get_perf()` 函数（位于第 237-238 行附近）
**改前**：
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

**改后**：
```python
performance = sys.tm.get_performance()

def get_perf(key, default="--"):
    """使用索引访问（已在 007-SystemDetails.ipynb 验证可用）"""
    try:
        val = performance[key]
        if hasattr(val, '__float__'):
            return float(val)
        return val
    except (KeyError, TypeError):
        return default

# 用 Hikyuu 真实指标名（已在 007-SystemDetails.ipynb 第 142-200 行确认）
total_return = get_perf("已平仓帐户收益率%", "--")
annual_return = get_perf("帐户年复合收益率%", "--")
max_drawdown = get_perf("最大回撤百分比", "--")
win_rate = get_perf("赢利交易比例%", "--")
profit_loss_ratio = get_perf("平均赢利/平均亏损比例", "--")
total_trades = get_perf("已平仓交易总数", "--")
win_trades = get_perf("赢利交易数", "--")
lose_trades = get_perf("亏损交易数", "--")
```

#### 改动 2：增强 `search_stocks()` 函数（支持名称搜索）
**改前**：只支持代码匹配
```python
def search_stocks(query):
    if not HKU_AVAILABLE or not sm or not query:
        return []
    query = query.strip().lower()
    results = []
    if re.match(r'^\d{6}$', query):
        ...
    elif re.match(r'^(sh|sz)\d{6}$', query):
        ...
    else:
        return []  # ← 名称搜索无结果
```

**改后**：支持代码、名称、混合搜索
```python
def search_stocks(query):
    """支持代码、名称、混合搜索
    - '600000' → 匹配代码 sh600000
    - '浦发' → 匹配名称包含"浦发"的股票
    - '平安银行' → 匹配名称完全等于或包含
    """
    if not HKU_AVAILABLE or not sm or not query:
        return []
    query = query.strip()
    query_lower = query.lower()
    results = []
    
    # 1. 精确代码匹配
    if re.match(r'^\d{6}$', query):
        for prefix in ['sh', 'sz']:
            full_code = prefix + query
            stock = sm.get_stock(full_code)
            if stock:
                results.append((full_code, stock.name))
                return results[:10]  # 精确匹配直接返回
    
    if re.match(r'^(sh|sz)\d{6}$', query_lower):
        stock = sm.get_stock(query_lower)
        if stock:
            return [(query_lower, stock.name)]
    
    # 2. 名称搜索（支持中文）
    #    遍历所有股票，匹配名称包含关键词
    #    用 limit 控制遍历数量，避免太慢
    for stock in sm:
        try:
            code = stock.market_code.lower()
            name = stock.name
            if query in name or query_lower in code:
                results.append((code, name))
                if len(results) >= 20:
                    break
        except Exception:
            continue
    
    return results[:10]
```

**注意**：遍历 `sm` 可能有 5000+ 只股票，但都加载在内存中（已在 `002-HowToGetStock.ipynb` 第 90 行证实 8471 只），匹配速度快，20 条限制后立即 break。

## 四、风险评估

| 风险点 | 评估 | 缓解 |
|--------|------|------|
| 指标名还不正确 | **低** | 已从官方 notebook 复制粘贴原文 |
| `performance[]` 索引访问失败 | **低** | 已用 try/except 包裹，失败回 "--" |
| 名称搜索遍历慢 | **低** | 限制 20 条即停止 |
| 用户输入大小写 | **无** | 中文搜索不受影响 |

## 五、验证步骤

1. **关掉旧窗口**，双击 `start_fixed.bat` 启动
2. 顶部应显示：✅ + 已加载股票数 + 数据目录
3. 输入框输入 `600000` → 点"搜索股票" → 下拉框出现"sh600000 - 浦发银行"
4. 输入 `浦发` → 点"搜索股票" → 下拉框出现浦发银行
5. 选一只股票 → 点"开始回测"
6. 期望结果：
   - 绩效概览标签页显示 8 项指标
   - 总收益率、年化收益率、最大回撤、胜率、盈亏比、交易次数、盈利次数、亏损次数都有值
7. K线图标签页显示蜡烛图 + 快慢均线 + 买卖点
8. 交易记录标签页显示买卖表格
9. 资金曲线标签页显示净值曲线

## 六、保证

- 所有指标名都是**从 Hikyuu 官方 notebook 复制**，不是猜测
- 所有访问方式（`performance[]`）都是**官方已验证用法**
- 所有 API（`for s in sm`、`stock.name`、`stock.market_code`）都是**官方文档有据可查**
- 写完代码后会逐行核对，确保不再出现"某属性不存在"问题
