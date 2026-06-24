# Hikyuu 策略回测可视化GUI - 实现计划

## [x] Task 1: 搭建Gradio基础框架与界面布局
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - 创建Gradio应用主文件
  - 设计三栏布局：左侧参数配置区、右侧结果展示区
  - 包含股票选择、策略选择、参数设置、回测按钮
  - 结果区包含绩效指标、K线图、交易记录三个标签页
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-1.1: 应用可通过 `python app.py` 正常启动
  - `human-judgement` TR-1.2: 界面布局清晰，操作区域分明，字体大小适中
- **Notes**: 使用Gradio Blocks API构建自定义布局

## [x] Task 2: 股票选择与验证功能
- **Priority**: high
- **Depends On**: Task 1
- **Description**: 
  - 实现股票代码输入框，支持sh/sz开头的代码格式
  - 验证股票是否存在于本地数据中
  - 显示股票名称和基本信息
  - 提供常用股票快捷选择（如上证指数、平安银行等）
- **Acceptance Criteria Addressed**: AC-2, AC-8
- **Test Requirements**:
  - `programmatic` TR-2.1: 输入sh600000能正确返回"浦发银行"
  - `programmatic` TR-2.2: 输入无效代码显示友好错误提示
  - `human-judgement` TR-2.3: 错误提示清晰易懂，不使用技术术语
- **Notes**: 调用Hikyuu的sm.get_stock()接口

## [x] Task 3: 内置策略库与参数配置
- **Priority**: high
- **Depends On**: Task 1
- **Description**: 
  - 实现策略下拉选择框，首期包含：双均线策略
  - 根据选择的策略动态显示对应参数配置项
  - 双均线策略参数：快线周期、慢线周期、止损比例、初始资金、买入数量
  - 参数使用滑块+数字输入框双模式
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-3.1: 选择"双均线策略"后显示对应参数
  - `programmatic` TR-3.2: 参数值可通过滑块和输入框双向调整
  - `human-judgement` TR-3.3: 参数说明通俗易懂，有默认值
- **Notes**: 预留扩展接口，方便后续添加更多策略

## [x] Task 4: 回测引擎封装
- **Priority**: high
- **Depends On**: Task 2, Task 3
- **Description**: 
  - 封装回测执行函数，接收股票代码、策略类型、参数字典
  - 内部调用Hikyuu的SYS_Simple、SG_Flex、MM_FixedCount、ST_FixedPercent等组件
  - 返回绩效对象、交易记录列表、K线数据
  - 添加错误捕获和异常处理
- **Acceptance Criteria Addressed**: AC-4, AC-8
- **Test Requirements**:
  - `programmatic` TR-4.1: 输入有效参数能成功执行回测并返回结果
  - `programmatic` TR-4.2: 参数错误时返回友好错误信息
  - `programmatic` TR-4.3: 回测结果包含performance、trades、kdata
- **Notes**: 回测周期默认最近2年日线数据

## [x] Task 5: 绩效指标展示
- **Priority**: high
- **Depends On**: Task 4
- **Description**: 
  - 从Hikyuu Performance对象提取关键指标
  - 用卡片式布局展示核心指标：总收益率、年化收益率、胜率、最大回撤、交易次数、盈亏比
  - 指标名称使用通俗中文（如"赚了多少"、"成功率"、"最大亏损"）
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `programmatic` TR-5.1: 回测后正确显示6项以上关键指标
  - `programmatic` TR-5.2: 指标数值与Hikyuu内置计算一致
  - `human-judgement` TR-5.3: 指标名称易懂，数值格式清晰（百分比、金额）
- **Notes**: 重点指标用颜色区分（盈利红色，亏损绿色）

## [x] Task 6: K线图与买卖点可视化
- **Priority**: high
- **Depends On**: Task 4
- **Description**: 
  - 使用matplotlib绘制K线图
  - 在K线上叠加均线（快线、慢线）
  - 用向上箭头标记买入点，向下箭头标记卖出点
  - 支持缩放和平移（通过matplotlib工具栏）
- **Acceptance Criteria Addressed**: AC-6
- **Test Requirements**:
  - `programmatic` TR-6.1: K线图能正常生成并显示
  - `human-judgement` TR-6.2: 买卖点标记清晰可辨，颜色区分明显
  - `human-judgement` TR-6.3: 均线与K线叠加正确
- **Notes**: 使用mplfinance或自定义matplotlib绘图

## [x] Task 7: 交易记录表格
- **Priority**: medium
- **Depends On**: Task 4
- **Description**: 
  - 从TradeManager获取交易记录
  - 表格展示：交易日期、买卖方向、价格、数量、金额、盈亏
  - 按日期倒序排列
  - 支持滚动查看
- **Acceptance Criteria Addressed**: AC-7
- **Test Requirements**:
  - `programmatic` TR-7.1: 表格展示所有交易记录，数据准确
  - `programmatic` TR-7.2: 按日期倒序排列
  - `human-judgement` TR-7.3: 表格样式清晰，盈亏用颜色区分
- **Notes**: 使用pandas DataFrame格式输出

## [x] Task 8: 资金曲线图
- **Priority**: medium
- **Depends On**: Task 4
- **Description**: 
  - 绘制账户净值变化曲线
  - 标注初始资金线
  - 标注最高/最低点
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `programmatic` TR-8.1: 资金曲线能正确生成
  - `human-judgement` TR-8.2: 曲线走势与交易记录对应
- **Notes**: 从TradeManager的资金记录提取数据

## [x] Task 9: 启动脚本与使用说明
- **Priority**: medium
- **Depends On**: Task 1-8
- **Description**: 
  - 创建一键启动脚本（Windows .bat文件）
  - 启动时自动打开浏览器
  - 提供简单的使用说明
  - 依赖检查和自动安装提示
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-9.1: 双击启动脚本能正常启动应用
  - `human-judgement` TR-9.2: 使用说明清晰易懂，步骤明确
- **Notes**: 启动脚本包含环境检查
