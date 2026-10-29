<div align="center">

# starcheck

**你的项目很好。所以才没人 star。**

28 项检查 → 一个分数 → 3 条真正能改动的建议。

[![CI](https://github.com/chxhwc/starcheck/actions/workflows/ci.yml/badge.svg)](https://github.com/chxhwc/starcheck/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/starcheck.svg)](https://pypi.org/project/starcheck/)
[![runtime deps](https://img.shields.io/badge/runtime%20deps-0-brightgreen.svg)](#)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[快速开始](#快速开始) · [检查什么](#检查什么) · [English](README.md)

</div>

![starcheck 正在审计一个仓库](assets/demo.gif)

## 快速开始

```bash
uvx starcheck              # 审计你当前所在的仓库，零安装
starcheck chxhwc/starcheck    # 审计别人的仓库（浅克隆 + GitHub API）
```

<sub>还没上 PyPI？先 `pip install git+https://github.com/chxhwc/starcheck`，今天就能用。</sub>

```console
$ starcheck .
┌──────────────────────────────────────────────────────────────────────────┐
│ starcheck · my-lib                                           62/100  C   │
├──────────────────────────────────────────────────────────────────────────┤
│ ██████████████░░░░░░░░  62/100                                            │
│ 发现 78   转化 44   可信 71   分发 37                                     │
├──────────────────────────────────────────────────────────────────────────┤
│   ✔ 安装命令在首屏            首屏就能看到 `pip install my-lib`            │
│   ✘ 演示图 / GIF              README 里没有任何演示图                      │
└──────────────────────────────────────────────────────────────────────────┘
```

然后：

```bash
starcheck . --fix          # 每一条失败都给一条能直接粘贴的命令
starcheck . --json         # 机器可读：分数、等级、28 项明细
starcheck . --badge score.svg --markdown REPORT.md
starcheck . --fail-under 80      # 低于 80 退出码 1，直接进 CI
```

## Why

因为所有人给你的建议都一样，而且一样没用：

> 「写好 README、加个 LICENSE、发到 Hacker News。」

三句真话，没有顺序，也没有任何办法判断自己做完没有。`starcheck` 就是把这句话变成**可判定的**：

- **加权，不是清单。** 清单说你 20 项都错了，结果你一项都没改。权重告诉你：
  这周先修首屏钩子和 GIF，`SECURITY.md` 可以放着。
- **可判定，不是感觉。** 每条检查只读文件或 API 字段，没有品味问题，
  所以你可以反驳，而且能赢。
- **先给修复。** 一条没有可粘贴命令的失败，只是批评。

## 一句话原理

star 不是代码质量指标，它是：

```
star  ≈  曝光量  ×  首屏转化率  ×  复用频次
```

绝大多数「写得好但没人 star」的项目，输在中间那一项，而且输的原因跟代码毫无关系：
没有 description、只有 2 个 topics、没有演示图、安装命令在 240 行之后、README 一上来是目录
而不是一个让人想读下去的理由。

`starcheck` 把这句正确的废话拆成 28 条可判定的检查，并按「它对转化的真实杀伤力」加权——
真正会让人关掉页面的那几项，扣分最狠。

## 检查什么

| 维度 | 权重 | 看什么 |
| --- | --- | --- |
| **发现** | 24 | description · topics · license · 仓库名 · 社交预览图 · homepage · README 首屏钩子 |
| **转化** | 26 | 首屏安装命令 · 代码块 · GIF · 徽章 · Why 段落 · Quick start · 多语言 · README 长度 |
| **可信** | 15 | CI · 测试 · tag/Release · CHANGELOG · CONTRIBUTING · issue 模板 · SECURITY · 提交新鲜度 · 依赖机器人 |
| **分发** | 7 | Pages/文档站 · 包元数据与 keywords · action.yml · awesome-list 收录 |

等级：`A+ ≥95`、`A ≥88`、`B ≥70`、`C ≥55`、`D ≥35`、`E < 35`。

每一条检查就是 [`src/starcheck/checks.py`](src/starcheck/checks.py) 里的一个函数，
可读、可测、可以拿来吵。完整的权重与判定依据见 [docs/SCORECARD.md](docs/SCORECARD.md)。

## 设计原则

1. **只用标准库。** 有依赖就毁了它的意义——你本该能在任何一台机器上 3 秒 `uvx` 跑起来。
2. **一条检查必须只靠仓库本身就能判定。** 需要人主观判断的，写进文档，不写进代码。
3. **`skip` 不等于 `fail`。** 本地模式看不到 description 和 topics，那就从分母里拿掉，
   而不是假装它挂了。
4. **每条失败都带一条能粘贴的修复命令。** 不写「建议优化 README」这种话。
5. **它不执行你的代码。** 只把文件当文本读，仅此而已。
6. **GBK 控制台也要能看。** 见 `render.py` 里的 `Glyphs`：整体降级成 ASCII，而不是崩在 `█` 上。

## 在 CI 里用

```yaml
- uses: actions/checkout@v4
- run: pipx run starcheck . --fail-under 85
```

## 边界

`starcheck` 打的是**发布就绪度**，不是结果。它看不到你的流量、转化率，
也判断不了你的点子有没有意思。一个 100 分但无聊的项目，依然是个无聊的项目——
只是会被多读两眼再关掉。

## 协议

MIT
