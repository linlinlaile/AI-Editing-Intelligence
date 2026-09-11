# ADR-0003：Semantic Timeline 的事实/判断分层

- 状态：Accepted
- 日期：2026-09-11

## 背景

“人物向左移动”是描述性观察；“适合接在当前镜头后面”是带剪辑目标的判断。两者更新频率、证据、评估方法和失效方式不同，混在一个字段中会让模型替换和重新排序变得困难。

## 决策

使用三层关系：

1. `HierarchyLink`：时间层级和归属。
2. `DescriptiveObservation` / `ObservedRelation`：带 evidence、confidence、coverage 和 producer 的观察或推断。
3. `EditorialAssessment`：带 current shot、candidate shot、edit intent、ranker revision 和分项评分的编辑判断。

`good_next_shot` 只属于第三层，不能作为无上下文的永久事实。

## 后果

- 任何编辑推荐都可重算、解释和比较。
- 需要分别评估观测准确性和推荐质量。
- UI 不能把模型自报置信度直接展示为确定事实。
