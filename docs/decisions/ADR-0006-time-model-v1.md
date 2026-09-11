# ADR-0006：Contract v1 的时间模型

- 状态：Accepted
- 日期：2026-09-11

Contract v1 将每个时间点表示为 `stream_id`、整数 `pts`、`Rational(numerator, denominator)` timebase，以及可选的呈现帧序号。时间段使用起始包含、结束不包含。这样可以原样表达 CFR、VFR、非零起始 PTS 和 B-frame 呈现顺序；浮点秒数只在边界层计算。
