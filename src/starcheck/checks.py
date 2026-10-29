"""The 28 checks. One function per check, all pure: Context in, Check out."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

DIMENSIONS = {
    "discovery": ("发现", "有人搜得到你吗"),
    "conversion": ("转化", "点进来的人会 star 吗"),
    "credibility": ("可信", "看起来像在认真维护吗"),
    "distribution": ("分发", "有二次传播的钩子吗"),
}

FACTOR = {"pass": 1.0, "warn": 0.5, "fail": 0.0}


@dataclass
class Check:
    id: str
    title: str
    dimension: str
    weight: int
    status: str = "skip"
    detail: str = ""
    fix: str = ""

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "dimension": self.dimension,
            "weight": self.weight,
            "status": self.status,
            "detail": self.detail,
            "fix": self.fix,
        }


@dataclass
class Context:
    root: Path
    files: list
    readme: str = ""
    readme_name: str = ""
    meta: dict = field(default_factory=dict)
    git: dict = field(default_factory=dict)
    remote: dict = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.remote.get("name") or self.root.name

    def has_file(self, pattern: str) -> bool:
        rx = re.compile(pattern, re.I)
        return any(rx.search(f) for f in self.files)

    def first_lines(self, n: int) -> list:
        lines = [ln.strip() for ln in self.readme.splitlines()]
        return [ln for ln in lines if ln][:n]


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------

REGISTRY = []


def check(cid, title, dimension, weight):
    def deco(fn):
        REGISTRY.append((cid, title, dimension, weight, fn))
        return fn

    return deco


# --------------------------------------------------------------------------
# context building
# --------------------------------------------------------------------------

SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    "target",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "vendor",
    ".next",
    ".tox",
    "site-packages",
}

README_NAMES = ["readme.md", "readme.rst", "readme.txt", "readme"]


def walk_files(root: Path, limit: int = 20000) -> list:
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fn in sorted(filenames):
            rel = (Path(dirpath) / fn).relative_to(root).as_posix()
            out.append(rel)
            if len(out) >= limit:
                return out
    return out


def find_readme(files: list) -> str:
    top = {f.lower(): f for f in files if "/" not in f}
    for name in README_NAMES:
        if name in top:
            return top[name]
    return ""


def read_text(path: Path, limit: int = 400_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def read_meta(root: Path, files: list) -> dict:
    meta = {"keywords": [], "description": "", "kind": ""}
    lower = {f.lower() for f in files if "/" not in f}

    if "pyproject.toml" in lower:
        meta["kind"] = "python"
        raw = read_text(root / "pyproject.toml")
        try:
            import tomllib

            data = tomllib.loads(raw)
            proj = data.get("project", {})
            meta["keywords"] = list(proj.get("keywords", []) or [])
            meta["description"] = proj.get("description", "") or ""
            meta["scripts"] = list((proj.get("scripts") or {}).keys())
        except Exception:
            kw = re.search(r"keywords\s*=\s*\[(.*?)\]", raw, re.S)
            meta["keywords"] = re.findall(r'"([^"]+)"', kw.group(1)) if kw else []
            desc = re.search(r'^description\s*=\s*"([^"]*)"', raw, re.M)
            meta["description"] = desc.group(1) if desc else ""
    elif "package.json" in lower:
        meta["kind"] = "node"
        try:
            data = json.loads(read_text(root / "package.json"))
            meta["keywords"] = list(data.get("keywords") or [])
            meta["description"] = data.get("description", "") or ""
        except Exception:
            pass
    elif "cargo.toml" in lower:
        meta["kind"] = "rust"
        raw = read_text(root / "Cargo.toml")
        desc = re.search(r'^description\s*=\s*"([^"]*)"', raw, re.M)
        meta["description"] = desc.group(1) if desc else ""
        kw = re.search(r"^keywords\s*=\s*\[(.*?)\]", raw, re.M | re.S)
        meta["keywords"] = re.findall(r'"([^"]+)"', kw.group(1)) if kw else []
    elif "go.mod" in lower:
        meta["kind"] = "go"
    return meta


def git_info(root: Path) -> dict:
    info = {"tags": [], "commits": "", "last_commit": 0, "origin": ""}

    def run(*args):
        try:
            proc = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return proc.stdout.strip() if proc.returncode == 0 else ""
        except (OSError, subprocess.SubprocessError):
            return ""

    info["tags"] = [t for t in run("tag", "--sort=-creatordate").splitlines() if t][:8]
    info["commits"] = run("rev-list", "--count", "HEAD")
    raw = run("log", "-1", "--format=%ct")
    if raw.isdigit():
        info["last_commit"] = int(raw)
    info["origin"] = run("remote", "get-url", "origin")
    return info


def parse_origin(url: str):
    """'git@github.com:o/r.git' or 'https://github.com/o/r' -> (o, r)."""
    if not url:
        return None
    m = re.search(r"github\.com[:/]+([^/]+)/([^/\s]+?)(?:\.git)?/?$", url)
    if not m:
        return None
    return m.group(1), m.group(2)


def build_context(root: Path, remote: dict = None) -> Context:
    root = Path(root).resolve()
    files = walk_files(root)
    readme_name = find_readme(files)
    readme = read_text(root / readme_name) if readme_name else ""
    ctx = Context(
        root=root,
        files=files,
        readme=readme,
        readme_name=readme_name,
        meta=read_meta(root, files),
        git=git_info(root),
        remote=remote or {},
    )
    return ctx


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

INSTALL_RX = re.compile(
    r"(pip3? install|uv (?:pip )?install|uvx |pipx (?:run|install)|npm (?:i|install)|pnpm (?:add|i|install)"
    r"|yarn (?:add|global add)|brew install|go install|cargo install|docker run|npx |iwr |choco install"
    r"|winget install|scoop install|curl -[A-Za-z]*f[A-Za-z]* https?://|git clone )",
    re.I,
)
BADGE_RX = re.compile(r"(img\.shields\.io|badge\.fury\.io|badgen\.net|badge|travis-ci|codecov)", re.I)
IMAGE_RX = re.compile(r"!\[[^\]]*\]\(([^)\s]+\.(?:png|jpe?g|gif|webp|svg))", re.I)
CODEBLOCK_RX = re.compile(r"```")
HEADING_RX = re.compile(r"^#{1,6}\s", re.M)


def _image_urls(text: str) -> list:
    return [u for u in IMAGE_RX.findall(text) if not BADGE_RX.search(u)]


def _first_screen(text: str, lines: int = 30) -> str:
    return "\n".join(text.splitlines()[:lines])


def _has_section(text: str, *words) -> bool:
    for line in text.splitlines():
        if HEADING_RX.match(line.strip()):
            low = line.lower()
            if any(w in low for w in words):
                return True
    return False


def _remote_missing(ctx: Context) -> bool:
    return not ctx.remote


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------


@check("desc", "仓库描述", "discovery", 5)
def _desc(ctx: Context) -> Check:
    c = Check("desc", "仓库描述", "discovery", 5)
    if _remote_missing(ctx):
        c.status = "skip"
        c.detail = "未取到 GitHub 元数据（本地模式）"
        c.fix = "gh repo edit --description \"一句话说清它替谁省了什么\""
        return c
    desc = (ctx.remote.get("description") or "").strip()
    if not desc:
        c.status, c.detail = "fail", "空描述 -- 搜索和列表里都不会有人点"
    elif len(desc) > 160:
        c.status, c.detail = "warn", f"{len(desc)} 字符，超过 160 会被截断"
    elif len(desc) < 20:
        c.status, c.detail = "warn", f"只有 {len(desc)} 字符，信息量不足"
    else:
        c.status, c.detail = "pass", f"{len(desc)} 字符"
    c.fix = 'gh repo edit --description "用 X 一条命令替代 Y"'
    return c


@check("topics", "Topics 标签", "discovery", 4)
def _topics(ctx: Context) -> Check:
    c = Check("topics", "Topics 标签", "discovery", 4)
    if _remote_missing(ctx):
        c.status = "skip"
        c.detail = "本地模式无法读取 topics"
        c.fix = "gh repo edit --add-topic cli --add-topic developer-tools"
        return c
    topics = ctx.remote.get("topics") or []
    n = len(topics)
    if n >= 10:
        c.status, c.detail = "pass", f"{n} 个标签"
    elif n >= 5:
        c.status, c.detail = "warn", f"{n} 个标签，建议 10-20 个"
    else:
        c.status, c.detail = "fail", f"{n} 个标签 -- 少了 GitHub 搜索的主要入口"
    c.fix = "gh repo edit --add-topic " + " --add-topic ".join(
        ["cli", "developer-tools", "github", "productivity"]
    )
    return c


@check("license", "开源协议", "discovery", 3)
def _license(ctx: Context) -> Check:
    c = Check("license", "开源协议", "discovery", 3)
    if ctx.has_file(r"^(license|licence|copying)(\.(md|txt))?$"):
        c.status, c.detail = "pass", "已声明协议"
    else:
        c.status, c.detail = "fail", "没有 LICENSE -- 公司用户直接跳过你"
        c.fix = "选 MIT：https://choosealicense.com/licenses/mit/"
    return c


@check("name", "仓库名", "discovery", 2)
def _name(ctx: Context) -> Check:
    c = Check("name", "仓库名", "discovery", 2)
    name = ctx.name
    if len(name) <= 24 and re.fullmatch(r"[a-z0-9][a-z0-9._-]*", name):
        c.status, c.detail = "pass", f"`{name}` 短、可拼写、能当命令用"
    elif len(name) > 24:
        c.status, c.detail = "warn", f"`{name}` 偏长，不好念也不好搜"
    else:
        c.status, c.detail = "warn", f"`{name}` 含非标准字符或大小写混杂"
    c.fix = "名字 = 命令名 = 搜索词，最好一个词"
    return c


@check("social", "社交预览图", "discovery", 2)
def _social(ctx: Context) -> Check:
    c = Check("social", "社交预览图 / OG 图", "discovery", 2)
    if ctx.has_file(r"(social|preview|og[-_]?image|cover)\.(png|jpe?g|webp)$"):
        c.status, c.detail = "pass", "找到预览图资源"
    else:
        c.status, c.detail = "warn", "没找到预览图 -- 分享出去的卡片是灰的"
        c.fix = "Settings → Social preview 上传 1280×640 的图"
    return c


@check("homepage", "主页 / 在线 demo", "discovery", 3)
def _homepage(ctx: Context) -> Check:
    c = Check("homepage", "主页 / 在线 demo", "discovery", 3)
    if _remote_missing(ctx):
        c.status = "skip"
        c.detail = "本地模式无法读取 homepage"
        c.fix = "gh repo edit --homepage https://your-demo-url"
        return c
    hp = (ctx.remote.get("homepage") or "").strip()
    if hp.startswith("http"):
        c.status, c.detail = "pass", hp
    else:
        c.status, c.detail = "fail", "没设主页 -- 少了唯一能放 demo 的位置"
        c.fix = "gh repo edit --homepage https://your-demo-url"
    return c


@check("hook", "README 首屏钩子", "discovery", 5)
def _hook(ctx: Context) -> Check:
    c = Check("hook", "README 首屏钩子", "discovery", 5)
    if not ctx.readme:
        c.status, c.detail = "fail", "没有 README"
        c.fix = "第一行写：它替谁解决了什么，带上数字"
        return c
    heads = ctx.first_lines(10)
    has_h1 = any(h.startswith("# ") for h in heads)
    body = [h for h in heads if not h.startswith(("#", "!", "[!", "<", "|", ">")) and len(h) >= 40]
    if has_h1 and body:
        c.status, c.detail = "pass", "标题 + 40 字以上的定位句都在首屏"
    elif has_h1:
        c.status, c.detail = "warn", "有标题，但缺一句能说服人的定位句"
        c.fix = "标题下第一行：`一条命令解决 X，不用装 Y`"
    else:
        c.status, c.detail = "fail", "首屏没有 H1 标题"
        c.fix = "第一行 `# 名字 -- 一句话卖点`"
    return c


# --------------------------------------------------------------------------
# conversion
# --------------------------------------------------------------------------


@check("install", "安装命令在首屏", "conversion", 5)
def _install(ctx: Context) -> Check:
    c = Check("install", "安装命令在首屏", "conversion", 5)
    if not ctx.readme:
        c.status, c.detail = "fail", "没有 README"
        return c
    screen = _first_screen(ctx.readme, 35)
    m = INSTALL_RX.search(screen)
    if m:
        c.status, c.detail = "pass", f"首屏就能看到 `{m.group(0).strip()}`"
    elif INSTALL_RX.search(ctx.readme):
        c.status, c.detail = "warn", "有安装命令，但埋在 35 行之后"
        c.fix = "把安装命令提到首屏，复制即用"
    else:
        c.status, c.detail = "fail", "找不到任何安装命令"
        c.fix = "写一条能直接粘贴执行的安装命令"
    return c


@check("codeblock", "首屏有代码块", "conversion", 3)
def _codeblock(ctx: Context) -> Check:
    c = Check("codeblock", "首屏有代码块", "conversion", 3)
    screen = _first_screen(ctx.readme, 40)
    n = len(CODEBLOCK_RX.findall(screen)) // 2
    if n >= 1:
        c.status, c.detail = "pass", f"首屏 {n} 个代码块"
    else:
        c.status, c.detail = "warn", "首屏没有代码块"
        c.fix = "加一个 ```bash 的安装块 + 一个输出示例"
    return c


@check("visual", "演示图 / GIF", "conversion", 5)
def _visual(ctx: Context) -> Check:
    c = Check("visual", "演示图 / GIF", "conversion", 5)
    imgs = [u for u in _image_urls(ctx.readme) if re.search(r"\.gif$", u, re.I)]
    if imgs:
        c.status, c.detail = "pass", f"有 GIF：{imgs[0]}"
    elif _image_urls(ctx.readme):
        c.status, c.detail = "warn", "有图但没有动图 -- 8 秒 GIF 的转化率最高"
        c.fix = "录一个 8 秒 GIF，放在首屏第一段之后"
    else:
        c.status, c.detail = "fail", "README 里没有任何演示图"
        c.fix = "录一个 8 秒 GIF，放在首屏第一段之后"
    return c


@check("badges", "状态徽章", "conversion", 2)
def _badges(ctx: Context) -> Check:
    c = Check("badges", "状态徽章", "conversion", 2)
    screen = _first_screen(ctx.readme, 12)
    n = len(re.findall(r"img\.shields\.io|badge", screen, re.I))
    if n >= 2:
        c.status, c.detail = "pass", f"{n} 个徽章"
    elif n == 1:
        c.status, c.detail = "warn", "只有 1 个徽章"
        c.fix = "至少：license + CI + 版本/下载量"
    else:
        c.status, c.detail = "warn", "首屏没有徽章"
        c.fix = "至少：license + CI + 版本/下载量"
    return c


@check("features", "Why 段落", "conversion", 3)
def _features(ctx: Context) -> Check:
    c = Check("features", "Why / Features 段落", "conversion", 3)
    if _has_section(ctx.readme, "why", "features", "highlights", "✨", "为什么"):
        c.status, c.detail = "pass", "有独立的价值主张段落"
    else:
        c.status, c.detail = "warn", "缺 Why 段落 -- 读者不知道它和同类有什么不同"
        c.fix = "加一节 `## Why`，3 条 bullet，每条带数字"
    return c


@check("quickstart", "可复制的快速开始", "conversion", 4)
def _quickstart(ctx: Context) -> Check:
    c = Check("quickstart", "可复制的快速开始", "conversion", 4)
    if _has_section(ctx.readme, "quick start", "quickstart", "getting started", "usage", "快速"):
        c.status, c.detail = "pass", "有快速开始段落"
    else:
        c.status, c.detail = "fail", "没有快速开始段落"
        c.fix = "## Quick start：3 行以内，从安装到看到结果"
    return c


@check("bilingual", "多语言 README", "conversion", 2)
def _bilingual(ctx: Context) -> Check:
    c = Check("bilingual", "多语言 README", "conversion", 2)
    alts = [f for f in ctx.files if re.match(r"readme\.[a-z]{2}(-[a-z]{2})?\.md$", f, re.I)]
    if alts:
        c.status, c.detail = "pass", f"有 {', '.join(alts[:3])}"
    else:
        c.status, c.detail = "warn", "只有一种语言"
        c.fix = "加 README.zh-CN.md 并在顶部互链，吃两拨流量"
    return c


@check("readme-size", "README 长度", "conversion", 2)
def _readme_size(ctx: Context) -> Check:
    c = Check("readme-size", "README 长度", "conversion", 2)
    n = len(ctx.readme)
    if 1200 <= n <= 12000:
        c.status, c.detail = "pass", f"{n} 字符"
    elif n == 0:
        c.status, c.detail = "fail", "空的"
    elif n < 1200:
        c.status, c.detail = "warn", f"只有 {n} 字符，信息量不够"
        c.fix = "补齐：安装 / 一条示例 / 输出长什么样 / 为什么用它"
    else:
        c.status, c.detail = "warn", f"{n} 字符，太长会稀释首屏"
        c.fix = "把细节挪到 docs/，首屏只留钩子"
    return c


# --------------------------------------------------------------------------
# credibility
# --------------------------------------------------------------------------


@check("ci", "CI 配置", "credibility", 3)
def _ci(ctx: Context) -> Check:
    c = Check("ci", "CI 配置", "credibility", 3)
    if ctx.has_file(r"^\.github/workflows/.*\.ya?ml$") or ctx.has_file(
        r"^(\.gitlab-ci\.yml|\.travis\.yml|azure-pipelines\.yml)$"
    ):
        c.status, c.detail = "pass", "有 CI workflow"
    else:
        c.status, c.detail = "fail", "没有 CI -- 给人一种「写完就没再碰」的感觉"
        c.fix = "加 .github/workflows/ci.yml，跑 lint + test"
    return c


@check("tests", "测试目录", "credibility", 2)
def _tests(ctx: Context) -> Check:
    c = Check("tests", "测试", "credibility", 2)
    if ctx.has_file(r"(^|/)(tests?|spec|__tests__)/") or ctx.has_file(r"(^|/)test_[^/]+\.py$"):
        c.status, c.detail = "pass", "有测试"
    else:
        c.status, c.detail = "warn", "没找到测试 -- 信任度打折"
        c.fix = "加 tests/，哪怕只測一个核心函数"
    return c


@check("release", "有版本发布", "credibility", 3)
def _release(ctx: Context) -> Check:
    c = Check("release", "有版本 / Release", "credibility", 3)
    tags = ctx.git.get("tags") or []
    if tags:
        c.status, c.detail = "pass", f"最新 tag：{tags[0]}"
    elif ctx.remote.get("latest_release"):
        c.status, c.detail = "pass", ctx.remote["latest_release"]
    else:
        c.status, c.detail = "warn", "还没打过 tag -- watcher 收不到更新通知"
        c.fix = "git tag v0.1.0 && git push --tags"
    return c


@check("changelog", "CHANGELOG", "credibility", 1)
def _changelog(ctx: Context) -> Check:
    c = Check("changelog", "CHANGELOG", "credibility", 1)
    if ctx.has_file(r"^(changelog|changes|history)(\.md|\.rst|\.txt)?$"):
        c.status, c.detail = "pass", "有变更日志"
    else:
        c.status, c.detail = "warn", "没有 CHANGELOG"
        c.fix = "加 CHANGELOG.md，Keep a Changelog 格式"
    return c


@check("contributing", "CONTRIBUTING", "credibility", 1)
def _contributing(ctx: Context) -> Check:
    c = Check("contributing", "CONTRIBUTING", "credibility", 1)
    if ctx.has_file(r"^contributing(\.md|\.rst|\.txt)?$"):
        c.status, c.detail = "pass", "有贡献指南"
    else:
        c.status, c.detail = "warn", "没有 CONTRIBUTING -- 降低了别人提 PR 的概率"
        c.fix = "加 CONTRIBUTING.md，写清怎么跑测试"
    return c


@check("issue-templates", "Issue / PR 模板", "credibility", 1)
def _issue_templates(ctx: Context) -> Check:
    c = Check("issue-templates", "Issue / PR 模板", "credibility", 1)
    if ctx.has_file(r"^\.github/(ISSUE_TEMPLATE/|pull_request_template)"):
        c.status, c.detail = "pass", "有模板"
    else:
        c.status, c.detail = "warn", "没有 issue 模板"
        c.fix = "加 .github/ISSUE_TEMPLATE/bug_report.yml"
    return c


@check("security", "SECURITY.md", "credibility", 1)
def _security(ctx: Context) -> Check:
    c = Check("security", "SECURITY.md", "credibility", 1)
    if ctx.has_file(r"^security(\.md|\.txt)?$") or ctx.has_file(r"^\.github/security\.md$"):
        c.status, c.detail = "pass", "有安全策略"
    else:
        c.status, c.detail = "warn", "没有 SECURITY.md"
        c.fix = "GitHub 自动生成：Security → Advisories"
    return c


@check("recency", "最近有提交", "credibility", 2)
def _recency(ctx: Context) -> Check:
    c = Check("recency", "最近有提交", "credibility", 2)
    ts = ctx.git.get("last_commit") or 0
    if not ts:
        c.status, c.detail = "skip", "不是 git 仓库或没有提交"
        return c
    days = int((time.time() - ts) // 86400)
    if days <= 90:
        c.status, c.detail = "pass", f"{days} 天前还在动"
    elif days <= 365:
        c.status, c.detail = "warn", f"最后一次提交在 {days} 天前"
        c.fix = "哪怕只更新 README，也保持月度节奏"
    else:
        c.status, c.detail = "fail", f"已经 {days} 天没提交 -- 会被当成弃坑"
        c.fix = "发一个 patch release 重新进入时间线"
    return c


@check("deps-bot", "依赖机器人", "credibility", 1)
def _deps_bot(ctx: Context) -> Check:
    c = Check("deps-bot", "依赖更新机器人", "credibility", 1)
    if ctx.has_file(r"^(\.github/dependabot\.ya?ml|renovate\.json5?|\.renovaterc)$"):
        c.status, c.detail = "pass", "已配置自动依赖更新"
    else:
        c.status, c.detail = "warn", "没有 dependabot / renovate"
        c.fix = "加 .github/dependabot.yml，零成本加一份「在维护」信号"
    return c


# --------------------------------------------------------------------------
# distribution
# --------------------------------------------------------------------------


@check("docs-site", "文档站 / Pages", "distribution", 2)
def _docs_site(ctx: Context) -> Check:
    c = Check("docs-site", "文档站 / Pages", "distribution", 2)
    if ctx.remote.get("has_pages"):
        c.status, c.detail = "pass", "已开启 GitHub Pages"
    elif ctx.has_file(r"^(mkdocs\.ya?ml|docusaurus\.config\.[jt]s|\.vitepress/config\.[jt]s)$"):
        c.status, c.detail = "pass", "有文档站配置"
    elif ctx.has_file(r"^docs/(index|readme)\.md$"):
        c.status, c.detail = "warn", "有 docs/ 但没看到站点配置"
        c.fix = "开 Pages，README 里放链接 -- 也是一个可被搜到的入口"
    else:
        c.status, c.detail = "warn", "没有文档站"
        c.fix = "docs/ + Pages，至少让 README 短一点"
    return c


@check("package-meta", "可安装 / 关键词元数据", "distribution", 2)
def _package_meta(ctx: Context) -> Check:
    c = Check("package-meta", "可安装 + 关键词元数据", "distribution", 2)
    kind = ctx.meta.get("kind")
    if not kind:
        c.status, c.detail = "fail", "没找到包管理清单 -- 用户没法一条命令装上"
        c.fix = "发布到 PyPI / npm / Homebrew，安装成本越低 star 越多"
        return c
    kws = ctx.meta.get("keywords") or []
    if len(kws) >= 5:
        c.status, c.detail = "pass", f"{kind} 包，{len(kws)} 个关键词"
    else:
        c.status, c.detail = "warn", f"{kind} 包，但关键词只有 {len(kws)} 个"
        c.fix = "package 的 keywords 会被包索引搜索到，填满 10 个"
    return c


@check("action", "GitHub Action / 集成入口", "distribution", 2)
def _action(ctx: Context) -> Check:
    c = Check("action", "Action / 集成入口", "distribution", 2)
    if ctx.has_file(r"(^|/)action\.ya?ml$"):
        c.status, c.detail = "pass", "可以作为 Action 被复用"
    else:
        c.status, c.detail = "warn", "没有 action.yml -- 少了一个被别人的 CI 拉进来的入口"
        c.fix = "包一层 action.yml，白拿 Action 市场的曝光"
    return c


@check("awesome", "被 awesome-list 收录", "distribution", 1)
def _awesome(ctx: Context) -> Check:
    c = Check("awesome", "被 awesome-list 收录", "distribution", 1)
    link = re.search(r"\]\(\s*https?://github\.com/[^)\s]*awesome[^)\s]*\)", ctx.readme, re.I)
    if link:
        c.status, c.detail = "pass", "README 里有 awesome-list 的反链"
    else:
        c.status, c.detail = "warn", "没看到 awesome-list 反链 -- 这是最便宜的长期流量"
        c.fix = "给 5-10 个相关 awesome-list 提 PR 加一行，再在本仓 README 回链"
    return c


# --------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------


def run_checks(ctx: Context) -> list:
    out = []
    for cid, title, dim, weight, fn in REGISTRY:
        try:
            res = fn(ctx)
        except Exception as exc:  # a broken check must never kill the run
            res = Check(cid, title, dim, weight, "skip", f"检查失败：{exc}"[:200])
        res.id, res.title, res.dimension, res.weight = cid, title, dim, weight
        out.append(res)
    return out
