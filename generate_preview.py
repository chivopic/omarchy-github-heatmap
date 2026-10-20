#!/usr/bin/env python3
"""
Generate pixel-perfect high-resolution preview and icon assets for omarchy-github-heatmap.
"""

import os
import json
import base64
import subprocess

PROJECT_DIR = "/home/chiv/Projects/omarchy-github-heatmap"
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets")
CACHE_FILE = os.path.expanduser("~/.cache/omarchy-github-heatmap/heatmap_data.json")

os.makedirs(ASSETS_DIR, exist_ok=True)

with open(CACHE_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

avatar_path = os.path.join(ASSETS_DIR, "avatar.png")
with open(avatar_path, "rb") as f:
    avatar_b64 = base64.b64encode(f.read()).decode("utf-8")
avatar_uri = f"data:image/jpeg;base64,{avatar_b64}"

username = data.get("username", "chivopic")
display_name = data.get("displayName", "Zehong Chen")
total = data.get("totalContributions", 558)
today = data.get("todayCount", 20)
current_streak = data.get("currentStreak", 5)
longest_streak = data.get("longestStreak", 15)
active_days = data.get("activeDays", 114)
weeks = data.get("weeks", [])
updated_at = data.get("updatedAt", "2026-10-20 21:00:00")

# 1. Generate preview.svg
W, H = 1600, 920

svg_parts = []
svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&amp;display=swap');
    text {{ font-family: 'JetBrainsMono Nerd Font', 'Noto Sans CJK SC', 'Noto Sans', sans-serif; }}
    .title {{ font-size: 15px; font-weight: 700; fill: #f0f6fc; }}
    .sub {{ font-size: 11px; fill: #8b949e; }}
    .label {{ font-size: 10px; fill: #8b949e; }}
    .val {{ font-size: 14px; font-weight: 700; fill: #58a6ff; }}
    .unit {{ font-size: 9px; fill: #8b949e; }}
  </style>

  <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#090d13" />
    <stop offset="50%" stop-color="#0d1117" />
    <stop offset="100%" stop-color="#161b22" />
  </linearGradient>

  <linearGradient id="glow" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="#238636" stop-opacity="0.25" />
    <stop offset="100%" stop-color="#238636" stop-opacity="0.0" />
  </linearGradient>

  <filter id="cardShadow" x="-10%" y="-10%" width="120%" height="125%">
    <feDropShadow dx="0" dy="16" stdDeviation="24" flood-color="#000000" flood-opacity="0.65" />
    <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000000" flood-opacity="0.4" />
  </filter>

  <filter id="hoverGlow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="#39d353" flood-opacity="0.8" />
  </filter>

  <clipPath id="avatarClip">
    <circle cx="20" cy="20" r="19" />
  </clipPath>
</defs>

<!-- Background -->
<rect width="{W}" height="{H}" fill="url(#bgGrad)" />

<!-- Background ambient grid pattern -->
<g opacity="0.06">
''')

for x in range(0, W, 40):
    svg_parts.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="#ffffff" stroke-width="1" />')
for y in range(0, H, 40):
    svg_parts.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#ffffff" stroke-width="1" />')

svg_parts.append('''</g>

<!-- Top bar mock -->
<g transform="translate(150, 40)">
  <rect width="1300" height="42" rx="10" fill="#161b22" stroke="#30363d" stroke-width="1" />
  
  <!-- Left items -->
  <text x="20" y="26" font-size="14" fill="#f0f6fc">󰣇</text>
  <text x="45" y="26" font-size="12" fill="#8b949e">Omarchy</text>

  <!-- Right items -->
  <g transform="translate(930, 0)">
    <!-- Tray / Status icons -->
    <text x="20" y="26" font-size="13" fill="#8b949e">󰍛 280Hz</text>
    <text x="100" y="26" font-size="13" fill="#8b949e">󰤨</text>
    <text x="130" y="26" font-size="13" fill="#8b949e">󰂯</text>
    <text x="160" y="26" font-size="13" fill="#8b949e">󰕾</text>

    <!-- Heatmap Bar Widget Pill (Active Highlighted) -->
    <g transform="translate(195, 6)">
      <rect width="90" height="30" rx="6" fill="#21262d" stroke="#58a6ff" stroke-width="1.5" />
      <text x="16" y="20" font-size="14" fill="#39d353">󰊤</text>
      <text x="36" y="20" font-size="12" font-weight="700" fill="#f0f6fc">''' + str(today) + '''</text>
      <!-- Small active dot underneath -->
      <circle cx="45" cy="34" r="2.5" fill="#58a6ff" />
    </g>

    <!-- Next icon (Muyu) -->
    <text x="305" y="26" font-size="14" fill="#8b949e">🪷</text>
    <text x="335" y="26" font-size="13" fill="#8b949e">21:00</text>
  </g>
</g>
''')

# Card Position
CX, CY = 320, 115
CW, CH = 960, 420

svg_parts.append(f'''
<!-- PopupCard Container -->
<g transform="translate({CX}, {CY})" filter="url(#cardShadow)">
  <!-- Card Background -->
  <rect width="{CW}" height="{CH}" rx="14" fill="#12161c" stroke="#30363d" stroke-width="1.5" />
  
  <!-- Subtle header aura -->
  <rect x="1" y="1" width="{CW-2}" height="100" rx="14" fill="url(#glow)" />

  <!-- 1. Header Row -->
  <g transform="translate(26, 24)">
    <!-- Avatar -->
    <g transform="translate(0, 0)">
      <circle cx="22" cy="22" r="22" fill="#21262d" stroke="#30363d" stroke-width="1" />
      <g transform="translate(2, 2)">
        <image href="{avatar_uri}" width="40" height="40" clip-path="url(#avatarClip)" />
      </g>
    </g>

    <!-- Name & Handle -->
    <g transform="translate(56, 12)">
      <text x="0" y="12" class="title">{display_name}</text>
      <text x="105" y="12" class="sub">@{username}</text>
      <text x="0" y="28" class="sub">GitHub 提交活动看板 · 实时同步</text>
    </g>

    <!-- Stats Badges (Right side) -->
    <g transform="translate(420, 2)">
      <!-- Total -->
      <g transform="translate(0, 0)">
        <rect width="105" height="44" rx="8" fill="#1c2128" stroke="#30363d" stroke-width="1" />
        <text x="12" y="22" class="val">{total}</text>
        <text x="56" y="22" class="unit">次</text>
        <text x="12" y="36" class="label">年度总提交</text>
      </g>

      <!-- Current Streak -->
      <g transform="translate(115, 0)">
        <rect width="105" height="44" rx="8" fill="#1c2128" stroke="#30363d" stroke-width="1" />
        <text x="12" y="22" class="val" fill="#39d353">{current_streak}</text>
        <text x="32" y="22" class="unit">天</text>
        <text x="12" y="36" class="label">当前连续</text>
      </g>

      <!-- Longest Streak -->
      <g transform="translate(230, 0)">
        <rect width="105" height="44" rx="8" fill="#1c2128" stroke="#30363d" stroke-width="1" />
        <text x="12" y="22" class="val">{longest_streak}</text>
        <text x="40" y="22" class="unit">天</text>
        <text x="12" y="36" class="label">最长连续</text>
      </g>

      <!-- Today -->
      <g transform="translate(345, 0)">
        <rect width="90" height="44" rx="8" fill="#1c2128" stroke="#30363d" stroke-width="1" />
        <text x="12" y="22" class="val" fill="#39d353">{today}</text>
        <text x="36" y="22" class="unit">次</text>
        <text x="12" y="36" class="label">今日提交</text>
      </g>

      <!-- Refresh button -->
      <g transform="translate(445, 0)">
        <rect width="44" height="44" rx="8" fill="#1c2128" stroke="#30363d" stroke-width="1" />
        <text x="14" y="27" font-size="16" fill="#8b949e">󰑐</text>
      </g>
    </g>
  </g>

  <!-- Divider -->
  <line x1="26" y1="92" x2="{CW-26}" y2="92" stroke="#21262d" stroke-width="1" />

  <!-- 2. Heatmap Section -->
  <g transform="translate(32, 115)">
    <!-- Month labels -->
    <g transform="translate(36, 0)">
''')

color_levels = {
    0: "rgba(255, 255, 255, 0.05)",
    1: "#0e4429",
    2: "#006d32",
    3: "#26a641",
    4: "#39d353"
}

cell_size = 13
cell_gap = 3.5
step = cell_size + cell_gap

for w in weeks:
    idx = w["index"]
    m_label = w.get("monthLabel", "")
    if m_label:
        x_pos = idx * step
        svg_parts.append(f'<text x="{x_pos}" y="0" font-size="11" fill="#8b949e">{m_label}</text>')

svg_parts.append('''    </g>

    <!-- Grid Container -->
    <g transform="translate(0, 16)">
      <!-- Weekday Labels -->
      <text x="6" y="28" font-size="10" fill="#8b949e">一</text>
      <text x="6" y="62" font-size="10" fill="#8b949e">三</text>
      <text x="6" y="96" font-size="10" fill="#8b949e">五</text>

      <!-- Weeks matrix -->
      <g transform="translate(36, 0)">
''')

# Render 53 columns
for w in weeks:
    w_idx = w["index"]
    x = w_idx * step
    days = w["days"]
    for day in days:
        wday = day["weekday"]
        y = wday * step
        if day["empty"]:
            continue
        lvl = day.get("level", 0)
        c = color_levels.get(lvl, color_levels[0])
        is_today = day.get("isToday", False)

        if is_today:
            # Highlight today's active cell
            svg_parts.append(f'''
        <rect x="{x-1.5}" y="{y-1.5}" width="{cell_size+3}" height="{cell_size+3}" rx="3.5" fill="{c}" stroke="#ffffff" stroke-width="1.8" filter="url(#hoverGlow)" />
            ''')
        else:
            svg_parts.append(f'''
        <rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="2.5" fill="{c}" />
            ''')

svg_parts.append(f'''      </g>
    </g>
  </g>

  <!-- 3. Bottom Information & Legend Bar -->
  <g transform="translate(32, 280)">
    <!-- Hover / Status info -->
    <text x="36" y="14" font-size="12" font-weight="700" fill="#39d353">2026-10-20 (今天) · 20 次提交贡献 · 保持连胜中 🔥</text>

    <!-- Legend -->
    <g transform="translate(680, 0)">
      <text x="0" y="14" font-size="11" fill="#8b949e">少</text>
      <rect x="22" y="2" width="13" height="13" rx="2.5" fill="{color_levels[0]}" />
      <rect x="39" y="2" width="13" height="13" rx="2.5" fill="{color_levels[1]}" />
      <rect x="56" y="2" width="13" height="13" rx="2.5" fill="{color_levels[2]}" />
      <rect x="73" y="2" width="13" height="13" rx="2.5" fill="{color_levels[3]}" />
      <rect x="90" y="2" width="13" height="13" rx="2.5" fill="{color_levels[4]}" />
      <text x="110" y="14" font-size="11" fill="#8b949e">多</text>
    </g>
  </g>

  <!-- Divider -->
  <line x1="26" y1="316" x2="{CW-26}" y2="316" stroke="#21262d" stroke-width="1" />

  <!-- 4. Footer Actions Bar -->
  <g transform="translate(32, 336)">
    <!-- GitHub Profile Button -->
    <g transform="translate(36, 0)">
      <rect width="240" height="34" rx="7" fill="#21262d" stroke="#30363d" stroke-width="1" />
      <text x="18" y="22" font-size="15" fill="#f0f6fc"></text>
      <text x="42" y="21" font-size="12" font-weight="600" fill="#f0f6fc">在浏览器中查看 GitHub 主页</text>
    </g>

    <!-- Active Days Badge -->
    <g transform="translate(290, 0)">
      <rect width="160" height="34" rx="7" fill="#161b22" stroke="#21262d" stroke-width="1" />
      <text x="14" y="21" font-size="12" fill="#8b949e">年度活跃天数: <tspan fill="#f0f6fc" font-weight="600">{active_days} 天</tspan></text>
    </g>

    <!-- Updated timestamp -->
    <text x="{CW-70}" y="22" text-anchor="end" font-size="11" fill="#8b949e">上次同步: {updated_at}</text>
  </g>
</g>
</svg>
''')

svg_content = "\n".join(svg_parts)
svg_path = os.path.join(ASSETS_DIR, "preview.svg")
with open(svg_path, "w", encoding="utf-8") as f:
    f.write(svg_content)

preview_png = os.path.join(ASSETS_DIR, "preview.png")
subprocess.run(["magick", svg_path, preview_png], check=True)
print(f"Generated {preview_png}")

# 2. Generate icon.png (512x512)
icon_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
<defs>
  <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#0d1117" />
    <stop offset="100%" stop-color="#161b22" />
  </linearGradient>
  <filter id="shadow">
    <feDropShadow dx="0" dy="8" stdDeviation="16" flood-color="#000000" flood-opacity="0.5" />
  </filter>
</defs>
<rect width="512" height="512" rx="112" fill="url(#bg)" stroke="#30363d" stroke-width="6" />

<!-- 4x4 Mini Contribution Heatmap Matrix in center -->
<g transform="translate(106, 106)" filter="url(#shadow)">
  <rect x="0" y="0" width="65" height="65" rx="14" fill="#0e4429" />
  <rect x="78" y="0" width="65" height="65" rx="14" fill="#006d32" />
  <rect x="156" y="0" width="65" height="65" rx="14" fill="#26a641" />
  <rect x="234" y="0" width="65" height="65" rx="14" fill="#39d353" />

  <rect x="0" y="78" width="65" height="65" rx="14" fill="#006d32" />
  <rect x="78" y="78" width="65" height="65" rx="14" fill="#26a641" />
  <rect x="156" y="78" width="65" height="65" rx="14" fill="#39d353" />
  <rect x="234" y="78" width="65" height="65" rx="14" fill="#26a641" />

  <rect x="0" y="156" width="65" height="65" rx="14" fill="#26a641" />
  <rect x="78" y="156" width="65" height="65" rx="14" fill="#39d353" />
  <rect x="156" y="156" width="65" height="65" rx="14" fill="#0e4429" />
  <rect x="234" y="156" width="65" height="65" rx="14" fill="#006d32" />

  <rect x="0" y="234" width="65" height="65" rx="14" fill="#39d353" />
  <rect x="78" y="234" width="65" height="65" rx="14" fill="#0e4429" />
  <rect x="156" y="234" width="65" height="65" rx="14" fill="#006d32" />
  <rect x="234" y="234" width="65" height="65" rx="14" fill="#39d353" />
</g>

<!-- Octocat Icon in center foreground -->
<circle cx="256" cy="256" r="82" fill="#0d1117" stroke="#39d353" stroke-width="4" filter="url(#shadow)" />
<path d="M256 196c-33.1 0-60 26.9-60 60 0 26.5 17.2 49 41 56.9 3 .6 4.1-1.3 4.1-2.9 0-1.4-.1-6.1-.1-11-16.7 3.6-20.2-7.1-20.2-7.1-2.7-6.9-6.6-8.8-6.6-8.8-5.5-3.7.4-3.6.4-3.6 6 .4 9.2 6.2 9.2 6.2 5.4 9.2 14.1 6.5 17.5 5 0.5-3.9 2.1-6.5 3.8-8-13.3-1.5-27.3-6.7-27.3-29.7 0-6.6 2.3-11.9 6.2-16.1-.6-1.5-2.7-7.6.6-15.9 0 0 5-1.6 16.5 6.1 4.8-1.3 9.9-2 15-2 5.1 0 10.2.7 15 2 11.5-7.8 16.5-6.1 16.5-6.1 3.3 8.3 1.2 14.4.6 15.9 3.8 4.1 6.2 9.5 6.2 16.1 0 23.1-14 28.1-27.4 29.6 2.2 1.9 4.1 5.6 4.1 11.3 0 8.2-.1 14.7-.1 16.7 0 1.6 1.1 3.5 4.1 2.9 23.8-7.9 41-30.4 41-56.9 0-33.1-26.9-60-60-60z" fill="#f0f6fc"/>
</svg>
'''
icon_svg_path = os.path.join(ASSETS_DIR, "icon.svg")
with open(icon_svg_path, "w", encoding="utf-8") as f:
    f.write(icon_svg)

icon_png = os.path.join(ASSETS_DIR, "icon.png")
subprocess.run(["magick", icon_svg_path, icon_png], check=True)
print(f"Generated {icon_png}")
