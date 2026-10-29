# Scorecard

Every check, its weight, and exactly what evidence it reads. Total weight: **72**.
Score = `100 × Σ(weight × factor) / Σ(weight)`, where `pass = 1.0`, `warn = 0.5`,
`fail = 0`, and `skip` is removed from the denominator.

> Weights are a budget, not a vote. If a single check can move the score by more
> than ~7 points, it is probably measuring two things at once.

## 发现 discovery — 24

| id | 检查 | 权重 | 判定依据 | 为什么重要 |
| --- | --- | --- | --- | --- |
| `desc` | 仓库描述 | 5 | GitHub API `description`，长度 20–160 | 搜索结果和列表页只有这一行，空描述等于不存在 |
| `topics` | Topics 标签 | 4 | API `topics` ≥ 10（5 以上给 warn） | GitHub 站内搜索的主要入口，零成本 |
| `license` | 开源协议 | 3 | 根目录 `LICENSE*` / `COPYING*` | 没有协议，公司用户直接跳过 |
| `name` | 仓库名 | 2 | ≤ 24 字符、可拼写、能直接当命令 | 名字 = 命令名 = 搜索词 |
| `social` | 社交预览图 | 2 | 存在 `social/preview/og-image/cover.(png\|jpg)` | 分享出去的卡片默认是灰的 |
| `homepage` | 主页 / demo | 3 | API `homepage` 是 URL | 唯一能放「点开就能用」的位置 |
| `hook` | README 首屏钩子 | 5 | 前 10 行有 `# ` 标题 + 一句 ≥ 40 字的定位 | 大多数人只读首屏 |

## 转化 conversion — 26

| id | 检查 | 权重 | 判定依据 | 为什么重要 |
| --- | --- | --- | --- | --- |
| `install` | 安装命令在首屏 | 5 | 前 35 行匹配 `pip/uvx/brew/go/cargo/docker/npx…` | 安装成本每多一步，转化掉一半 |
| `codeblock` | 首屏有代码块 | 3 | 前 40 行有闭合 ``` | 代码块是可复制的信任 |
| `visual` | 演示图 / GIF | 5 | README 中有 `.gif`（有静态图给 warn） | 8 秒 GIF 是最高杠杆的单个资产 |
| `badges` | 状态徽章 | 2 | 首屏 ≥ 2 个 shields/badge | 「在跑、有协议、有版本」的最低成本信号 |
| `features` | Why 段落 | 3 | 存在 `## Why` / Features / 亮点 标题 | 读者需要知道它和同类差在哪 |
| `quickstart` | 快速开始 | 4 | 存在 Quick start / Usage / 快速开始 | 从「看到」到「跑起来」的最短路径 |
| `bilingual` | 多语言 README | 2 | 存在 `README.<lang>.md` | 一份内容，两拨流量 |
| `readme-size` | README 长度 | 2 | 1200–12000 字符 | 太短没信息，太长稀释首屏 |

## 可信 credibility — 15

| id | 检查 | 权重 | 判定依据 | 为什么重要 |
| --- | --- | --- | --- | --- |
| `ci` | CI 配置 | 3 | `.github/workflows/*.yml` 或同类 | 「写完就没再碰」的第一印象 |
| `tests` | 测试 | 2 | `tests/` `spec/` 或 `test_*.py` | 信任度的下限 |
| `release` | 版本 / Release | 3 | git tag 或 API `releases/latest` | watcher 靠 release 被唤醒 |
| `changelog` | CHANGELOG | 1 | 根目录 `CHANGELOG*` | 让人一眼看到节奏 |
| `contributing` | CONTRIBUTING | 1 | 根目录 `CONTRIBUTING*` | 降低提 PR 的心理成本 |
| `issue-templates` | Issue / PR 模板 | 1 | `.github/ISSUE_TEMPLATE/` | 好 issue 是好项目的副产品 |
| `security` | SECURITY.md | 1 | 根目录或 `.github/` | 企业采用的前置条件 |
| `recency` | 最近有提交 | 2 | 最后一次 commit ≤ 90 天（1 年内 warn） | 弃坑判定 |
| `deps-bot` | 依赖机器人 | 1 | `dependabot.yml` / `renovate.json` | 零成本的「在维护」信号 |

## 分发 distribution — 7

| id | 检查 | 权重 | 判定依据 | 为什么重要 |
| --- | --- | --- | --- | --- |
| `docs-site` | 文档站 / Pages | 2 | API `has_pages` 或 mkdocs/docusaurus/vitepress | 多一个能被搜到的入口 |
| `package-meta` | 可安装 + keywords | 2 | pyproject/package.json/Cargo.toml 且 keywords ≥ 5 | 包索引本身就是分发渠道 |
| `action` | `action.yml` | 2 | 存在 `action.yml` | 被别人的 CI 拉进来 = 被动曝光 |
| `awesome` | awesome-list 收录 | 1 | README 中出现 awesome-list 链接 | 最便宜的长期流量 |

## 已知偏差

- **`awesome` 是启发式。** 它只检查 README 里有没有 awesome-list 链接，判断不了
  你是否真的被收录了。权重 1，不打算修。
- **`desc` / `topics` / `homepage` / `docs-site` 依赖网络。** 本地模式全部 `skip`，
  所以本地分和远程分不能直接比。
- **`hook` 只看首 10 行。** 一个很好的 README 也可能因为一行烂标题拿不到分——这正是
  想抓的东西。
- **它不测「有没有人 star」。** 见 [docs/index.md](index.md#limits)。
