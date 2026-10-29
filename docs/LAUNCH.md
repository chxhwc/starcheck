# Launch notes

This is the distribution half of `starcheck` — the part that has nothing to do
with code. It is written as a runbook, not a blog post, because the same file
gets reused for the next project.

The whole thesis in one line:

> **stars ≈ exposure × first-screen conversion × reuse frequency**
> `starcheck` measures the middle term. This document is about the first one.

---

## 0. Before anything: the 10-item go-live checklist

Nothing below matters until these are true. All of them are `gh` one-liners.

```bash
gh repo create chxhwc/starcheck --public --source=. --remote=origin --push

# description = the pitch, 160 chars max, no buzzwords
gh repo edit --description "Audit any repo for star-readiness: 28 checks, one score, copy-paste fixes."

# topics = the search surface. 10+, lowercase, hyphenated
gh repo edit \
  --add-topic cli --add-topic developer-tools --add-topic github \
  --add-topic readme --add-topic opensource --add-topic python \
  --add-topic static-analysis --add-topic productivity --add-topic linter \
  --add-topic growth

gh repo edit --homepage "https://chxhwc.github.io/starcheck/"
gh repo edit --enable-discussions
```

| # | 事项 | 为什么是硬前置 |
| --- | --- | --- |
| 1 | description 写好 | 搜索结果里只有这一行 |
| 2 | topics ≥ 10 | GitHub 站内搜索的主要入口 |
| 3 | 上传 social preview（`assets/social.png`，1280×640） | 分享出去的卡片默认是灰的 |
| 4 | 打 tag：`git tag v0.4.0 && git push --tags` | watcher 的第一次唤醒 |
| 5 | Pages 打开（`mkdocs.yml` 已就绪） | 多一个能被搜到的入口 |
| 6 | 发 PyPI（`release.yml` 已就绪，配 `PYPI_API_TOKEN`） | `uvx starcheck` 才算真的存在 |
| 7 | README 首屏有 GIF + 一条安装命令 | 决定了 90% 的转化 |
| 8 | Discussions 打开 | 给"用不了"的人一个不用开 issue 的出口 |
| 9 | 自己的仓库先打 95+ | 第一个被 `starcheck` 审计的仓库必须是自己 |
| 10 | 准备好一条 20 字以内的转述 | 别人帮你传播时只需要这一句 |

---

## 1. 叙事：为什么别人愿意转

工具类仓库传播的燃料从来不是功能，是**一句话能复述的立场**。

| 版本 | 文案 | 用途 |
| --- | --- | --- |
| 钩子（英） | Your repo is good. That is why nobody stars it. | README 首屏、HN 标题 |
| 钩子（中） | 你的项目很好。所以才没人 star。 | 即刻、V2EX、朋友圈 |
| 转述句 | A linter for the things that actually decide whether a repo gets stars. | 别人帮你介绍时 |
| 反差数据 | 我审计了 100 个 0-star 的仓库，79 个没有 description，64 个没有演示图。 | 长文开头（数据要自己跑一遍） |

规则：**先给立场，再给工具**。没人转发"一个 CLI"，大家转发"一句他一直想说但没说出口的话"。

---

## 2. 首发日时间表（北京时间）

只在 **周二或周三** 发。UTC 13:00–15:00 ≈ 北京 21:00–23:00 = 美东上午 9 点。

| 时间 | 动作 | 目的 |
| --- | --- | --- |
| T-3 天 | 只在 r/coolgithubprojects 这类小池子发一次 | 拿真实反馈改 README，不消耗主渠道 |
| T-0 21:00 | **Hacker News `Show HN`**，单点打 | 天花板由它决定 |
| T-0 21:10 | 自己发第一条评论：讲实现里最脏的那个坑 | HN 排名很吃评论活跃度 |
| T-0 23:30 | 看 2 小时数据：<10 分就放弃 HN，转 Reddit | 不恋战 |
| T+1 09:00 | Reddit 对应 sub（一天最多两个） | 美国时间的第二波 |
| T+1 20:00 | 中文渠道：V2EX + 即刻 + 掘金 | 国内晚上是高峰 |
| T+2 | 写一条"首发复盘"（数据全公开） | 复盘文本身就是二次传播物 |
| T+3 | awesome-list PR × 8 | 长期免费流量，不占当天 |

