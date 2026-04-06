#!/usr/bin/env python3
"""
GitHub Stats Auto-Updater
每天自动获取所有仓库数据并更新 README 中的数据看板
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

GITHUB_TOKEN = os.environ.get("GH_TOKEN", "")
USERNAME = "bcefghj"
README_PATH = "README.md"
STATS_JSON_PATH = "stats.json"


def api_get(url):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "github-stats-updater")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get_all_repos():
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&page={page}&sort=updated"
        data = api_get(url)
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def get_user_info():
    return api_get(f"https://api.github.com/users/{USERNAME}")


def format_number(n):
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return str(n)


def build_stats_table(repos, user_info, now_str):
    own_repos = [r for r in repos if not r.get("fork")]

    total_stars = sum(r.get("stargazers_count", 0) for r in own_repos)
    total_forks = sum(r.get("forks_count", 0) for r in own_repos)
    followers = user_info.get("followers", 0)
    public_repos = user_info.get("public_repos", 0)

    # 保存 JSON 供 badge 使用
    stats_data = {
        "total_stars": total_stars,
        "total_forks": total_forks,
        "followers": followers,
        "public_repos": public_repos,
        "updated_at": now_str,
    }
    with open(STATS_JSON_PATH, "w") as f:
        json.dump(stats_data, f, indent=2)

    block = f"""<div align="center">

| ⭐ Stars | 🍴 Forks | 👥 Followers | 📦 Repos |
|:---:|:---:|:---:|:---:|
| **{total_stars}** | **{total_forks}** | **{followers}** | **{public_repos}** |

<sub>🔄 Updated: {now_str} · by <a href="https://github.com/bcefghj/bcefghj/actions">GitHub Actions</a></sub>

</div>

"""
    return block


def update_readme(stats_block):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = "<!-- STATS_START -->"
    end_marker = "<!-- STATS_END -->"
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        print("❌ 找不到 README 中的标记位置")
        return

    new_content = (
        content[: start_idx + len(start_marker)]
        + "\n"
        + stats_block
        + content[end_idx:]
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("✅ README 已更新")


def main():
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"🔄 开始更新 GitHub Stats... [{now_str}]")

    user_info = get_user_info()
    print(f"👤 用户: {user_info.get('login')}, 粉丝: {user_info.get('followers')}")

    repos = get_all_repos()
    own_repos = [r for r in repos if not r.get("fork")]
    print(f"📦 获取到 {len(own_repos)} 个自有仓库")

    stats_block = build_stats_table(repos, user_info, now_str)
    update_readme(stats_block)

    total_stars = sum(r.get("stargazers_count", 0) for r in own_repos)
    total_forks = sum(r.get("forks_count", 0) for r in own_repos)
    print(f"⭐ 总 Stars: {total_stars} | 🍴 总 Forks: {total_forks}")
    print("✅ 完成！")


if __name__ == "__main__":
    main()
