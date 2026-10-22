# Security

这个仓库只包含工作流说明、skill 文件和本地适配脚本，不应包含任何凭据或用户媒体。

请通过环境变量配置 Jev 或其他 provider 的 key，例如 `JEV_API_KEY`。不要把完整 key 粘贴到 issue、日志、截图、review JSON 或 commit message 中。

如果发现意外提交的秘密：

1. 立即撤销并轮换对应 key。
2. 不要只删除工作树文件；从 Git history 中移除并重新检查所有 refs。
3. 在公开 issue 中只描述影响范围，不要贴出秘密本身。

报告安全问题时，请通过私下渠道联系仓库维护者，不要先公开发布可利用的凭据或用户内容。