**一次只开一个渠道。** 同时全发＝无法归因，第二篇就没有可复用的经验。

---

## 3. 现成文案（直接复制）

### Hacker News — Show HN

```
Show HN: starcheck – audit a repo for star-readiness (28 checks, one score)

I kept giving the same advice to people with good repos and no stars: your README
opens with a table of contents, your install command is 240 lines down, there is no
GIF, your description is empty. All true, all useless, because there was never a
way to know when you were done.

So I made it falsifiable. 28 checks over four weighted dimensions (discovery,
conversion, credibility, distribution), one 0-100 score, and a paste-ready command
for every failure.

Design constraints, because they matter more than the feature list:
- stdlib only. `uvx starcheck` in 3 seconds, no venv, no install.
- every check must be decidable from the repo alone. Anything requiring taste is
  in the docs, not in the code.
- `skip` is not `fail`: offline mode cannot see your description or topics, so
  those drop out of the denominator instead of pretending to fail.
- it never executes code from the audited repo. It reads files as text.
- the box drawing degrades to ASCII on a GBK console instead of crashing.

It scores readiness, not results — it has no idea whether your idea is interesting.

    uvx starcheck owner/repo

https://github.com/chxhwc/starcheck
```

第一条评论（自己发，10 分钟内）：

```
Author here. The part I got wrong first: I assumed weight should track "how much
this annoys me". It should track how much it costs conversion.

A missing LICENSE (weight 3) does not lose you a visitor. A README with no GIF and
no install command in the first screen (weight 5 each) loses you most of them. The
scoring model got much more useful once I made weights a budget — no single check
may move the score by more than ~7 points.

Happy to argue about any of the 28. That is what docs/SCORECARD.md is for.
```

### Reddit — r/commandline, r/opensource, r/coolgithubprojects

标题（不带感叹号，sub 规则不同）：

```
starcheck: a linter for the things that actually decide whether a repo gets stars
```

正文：首图 `assets/social.png` + HN 正文前两段 + 一条 curl/uvx 命令。**不要在正文里说 "please star"**，七个 sub 里有五个会因此删帖。

### X / Twitter — 一条主推 + 三条回复

```
Your repo is good. That is why nobody stars it.

I built a linter for the 28 things that actually decide it — description, topics,
first-screen install, GIF, maintenance signals.

28 checks. One score. Zero dependencies.

uvx starcheck

[GIF]
```

回复 1：一张 62/100 的真实审计截图（红黄绿一眼看懂）
回复 2：`--fix` 的输出（哦，它还给命令）
回复 3：`--badge` + "put the score in your README, it is also a share button"

### V2EX（分享创造）

标题：`starcheck：给仓库做一次「star 就绪度」体检，28 项，一个分数`

正文结构：痛点两句 → 一张 GIF → 一条命令 → 四个维度的表 → 「它不判断你的点子有没有意思」。
**结尾放 GitHub 链接，不要放 star 请求。**

### 掘金 / 少数派

不要发工具介绍，发**方法文**：《我审计了 100 个 0 star 的仓库，发现了 5 个共同点》，
工具只在文末出现一次。方法文的阅读量通常是工具文的 5 倍。

---

## 4. awesome-list 提交清单

一个 PR 加一行，长期免费流量。按契合度排：

| 仓库 | 建议归入 |
| --- | --- |
| `matiassingers/awesome-readme` | Tools / Linters |
| `agarrharr/awesome-cli-apps` | Development |
| `vinta/awesome-python` | Tools → Command-line Application Development |
| `sdras/awesome-actions` | Tooling |
| `Kikobeats/awesome-github` | Tools |
| `dkhamsing/open-source-ios-apps` | 不适用，跳过 |
| `mikethebeast/awesome-devtools`（或同类 devtools 列表） | CLI |
| `521xueweihan/HelloGitHub` | 提 issue 自荐，每月一期 |
| `ruanyf/weekly` | 提 issue，注明「自荐」 |

