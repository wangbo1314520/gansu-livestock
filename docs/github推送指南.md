# GitHub 推送指南（两项目）

> 前提：阶段 1-3 已完成（安全清理 + LICENSE/README + 本提交）。
> 本指南执行完"创建仓库"后，把两个远程 URL 告诉助手，由助手执行 remote add + push。

## 0. 检查 git 身份（如已配置可跳过）

```bash
git config --global user.name    # 应输出你的名字
git config --global user.email   # 应输出你的邮箱
```

未配置则：
```bash
git config --global user.name "你的名字"
git config --global user.email "you@example.com"
```

## 1. 方案 A：gh CLI（命令行直接创建，推荐）

先确认已安装：`where gh`。未安装可 `winget install GitHub.cli` 后 `gh auth login`。

### gansu-livestock（公开仓库）

```bash
cd /d E:\Program\gansu-livestock
gh repo create gansu-livestock --public --description "甘肃牛羊价格统计预测与趋势分析平台（Flask+Vue3+ARIMAX，毕业设计）"
```

### gansu-home（私有仓库）

```bash
cd /d E:\Program\gansu-home
gh repo create gansu-home --private --description "我家牛羊行情：家庭牧场家用版（私有）"
```

创建成功后 gh 会输出 HTTPS/SSH 地址，把它们分别交给助手执行推送，或自己执行第 3 节命令。

## 2. 方案 B：网页创建（无 gh 时）

1. 浏览器登录 https://github.com/new
2. **gansu-livestock**：Repository name 填 `gansu-livestock`，选 **Public**，
   Description 填 `甘肃牛羊价格统计预测与趋势分析平台（Flask+Vue3+ARIMAX，毕业设计）`
   ——**不要**勾选 Add README/.gitignore/license（本地已有）
3. **gansu-home**：Repository name 填 `gansu-home`，选 **Private**，其余同上
4. 创建后复制各自地址（形如 `https://github.com/<用户名>/<仓库名>.git`）

## 3. 推送（拿到 URL 后执行，或交助手执行）

```bash
# gansu-livestock
cd /d E:\Program\gansu-livestock
git remote add origin https://github.com/<用户名>/gansu-livestock.git
git branch -M main
git push -u origin main

# gansu-home
cd /d E:\Program\gansu-home
git remote add origin https://github.com/<用户名>/gansu-home.git
git branch -M main
git push -u origin main
```

> 首次推送会弹浏览器授权（或要求 Personal Access Token），按提示登录即可。
> gansu-home 推送内容已不含家庭数据文件（snapshot 已停跟踪、密码文档已忽略），
> 但历史中仍有已作废的旧 MySQL 密码（root 密码已于 2026-10-12 更换）——仓库保持 Private 即可。

## 4. 推送后自检

- [ ] 两仓库 GitHub 页面 README 渲染正常（mermaid 架构图可见）
- [ ] gansu-livestock 显示 MIT License
- [ ] gansu-home 仓库锁标志（Private）存在
- [ ] 仓库内搜 `DB_PASSWORD=` 无真实密码命中（应只剩占位符）
