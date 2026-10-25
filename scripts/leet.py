#!/usr/bin/env python3
"""Small, dependency-free workflow helper for the LeetCode practice repository."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "progress.json"
README_PATH = ROOT / "README.md"
PROBLEMS_DIR = ROOT / "problems"
TEMPLATES_DIR = ROOT / "templates"
PROGRESS_START = "<!-- PROGRESS:START -->"
PROGRESS_END = "<!-- PROGRESS:END -->"
VALID_DIFFICULTIES = {"Easy", "Medium", "Hard"}


class WorkflowError(RuntimeError):
    pass


def load_db() -> dict[str, Any]:
    try:
        data = json.loads(DB_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkflowError(f"找不到进度文件：{DB_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"progress.json 格式错误：{exc}") from exc
    if not isinstance(data.get("problems"), list):
        raise WorkflowError("progress.json 的 problems 必须是数组")
    return data


def write_json(path: Path, data: Any) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def save_db(data: dict[str, Any]) -> None:
    write_json(DB_PATH, data)


def normalize_difficulty(value: str) -> str:
    normalized = value.strip().capitalize()
    if normalized not in VALID_DIFFICULTIES:
        raise WorkflowError("难度必须是 Easy、Medium 或 Hard")
    return normalized


def problem_dir(problem: dict[str, Any]) -> Path:
    return PROBLEMS_DIR / f"{int(problem['number']):04d}-{problem['slug']}"


def find_problem(data: dict[str, Any], key: str) -> dict[str, Any]:
    matches = [
        item
        for item in data["problems"]
        if str(item.get("number")) == key or item.get("slug") == key
    ]
    if not matches:
        raise WorkflowError(f"找不到题目：{key}")
    if len(matches) > 1:
        raise WorkflowError(f"题目标识不唯一：{key}")
    return matches[0]


def save_problem_metadata(problem: dict[str, Any]) -> None:
    directory = problem_dir(problem)
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "problem.json", problem)


def status_label(status: str) -> str:
    return {"todo": "待完成", "doing": "进行中", "solved": "已完成"}.get(
        status, status
    )


def render_progress(data: dict[str, Any]) -> str:
    problems = sorted(data["problems"], key=lambda item: int(item["number"]))
    target = int(data.get("target", 200))
    solved = sum(item.get("status") == "solved" for item in problems)
    doing = sum(item.get("status") == "doing" for item in problems)
    percent = (solved / target * 100) if target else 0.0
    lines = [
        PROGRESS_START,
        "## 进度",
        "",
        f"- 目标：{target} 题",
        f"- 已完成：{solved} / {target}（{percent:.1f}%）",
        f"- 进行中：{doing}",
        f"- 待完成：{len(problems) - solved - doing}",
        "",
        "| # | 题目 | 难度 | 状态 | 完成日期 | 用时 | 复习日 |",
        "|---:|---|---|---|---|---:|---|",
    ]
    if not problems:
        lines.append(
            "| - | 还没有题目。运行 `python scripts/leet.py new ...` 添加第一题。 | - | - | - | - | - |"
        )
    else:
        for item in problems:
            title = str(item["title"]).replace("|", "\\|")
            url = item.get("url", "")
            title_cell = f"[{title}]({url})" if url else title
            minutes = f"{item['minutes']} 分" if item.get("minutes") is not None else "-"
            reviews = ", ".join(item.get("review_dates", [])) or "-"
            lines.append(
                "| {number} | {title} | {difficulty} | {status} | {solved_at} | {minutes} | {reviews} |".format(
                    number=item["number"],
                    title=title_cell,
                    difficulty=item["difficulty"],
                    status=status_label(item.get("status", "todo")),
                    solved_at=item.get("solved_at") or "-",
                    minutes=minutes,
                    reviews=reviews,
                )
            )
    lines.append(PROGRESS_END)
    return "\n".join(lines)


def update_readme(data: dict[str, Any]) -> None:
    text = README_PATH.read_text(encoding="utf-8")
    if PROGRESS_START not in text or PROGRESS_END not in text:
        raise WorkflowError("README.md 缺少进度标记")
    prefix, remainder = text.split(PROGRESS_START, 1)
    _, suffix = remainder.split(PROGRESS_END, 1)
    README_PATH.write_text(
        prefix + render_progress(data) + suffix, encoding="utf-8"
    )


def command_new(args: argparse.Namespace) -> None:
    data = load_db()
    if any(int(item["number"]) == args.number for item in data["problems"]):
        raise WorkflowError(f"题号已存在：{args.number}")
    if any(item["slug"] == args.slug for item in data["problems"]):
        raise WorkflowError(f"slug 已存在：{args.slug}")
    if not args.slug or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in args.slug):
        raise WorkflowError("slug 只能包含小写字母、数字和连字符")

    problem = {
        "number": args.number,
        "slug": args.slug,
        "title": args.title,
        "difficulty": normalize_difficulty(args.difficulty),
        "url": args.url or "",
        "status": "todo",
        "created_at": date.today().isoformat(),
        "started_at": None,
        "solved_at": None,
        "minutes": None,
        "review_days": [],
        "review_dates": [],
    }
    directory = problem_dir(problem)
    directory.mkdir(parents=True, exist_ok=False)
    for name in ("attempt.md", "notes.md", "solution.cpp", "test.cpp"):
        shutil.copy2(TEMPLATES_DIR / name, directory / name)
    save_problem_metadata(problem)
    data["problems"].append(problem)
    save_db(data)
    update_readme(data)
    print(f"已新增 #{args.number} {args.title}：{directory.relative_to(ROOT)}")


def command_start(args: argparse.Namespace) -> None:
    data = load_db()
    problem = find_problem(data, args.problem)
    if problem.get("status") == "solved":
        print(f"#{problem['number']} {problem['title']} 已完成，将作为复习题打开。")
    else:
        problem["status"] = "doing"
        problem["started_at"] = problem.get("started_at") or datetime.now().isoformat(
            timespec="seconds"
        )
        save_problem_metadata(problem)
        save_db(data)
        update_readme(data)
        print(f"开始 #{problem['number']} {problem['title']}")
    print(problem.get("url") or "（未设置题目链接）")
    print(problem_dir(problem).relative_to(ROOT))


def command_next(_: argparse.Namespace) -> None:
    data = load_db()
    candidates = [
        item for item in data["problems"] if item.get("status") in {"doing", "todo"}
    ]
    candidates.sort(
        key=lambda item: (0 if item.get("status") == "doing" else 1, int(item["number"]))
    )
    if not candidates:
        if data["problems"]:
            print("当前题目已全部完成，请添加扩展题或运行 review 查看复习题。")
        else:
            print(
                "题库还是空的。先运行：python scripts/leet.py new <题号> <slug> \"题名\" <难度> --url <链接>"
            )
        return
    item = candidates[0]
    print(
        json.dumps(
            {
                "number": item["number"],
                "title": item["title"],
                "slug": item["slug"],
                "difficulty": item["difficulty"],
                "status": item["status"],
                "url": item.get("url", ""),
                "directory": str(problem_dir(item).relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def parse_review_days(value: str) -> list[int]:
    try:
        days = sorted({int(part.strip()) for part in value.split(",") if part.strip()})
    except ValueError as exc:
        raise WorkflowError("review-days 必须是逗号分隔的整数，例如 1,3,7,14,30") from exc
    if any(day <= 0 for day in days):
        raise WorkflowError("复习间隔必须是正整数")
    return days


def command_done(args: argparse.Namespace) -> None:
    data = load_db()
    problem = find_problem(data, args.problem)
    directory = problem_dir(problem)
    if not (directory / "solution.cpp").exists():
        raise WorkflowError(f"缺少答案文件：{directory / 'solution.cpp'}")
    solved_day = date.today()
    review_days = parse_review_days(args.review_days)
    problem.update(
        {
            "status": "solved",
            "started_at": problem.get("started_at")
            or datetime.now().isoformat(timespec="seconds"),
            "solved_at": solved_day.isoformat(),
            "minutes": args.minutes,
            "review_days": review_days,
            "review_dates": [
                (solved_day + timedelta(days=day)).isoformat() for day in review_days
            ],
        }
    )
    save_problem_metadata(problem)
    save_db(data)
    update_readme(data)
    print(f"已完成 #{problem['number']} {problem['title']}，README 进度已更新。")


def compiler() -> str:
    for name in ("g++", "clang++"):
        path = shutil.which(name)
        if path:
            return path
    raise WorkflowError("找不到 g++ 或 clang++；请先安装支持 C++17 的编译器")


def compile_and_run(problem: dict[str, Any], run_binary: bool = True) -> None:
    directory = problem_dir(problem)
    test_file = directory / "test.cpp"
    if not test_file.exists():
        raise WorkflowError(f"缺少测试入口：{test_file}")
    with tempfile.TemporaryDirectory(prefix="leetcode-check-") as temp_dir:
        binary = Path(temp_dir) / "test"
        result = subprocess.run(
            [
                compiler(),
                "-std=c++17",
                "-Wall",
                "-Wextra",
                "-pedantic",
                str(test_file),
                "-o",
                str(binary),
            ],
            cwd=directory,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            raise WorkflowError(
                f"#{problem['number']} 编译失败：\n{result.stdout}{result.stderr}"
            )
        if run_binary:
            run = subprocess.run(
                [str(binary)], cwd=directory, text=True, capture_output=True
            )
            if run.returncode != 0:
                raise WorkflowError(
                    f"#{problem['number']} 测试失败（退出码 {run.returncode}）：\n"
                    f"{run.stdout}{run.stderr}"
                )
            output = (run.stdout + run.stderr).strip()
            if output:
                print(output)


def command_check(args: argparse.Namespace) -> None:
    data = load_db()
    problem = find_problem(data, args.problem)
    compile_and_run(problem)
    print(f"#{problem['number']} {problem['title']} 编译和本地测试通过。")


def validate_data(data: dict[str, Any], compile_tests: bool) -> None:
    errors: list[str] = []
    numbers: set[int] = set()
    slugs: set[str] = set()
    required = {"attempt.md", "notes.md", "solution.cpp", "test.cpp", "problem.json"}
    for item in data["problems"]:
        number = item.get("number")
        slug = item.get("slug")
        if not isinstance(number, int) or number <= 0:
            errors.append(f"无效题号：{number!r}")
        elif number in numbers:
            errors.append(f"重复题号：{number}")
        numbers.add(number)
        if not isinstance(slug, str) or not slug:
            errors.append(f"题号 {number} 缺少 slug")
        elif slug in slugs:
            errors.append(f"重复 slug：{slug}")
        slugs.add(slug)
        if item.get("status") not in {"todo", "doing", "solved"}:
            errors.append(f"题号 {number} 状态无效：{item.get('status')}")
        if item.get("difficulty") not in VALID_DIFFICULTIES:
            errors.append(f"题号 {number} 难度无效：{item.get('difficulty')}")
        directory = problem_dir(item)
        if not directory.is_dir():
            errors.append(f"缺少目录：{directory.relative_to(ROOT)}")
            continue
        missing = sorted(name for name in required if not (directory / name).exists())
        if missing:
            errors.append(f"{directory.name} 缺少：{', '.join(missing)}")
        try:
            metadata = json.loads((directory / "problem.json").read_text(encoding="utf-8"))
            if metadata != item:
                errors.append(f"{directory.name}/problem.json 与 progress.json 不一致")
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            errors.append(f"{directory.name}/problem.json 无法读取：{exc}")
    if errors:
        raise WorkflowError("校验失败：\n- " + "\n- ".join(errors))
    if compile_tests:
        for item in sorted(data["problems"], key=lambda value: value["number"]):
            compile_and_run(item, run_binary=True)


def command_validate(args: argparse.Namespace) -> None:
    data = load_db()
    validate_data(data, args.compile)
    expected = render_progress(data)
    actual = README_PATH.read_text(encoding="utf-8")
    if expected not in actual:
        raise WorkflowError("README 进度表未同步，请运行 python scripts/leet.py stats")
    print(f"校验通过：{len(data['problems'])} 道题。")


def command_stats(_: argparse.Namespace) -> None:
    data = load_db()
    update_readme(data)
    solved = sum(item.get("status") == "solved" for item in data["problems"])
    target = int(data.get("target", 200))
    print(f"进度：{solved}/{target}；README 已更新。")


def command_review(_: argparse.Namespace) -> None:
    data = load_db()
    today = date.today().isoformat()
    due = [
        item
        for item in data["problems"]
        if item.get("status") == "solved"
        and any(review_date <= today for review_date in item.get("review_dates", []))
    ]
    if not due:
        print("今天没有到期的复习题。")
        return
    for item in sorted(due, key=lambda value: value["number"]):
        print(f"#{item['number']} {item['title']}  {item.get('url', '')}")


def run_git(arguments: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments], cwd=ROOT, text=True, capture_output=True, check=check
    )


def command_sync(args: argparse.Namespace) -> None:
    data = load_db()
    update_readme(data)
    validate_data(data, compile_tests=False)
    if not shutil.which("git"):
        raise WorkflowError("找不到 Git")
    inside = run_git(["rev-parse", "--is-inside-work-tree"], check=False)
    if inside.returncode != 0:
        raise WorkflowError("当前目录还不是 Git 仓库；请先运行 git init -b main")
    run_git(["add", "."])
    staged = run_git(["diff", "--cached", "--quiet"], check=False)
    if staged.returncode == 0:
        print("没有需要提交的变化。")
    elif staged.returncode == 1:
        committed = run_git(["commit", "-m", args.message], check=False)
        if committed.returncode != 0:
            raise WorkflowError(
                "Git 提交失败。请检查 user.name/user.email 配置：\n"
                + committed.stdout
                + committed.stderr
            )
        print(committed.stdout.strip())
    else:
        raise WorkflowError("无法检查暂存区：\n" + staged.stderr)

    remote = run_git(["remote", "get-url", "origin"], check=False)
    if remote.returncode != 0:
        print("本地提交已保留；尚未配置 origin，因此没有推送 GitHub。")
        return
    pushed = run_git(["push", "-u", "origin", "HEAD"], check=False)
    if pushed.returncode != 0:
        raise WorkflowError("GitHub 推送失败：\n" + pushed.stdout + pushed.stderr)
    print(f"已推送到 {remote.stdout.strip()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LeetCode Hot 100→200 C++17 刷题记录工具"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_parser = subparsers.add_parser("new", help="新增一道题")
    new_parser.add_argument("number", type=int, help="LeetCode 题号")
    new_parser.add_argument("slug", help="英文短名，例如 two-sum")
    new_parser.add_argument("title", help="中文或英文题名")
    new_parser.add_argument("difficulty", help="Easy / Medium / Hard")
    new_parser.add_argument("--url", default="", help="题目链接")
    new_parser.set_defaults(func=command_new)

    for name, help_text, handler in (
        ("start", "标记开始做题", command_start),
        ("check", "编译并运行本地测试", command_check),
    ):
        sub = subparsers.add_parser(name, help=help_text)
        sub.add_argument("problem", help="题号或 slug")
        sub.set_defaults(func=handler)

    done_parser = subparsers.add_parser("done", help="标记完成并安排复习")
    done_parser.add_argument("problem", help="题号或 slug")
    done_parser.add_argument("--minutes", type=int, default=None, help="本题用时（分钟）")
    done_parser.add_argument(
        "--review-days", default="1,3,7,14,30", help="复习间隔，逗号分隔"
    )
    done_parser.set_defaults(func=command_done)

    next_parser = subparsers.add_parser("next", help="显示下一题")
    next_parser.set_defaults(func=command_next)

    stats_parser = subparsers.add_parser("stats", help="更新 README 统计")
    stats_parser.set_defaults(func=command_stats)

    review_parser = subparsers.add_parser("review", help="列出到期复习题")
    review_parser.set_defaults(func=command_review)

    validate_parser = subparsers.add_parser("validate", help="校验记录和目录")
    validate_parser.add_argument(
        "--compile", action="store_true", help="同时编译并运行每题 test.cpp"
    )
    validate_parser.set_defaults(func=command_validate)

    sync_parser = subparsers.add_parser("sync", help="提交并在有 origin 时推送")
    sync_parser.add_argument("message", help="Git 提交信息")
    sync_parser.set_defaults(func=command_sync)
    return parser


def main() -> int:
    try:
        args = build_parser().parse_args()
        args.func(args)
        return 0
    except WorkflowError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"命令失败：{' '.join(exc.cmd)}\n{exc.stdout}{exc.stderr}", file=sys.stderr)
        return exc.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