行格式（照抄列表里相邻条目，别自己发明格式）：

```markdown
- [starcheck](https://github.com/chxhwc/starcheck) - Audit a repo for star-readiness: 28 checks, one score, paste-ready fixes.
```

PR 描述模板：

```
Adds starcheck, a zero-dependency CLI that scores a repo against 28
star-readiness checks. Relevant here because it is a README/distribution
linter, which is what this list is about.
```

---

## 5. 周刊投稿

| 目标 | 入口 | 备注 |
| --- | --- | --- |
| HelloGitHub | GitHub issue 自荐 | 中文，月度，命中率高 |
| 阮一峰周刊 | `ruanyf/weekly` issue | 中文，周五发，注明自荐 |
| Console Dev | console.dev/submit | 专门收 CLI 工具，转化极好 |
| Python Weekly | pythonweekly.com 提交表单 | 英文 |
| PyCoders Weekly | pycoders.com 提交 | 英文 |
| TLDR / Changelog Weekly | 官网表单 | 需要一点新闻性（如 v1.0） |

邮件正文（≤120 词，别写长）：

```
Subject: starcheck — a linter for repo star-readiness (zero deps)

Hi — one-line pitch: starcheck audits a repo against the 28 signals that decide
whether strangers star it (description, topics, first-screen install, GIF,
maintenance signals), returns one score, and prints the exact commands to fix
the top 3.

Why it fits your readers: it is a two-minute `uvx` call with no dependencies,
and the output is a screenshot people paste into their own README.

  uvx starcheck owner/repo            # https://github.com/chxhwc/starcheck
```

---

## 6. 第一周的承接（比首发更重要）

首发只决定前 200 个 star，承接决定后面 2000 个。

- **12 小时内回完所有 issue**，哪怕只是 "reproduced, fix tonight"。
- **合并 3 个外部 PR**，并在 CHANGELOG 里点名。每个贡献者都是一个传播节点。
- **把最常见的抱怨变成 v0.5 的第一个 feature**，然后在 issue 里 @ 那个人。
- **每天发一条审计别人的实录**（征得同意的公开仓库），配一句结论。这是可复用的内容引擎：
  `starcheck psf/requests` → 一张图 → "一个 6 万 star 的仓库也才 84 分，因为 X"。
- **发一次 v0.5 release**：watcher 通知是唯一能主动触达老用户的通道。

---

## 7. 指标与止损

| 时间 | 看什么 | 合格线 | 不合格怎么办 |
| --- | --- | --- | --- |
| T+2h | HN 分数 | ≥ 10 | 放弃 HN，转 Reddit，别重发 |
| T+24h | star 增量 | ≥ 50 | 说明首屏没说服人 → 改 GIF 和标题，不重发 |
| T+72h | star/访客比 | ≥ 5% | 说明来的人不对 → 换渠道，不换文案 |
| T+7d | fork 数 | ≥ 3 | 说明没人想改 → 说明工具太窄，考虑加维度 |
| T+30d | 自然流量占比 | ≥ 30% | 说明没沉淀 → 补齐 awesome-list 和周刊 |

止损规则：**同一个渠道，同一份文案，只发一次。** 重发换的是标题和首图，不是时间。

---

## 8. 反模式

- **买 star / 互 star 群**：GitHub 有异常增长检测，账号降权、Trending 直接踢；
  star/fork 比例失真后，懂行的人扫一眼仓库就知道，在招聘和融资场景是负资产。
- **"求 star"**：七个 sub 里有五个会因此删帖，HN 会直接沉。
- **抽奖换 star**：来的人永远不会用你的工具，转化率数据从此不可信。
- **一次发十个渠道**：无法归因，第二次就没有可复用的经验。
- **把首发当终点**：首发之后的两周，才是 star 曲线真正分叉的地方。

---

## 9. 这份 runbook 的复用方式

下次做新项目，只需要改三处：

1. 第 1 节的四句话（钩子、转述句、反差数据）
2. 第 3 节的标题和正文
3. 第 4 节的 awesome-list 清单

其余（时间表、承接 SOP、指标、反模式）与项目无关，直接照抄。
