# Claude Code 调用说明

Claude Code 用户级 Skill 目录是：

```text
%USERPROFILE%\.claude\skills\
```

复制 `skills/center-stage-talking-head`、`skills/lead-media-edit`、`skills/full-video-motion-workflow`、`skills/jev-video-review` 和 `skills/connect-chatcut-desktop` 到该目录后，新建会话并检查 Skill 清单。

## 直接调用

```text
/center-stage-talking-head
```

任务提示建议写清楚：

```text
使用 center-stage-talking-head + lead-media-edit 制作这条真人口播。
人物保持在中央；按 transcript_rough.json 的语义节点同步出现卡片、截图、数字、步骤和 callout。
复杂 UI 段落切 pip；保留原始人声和字幕；完成 Remotion/FFmpeg 合成、SRT/ASS 和 QA。
ChatCut MCP 如果不是 Connected，就执行本地渲染路线，不要虚构 ChatCut 工具调用。
```

## 与 ChatCut 的关系

`connect-chatcut-desktop` 只记录官方安装、登录、连接和回退规则，不包含 MCP server 和账号配置。Claude Code 只有在 `claude mcp list` 显示 `chatcut_desktop` 为 Connected 时，才可以使用 ChatCut 项目读写工具。

## 与其他 Skill 的关系

这个仓库使用用户级共享 Skill。`embedded-captions`、`talking-head-recut`、HyperFrames 和 `lead-media-edit` 可以同时保留；路由由任务类型决定，不需要隔离或禁用其他 Skill。

