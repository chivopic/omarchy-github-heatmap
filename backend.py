#!/usr/bin/env python3
"""
Backend service for Omarchy GitHub Commit Heatmap Plugin.
Fetches, normalizes, and caches GitHub contribution data.
"""

import sys
import os
import json
import time
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, date, timedelta

CACHE_DIR = os.path.expanduser("~/.cache/omarchy-github-heatmap")
CONFIG_DIR = os.path.expanduser("~/.config/omarchy-github-heatmap")
CACHE_FILE = os.path.join(CACHE_DIR, "heatmap_data.json")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
CACHE_TTL_SECONDS = 1800  # 30 minutes


def ensure_dirs():
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config():
    ensure_dirs()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(cfg):
    ensure_dirs()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}", file=sys.stderr)


def detect_username():
    # 1. Config override
    cfg = load_config()
    if cfg.get("username"):
        return cfg["username"]

    # 2. Check gh CLI viewer login
    try:
        res = subprocess.run(
            ["gh", "api", "user", "-q", ".login"],
            capture_output=True,
            text=True,
            timeout=4
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass

    # 3. Check git config
    try:
        res = subprocess.run(
            ["git", "config", "--get", "github.user"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass

    return "chivopic"


def fetch_via_gh(username):
    """Fetch contribution calendar via `gh api graphql`."""
    query = """
    query($login: String!) {
      user(login: $login) {
        name
        login
        avatarUrl
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                color
                contributionLevel
                weekday
              }
            }
          }
        }
      }
    }
    """
    try:
        res = subprocess.run(
            ["gh", "api", "graphql", "-F", f"login={username}", "-f", f"query={query}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if res.returncode == 0:
            data = json.loads(res.stdout)
            user_data = data.get("data", {}).get("user")
            if user_data:
                return user_data
    except Exception as e:
        print(f"gh api fetch failed: {e}", file=sys.stderr)
    return None


def fetch_via_public_api(username):
    """Fallback: fetch contribution data via public API."""
    url = f"https://github-contributions-api.jogruber.de/v4/{username}?y=last"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "omarchy-github-heatmap/1.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Public API fetch failed: {e}", file=sys.stderr)
    return None


def parse_gh_data(user_data, username):
    calendar = user_data["contributionsCollection"]["contributionCalendar"]
    total = calendar["totalContributions"]
    weeks_raw = calendar["weeks"]

    all_days = []
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_count = 0

    level_map = {
        "NONE": 0,
        "FIRST_QUARTILE": 1,
        "SECOND_QUARTILE": 2,
        "THIRD_QUARTILE": 3,
        "FOURTH_QUARTILE": 4
    }

    # Format weeks into standard 7-day columns (0=Sun .. 6=Sat)
    formatted_weeks = []
    prev_month = None

    month_names = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]

    for w_idx, week in enumerate(weeks_raw):
        days_in_week = week.get("contributionDays", [])
        grid_days = [None] * 7
        month_label = ""

        for day in days_in_week:
            dt_str = day["date"]
            count = day["contributionCount"]
            wday = day["weekday"]
            lvl_str = day.get("contributionLevel", "NONE")
            lvl = level_map.get(lvl_str, 0)
            is_today = (dt_str == today_str)

            if is_today:
                today_count = count

            day_dict = {
                "date": dt_str,
                "count": count,
                "level": lvl,
                "weekday": wday,
                "color": day.get("color", "#161b22"),
                "isToday": is_today,
                "empty": False
            }
            grid_days[wday] = day_dict
            all_days.append(day_dict)

            # Month label determination
            try:
                d_obj = datetime.strptime(dt_str, "%Y-%m-%d")
                curr_month = d_obj.month
                # If first day of month falls in this week, or this week starts a new month
                if prev_month is None or curr_month != prev_month:
                    if d_obj.day <= 14: # Only label if reasonably early in week
                        month_label = month_names[curr_month - 1]
                    prev_month = curr_month
            except Exception:
                pass

        # Fill missing slots (empty days)
        for i in range(7):
            if grid_days[i] is None:
                grid_days[i] = {
                    "date": "",
                    "count": 0,
                    "level": 0,
                    "weekday": i,
                    "color": "transparent",
                    "isToday": False,
                    "empty": True
                }

        formatted_weeks.append({
            "index": w_idx,
            "monthLabel": month_label,
            "days": grid_days
        })

    # Calculate streaks
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    active_days = 0

    sorted_days = sorted([d for d in all_days if not d["empty"] and d["date"] <= today_str], key=lambda x: x["date"])

    for d in sorted_days:
        if d["count"] > 0:
            active_days += 1
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0

    # Calculate current streak
    # Check backwards from today
    rev_days = list(reversed(sorted_days))
    if rev_days:
        idx = 0
        if rev_days[0]["count"] == 0:
            # If today has 0 commits, check yesterday
            idx = 1
        while idx < len(rev_days) and rev_days[idx]["count"] > 0:
            current_streak += 1
            idx += 1

    return {
        "username": user_data.get("login", username),
        "displayName": user_data.get("name") or user_data.get("login", username),
        "avatarUrl": user_data.get("avatarUrl", f"https://github.com/{username}.png"),
        "totalContributions": total,
        "todayCount": today_count,
        "currentStreak": current_streak,
        "longestStreak": longest_streak,
        "activeDays": active_days,
        "weeks": formatted_weeks,
        "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def parse_public_data(pub_data, username):
    """Parse public API format."""
    total_dict = pub_data.get("total", {})
    total = total_dict.get("lastYear", 0)
    contributions = pub_data.get("contributions", [])
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_count = 0

    month_names = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]

    # Group by week (Sunday to Saturday)
    weeks_dict = {}
    all_days = []

    for item in contributions:
        dt_str = item["date"]
        count = item["count"]
        lvl = item.get("level", 0)
        try:
            d_obj = datetime.strptime(dt_str, "%Y-%m-%d")
            # Python weekday: 0=Mon .. 6=Sun. Convert to 0=Sun .. 6=Sat
            wday = (d_obj.weekday() + 1) % 7
        except Exception:
            wday = 0

        is_today = (dt_str == today_str)
        if is_today:
            today_count = count

        day_dict = {
            "date": dt_str,
            "count": count,
            "level": lvl,
            "weekday": wday,
            "isToday": is_today,
            "empty": False
        }
        all_days.append(day_dict)

    # Calculate streaks
    sorted_days = sorted(all_days, key=lambda x: x["date"])
    longest_streak = 0
    temp_streak = 0
    active_days = 0

    for d in sorted_days:
        if d["count"] > 0:
            active_days += 1
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0

    current_streak = 0
    rev_days = list(reversed(sorted_days))
    if rev_days:
        idx = 0
        if rev_days[0]["count"] == 0:
            idx = 1
        while idx < len(rev_days) and rev_days[idx]["count"] > 0:
            current_streak += 1
            idx += 1

    # Chunk into weeks of 7 days starting from Sunday
    formatted_weeks = []
    if sorted_days:
        first_date = datetime.strptime(sorted_days[0]["date"], "%Y-%m-%d")
        first_wday = (first_date.weekday() + 1) % 7
        
        curr_week_days = [None] * 7
        curr_w_idx = 0
        prev_month = None

        # Fill leading empty days in first week
        for i in range(first_wday):
            curr_week_days[i] = {
                "date": "", "count": 0, "level": 0, "weekday": i,
                "color": "transparent", "isToday": False, "empty": True
            }

        for d in sorted_days:
            wday = d["weekday"]
            curr_week_days[wday] = d
            if wday == 6: # Saturday ends week
                # check month label
                m_label = ""
                for wd in curr_week_days:
                    if wd and not wd["empty"]:
                        m = datetime.strptime(wd["date"], "%Y-%m-%d").month
                        if prev_month is None or m != prev_month:
                            m_label = month_names[m - 1]
                            prev_month = m
                            break
                formatted_weeks.append({
                    "index": curr_w_idx,
                    "monthLabel": m_label,
                    "days": curr_week_days
                })
                curr_w_idx += 1
                curr_week_days = [None] * 7

        # Last partial week
        if any(d is not None for d in curr_week_days):
            for i in range(7):
                if curr_week_days[i] is None:
                    curr_week_days[i] = {
                        "date": "", "count": 0, "level": 0, "weekday": i,
                        "color": "transparent", "isToday": False, "empty": True
                    }
            formatted_weeks.append({
                "index": curr_w_idx,
                "monthLabel": "",
                "days": curr_week_days
            })

    return {
        "username": username,
        "displayName": username,
        "avatarUrl": f"https://github.com/{username}.png",
        "totalContributions": total,
        "todayCount": today_count,
        "currentStreak": current_streak,
        "longestStreak": longest_streak,
        "activeDays": active_days,
        "weeks": formatted_weeks,
        "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def refresh_data(username=None):
    ensure_dirs()
    if not username:
        username = detect_username()

    # Try gh CLI first
    gh_data = fetch_via_gh(username)
    if gh_data:
        parsed = parse_gh_data(gh_data, username)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False)
        return parsed

    # Try public API
    pub_data = fetch_via_public_api(username)
    if pub_data:
        parsed = parse_public_data(pub_data, username)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False)
        return parsed

    # If both failed, return existing cache if present
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "error": "Failed to fetch GitHub contribution data",
        "username": username,
        "totalContributions": 0,
        "todayCount": 0,
        "currentStreak": 0,
        "longestStreak": 0,
        "weeks": []
    }


def get_cached_or_refresh(force=False, username=None):
    ensure_dirs()
    if not username:
        username = detect_username()

    cache_exists = os.path.exists(CACHE_FILE)
    if cache_exists and not force:
        try:
            mtime = os.path.getmtime(CACHE_FILE)
            age = time.time() - mtime
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)

            # If cache matches username, return it
            if cached.get("username") == username:
                # If cache is older than TTL, trigger background refresh
                if age > CACHE_TTL_SECONDS:
                    subprocess.Popen(
                        [sys.executable, __file__, "refresh", username],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                return cached
        except Exception:
            pass

    return refresh_data(username)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "get"
    username = sys.argv[2] if len(sys.argv) > 2 else None

    if cmd == "get":
        data = get_cached_or_refresh(force=False, username=username)
        print(json.dumps(data, ensure_ascii=False))
    elif cmd == "refresh":
        data = refresh_data(username=username)
        print(json.dumps(data, ensure_ascii=False))
    elif cmd == "user":
        cfg = load_config()
        print(cfg.get("username") or detect_username())
    elif cmd == "set-user":
        if username:
            cfg = load_config()
            cfg["username"] = username
            save_config(cfg)
            data = refresh_data(username=username)
            print(json.dumps(data, ensure_ascii=False))
        else:
            print(json.dumps({"error": "Username required"}))
    elif cmd == "clear-cache":
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        print(json.dumps({"status": "cleared"}))
    else:
        data = get_cached_or_refresh(force=False)
        print(json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    main()
