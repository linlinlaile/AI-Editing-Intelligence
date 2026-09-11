# ADR-0002：PTS 和 rational timebase 是时间真值

- 状态：Accepted
- 日期：2026-09-11

## 背景

素材可能是 VFR，可能有非零起始 PTS、B-frame、旋转或复杂容器时间信息。仅保存 float seconds 或 nominal FPS 会产生边界漂移，无法支撑未来的 frame-accurate 导出。

## 决策

所有 canonical 时间使用源 stream 的整数 PTS、rational timebase、stream ID 和可选的 presentation frame index。`TimeSpan` 使用 start-inclusive/end-exclusive。float seconds 只用于展示和查询输入。

## 后果

- ingest、Shot boundary、Sample、Evidence 和未来导出共享同一时间语义。
- 必须测试 CFR、VFR、非零起点和呈现顺序。
- 代理视频或转码必须显式保存 source 映射。
- 外部工具的秒数时间码只能作为边界适配层，不能覆盖源 PTS。
