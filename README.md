# LeetCode Hot 100 → 200（C++17）

一个适合和 Codex/AI 结对使用的刷题仓库：先独立思考，卡住时逐级要提示，明确说“不会”或“看答案”后才展示完整 C++17 解法与讲解。每题的尝试、答案、笔记和完成时间都保存在 Git 历史里。

<!-- PROGRESS:START -->
## 进度

- 目标：200 题
- 已完成：0 / 200（0.0%）
- 进行中：0
- 待完成：0

| # | 题目 | 难度 | 状态 | 完成日期 | 用时 | 复习日 |
|---:|---|---|---|---|---:|---|
| - | 还没有题目。运行 `python scripts/leet.py new ...` 添加第一题。 | - | - | - | - | - |
<!-- PROGRESS:END -->

## 日常使用

在仓库中打开 Codex，然后直接说：

- `开始下一题`：进入下一道未完成题，不提前给答案。
- `提示` / `再提示`：按层级给方向、关键观察或伪代码。
- `不会，给我答案`：写出完整 C++17 解法，并讲清思路、正确性、复杂度、易错点。
- `我写好了，帮我检查`：编译测试、代码审查并更新记录。
- `今天结束，帮我同步`：更新进度并提交、推送到 GitHub。

仓库根目录的 `AGENTS.md` 定义了完整的结对规则，所以每次不必重复说明要求。

## 命令行

```powershell
# 新增题目
python scripts/leet.py new 1 two-sum "两数之和" Easy --url https://leetcode.cn/problems/two-sum/

# 开始、检查、完成
python scripts/leet.py start 1
python scripts/leet.py check 1
python scripts/leet.py done 1 --minutes 25 --review-days 1,3,7,14,30

# 查看下一题/统计/同步 GitHub
python scripts/leet.py next
python scripts/leet.py stats
python scripts/leet.py sync "solve: #1 two-sum"
```

每题目录包含：

```text
problems/0001-two-sum/
├── problem.json   # 题号、状态、日期等机器可读记录
├── attempt.md     # 自己的思路、失败尝试、卡点
├── solution.cpp   # LeetCode 提交代码
├── test.cpp       # 本地测试入口
└── notes.md       # 完整讲解、复杂度、错因、复习记录
```

## 本机位置与 GitHub

本仓库位于：

```text
/Users/jiaqiguo/Documents/leetcode-hot100-200
```

首次版本已经初始化为 Git 仓库。连接 GitHub 后，每完成一道题运行下面的命令即可记录并推送：

```bash
python3 scripts/leet.py sync "solve: 题号 题名"
```

## 目录约定

- `progress.json`：总进度数据库；不要手工改统计数字，使用脚本更新。
- `problems/`：每题一个目录，保留自己的尝试与最终解法。
- `templates/`：新题模板。
- `.github/workflows/validate.yml`：每次推送自动校验数据并编译有测试入口的题目。
- `PROMPTS.md`：可直接复制给 AI 的常用指令。

题目原文不复制进仓库，只保存链接和个人总结，便于保持仓库简洁。
