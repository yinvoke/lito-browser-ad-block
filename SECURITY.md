# 安全策略

## 发布信任边界

- GitHub Actions 严格抓取全部上游，编译、校验并直接发布 `public/v1`；任一上游失败、过旧或规模异常时整次任务失败。
- `manifest.txt` 固定记录版本、文件长度和 SHA-256；构建后、提交前与 Pages 部署前都会复验。
- Lito 仅接受 HTTPS 地址，并在安装前再次核验版本、大小、文件集合和 SHA-256，同时拒绝版本回滚。
- 本项目不使用规则发布签名。信任边界是 GitHub 仓库、默认分支、Actions 工作流、GitHub Pages 与 HTTPS 传输。

## 报告问题

涉及工作流权限、规则供应链、发布完整性或版本回滚的问题，请使用 GitHub 仓库的 **Security → Report a vulnerability** 私密报告，不要在公开 issue 中附带敏感细节。
