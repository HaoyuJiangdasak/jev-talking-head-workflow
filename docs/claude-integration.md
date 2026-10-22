# Claude Code integration

Claude Code 的 skill 搜索目录是 `%USERPROFILE%\.claude\skills\`。本仓库提供四个轻量入口：

```text
integrations/claude/jev-video-review
integrations/claude/lead-media-edit-bridge
integrations/claude/lead-media-script-bridge
integrations/claude/full-video-motion-workflow-bridge
```

Claude 侧不需要复制 MCP server 配置。已有 `/jev` skill 提供 Jev 1.14 工具；新入口只规定什么时候调用它以及如何把结果送回口播工作流。

推荐的 Claude 调用顺序：

1. `/lead-media-edit` 完成 A-roll transcript 和人工复听的候选 take。
2. `/jev-video-review` 或 `/jev` 的 `jev_decide` 比较候选 take。
3. 人工确认 EDL 后重新生成最终 transcript。
4. 使用 `jev_classify` 和 `jev_decide` 给语义段分配 `viewer_job`、`full/stage/pip` 和重点词。
5. 继续 Motion Graphics、字幕和 viewer QA。

如果 Claude 使用 ChatCut 的云转录，Jev 只消费 ChatCut 已接受的文字和时间；不要在同一条任务里再启动第二套 ASR。低置信度结果必须保留为人工复核。
