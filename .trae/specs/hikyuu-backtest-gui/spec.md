# Hikyuu 策略回测可视化GUI - 产品需求文档

## Overview
- **Summary**: 基于Gradio构建的Hikyuu量化回测可视化界面，让无编程基础用户通过网页界面完成策略回测、参数调整、结果查看全流程操作。
- **Purpose**: 解决用户因缺乏编程基础，无法通过代码运行回测、检验结果、反馈优化策略的痛点，提供"傻瓜式操作界面，降低量化研究门槛。
- **Target Users**: 无Python编程基础的量化研究爱好者、投资者

## Goals
- 用户无需编写任何代码，通过点击、下拉框、滑块等GUI组件完成策略回测
- 支持内置策略参数调整，实时查看回测结果
- 可视化展示K线图、交易点、绩效指标
- 低内存占用，避免因内存不足导致系统蓝屏
- 与现有Hikyuu数据无缝对接

## Non-Goals (Out of Scope)
- 不提供实盘交易功能
- 不提供策略编写IDE/代码编辑器
- 不实现复杂的多因子/组合回测
- 不替代现有HikyuuTDX数据管理功能
- 不提供移动端适配（仅桌面浏览器

## Background & Context
- 用户已安装Hikyuu并下载了历史数据
- 用户电脑配置不高，之前使用Streamlit出现蓝屏
- 用户无Python编程基础，需要纯GUI操作
- Hikyuu已有完整的策略组件体系（SG/ST/MM/PG等）
- 已验证双均线策略可在Jupyter中正常运行

## Functional Requirements
- **FR-1**: 股票选择 - 通过股票代码或名称搜索选择回测标的
- **FR-2**: 策略选择 - 下拉选择内置策略（双均线、海龟等）
- **FR-3**: 参数设置 - 通过滑块/输入框调整策略参数（均线周期、止损比例等）
- **FR-4**: 回测执行 - 点击按钮执行回测，显示进度
- **FR-5**: 绩效展示 - 表格展示收益率、胜率、最大回撤等关键指标
- **FR-6**: K线图表 - 可视化K线图叠加买卖点标记
- **FR-7**: 交易记录 - 表格展示详细买卖记录
- **FR-8**: 资金曲线 - 展示账户净值变化曲线

## Non-Functional Requirements
- **NFR-1**: 轻量级 - 内存占用低于500MB，避免蓝屏
- **NFR-2**: 响应快 - 单只股票回测（日线252天）应在5秒内完成
- **NFR-3**: 易启动 - 单命令启动，浏览器自动打开
- **NFR-4**: 稳定性 - 不会因参数错误崩溃，有友好错误提示

## Constraints
- **技术栈**: Python + Gradio + Matplotlib/Plotly
- **依赖**: Hikyuu、gradio、pandas、matplotlib
- **平台**: Windows（用户当前环境
- **数据**: 使用用户已有的Hikyuu本地数据

## Assumptions
- 用户已正确安装Hikyuu并下载了日线数据
- 用户使用默认Hikyuu配置（HDF5存储
- 用户电脑至少有4GB以上内存
- 用户使用Chrome/Edge浏览器

## Acceptance Criteria

### AC-1: 启动界面
- **Given**: 用户已安装Hikyuu和Gradio
- **When**: 用户运行启动命令
- **Then**: 浏览器自动打开GUI界面，显示股票选择、策略选择、参数设置区域
- **Verification**: `human-judgment`
- **Notes**: 界面布局清晰，操作区域分明

### AC-2: 股票搜索与选择
- **Given**: GUI界面已打开
- **When**: 用户输入股票代码（如sh600000）
- **Then**: 系统正确识别股票并显示名称
- **Verification**: `programmatic`
- **Notes**: 支持沪市/深市代码格式

### AC-3: 策略选择与参数配置
- **Given**: GUI界面已打开
- **When**: 用户选择"双均线策略"，调整快线/慢线周期
- **Then**: 参数滑块实时响应，参数值显示正确
- **Verification**: `human-judgment`
- **Notes**: 参数有合理范围限制

### AC-4: 回测执行
- **Given**: 已选择股票和策略，参数已设置
- **When**: 用户点击"开始回测"按钮
- **Then**: 显示回测进度，完成后展示结果
- **Verification**: `programmatic`
- **Notes**: 回测过程中界面不卡死

### AC-5: 绩效指标展示
- **Given**: 回测完成
- **When**: 查看绩效区域
- **Then**: 显示收益率、胜率、最大回撤、交易次数等关键指标
- **Verification**: `programmatic`
- **Notes**: 指标名称通俗易懂

### AC-6: K线图与买卖点
- **Given**: 回测完成
- **When**: 查看图表区域
- **Then**: 显示K线图，买入点用箭头标记，卖出点用另一种箭头标记
- **Verification**: `human-judgment`
- **Notes**: 图表清晰可辨

### AC-7: 交易记录表格
- **Given**: 回测完成
- **When**: 查看交易记录
- **Then**: 表格展示每笔交易的日期、价格、数量、盈亏
- **Verification**: `programmatic`
- **Notes**: 按时间排序

### AC-8: 错误处理
- **Given**: 用户输入无效股票代码或参数
- **When**: 点击回测
- **Then**: 显示友好的错误提示，不崩溃
- **Verification**: `programmatic`
- **Notes**: 提示信息清晰易懂

## Open Questions
- [ ] 用户需要哪些内置策略？（先从双均线开始）
- [ ] 是否需要参数优化功能？
- [ ] 是否需要多股票对比功能？
- [ ] 数据来源是否需要支持多周期？
