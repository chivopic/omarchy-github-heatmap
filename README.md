# Omarchy GitHub Commit Heatmap · GitHub 提交热力图

<p align="center">
  <a href="https://plugins.omarchy.org"><img src="https://img.shields.io/badge/Omarchy-plugin-orange?style=flat-square" alt="Omarchy plugin" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="MIT License" /></a>
  <img src="https://img.shields.io/badge/Version-1.0.0-green?style=flat-square" alt="Version 1.0.0" />
</p>

随时点击 Omarchy 状态栏查看你的 GitHub 贡献热力图与提交打卡记录。为 Omarchy Linux / Hyprland 桌面环境打造的原生 Quickshell 状态栏插件。

A native Quickshell bar widget for Omarchy Linux that lets you click anytime to inspect your GitHub commit heatmap, streak statistics, and contribution history.

---

## ✨ 功能特性 (Features)

- 🟩 **完整 53 周贡献热力图**：展示过去一整年的提交活动矩阵，自适应月份与星期排布。
- 📊 **核心指标统计看板**：
  - 年度总提交次数 (Total Contributions)
  - 当前连续打卡天数 (Current Streak)
  - 历史最长连续打卡天数 (Longest Streak)
  - 今日提交统计 (Today's Commits)
  - 活跃打卡天数 (Active Days)
- 🖱️ **平滑交互与悬浮预览**：
  - 鼠标悬浮任意格子可实时显示具体日期、星期与提交次数。
  - 选中格子高亮微放大反馈。
- 🔄 **离线韧性与双模数据源**：
  - 优先通过 `gh api graphql` 获取完整提交（含私有仓库授权贡献与高精度统计）。
  - 若未安装或未登录 GitHub CLI，自动无缝回退至公开贡献 API 与本地高速缓存。
  - 启动 0 延迟渲染，后台静默自动刷新（15 分钟），不卡顿桌面主线程。
- 🎨 **主题无缝融合**：
  - 支持经典 GitHub 绿（Classic Green）与 Omarchy 当前系统主题强调色（Accent）。
  - 遵循 Omarchy 设计语言（BorderSurface、PopupCard、Nerd Font 图标）。
- 🔌 **全面支持 Shell IPC 与快捷键**：
  - 可通过命令行或 Hyprland 快捷键随时唤出/隐藏热力图面板。

---

## 🚀 操作说明 (Usage)

| 鼠标操作 | 触发效果 |
| :--- | :--- |
| **左键点击 (Left-Click)** | 弹出或隐藏 GitHub 提交热力图看板 (Toggle Heatmap Panel) |
| **中键点击 (Middle-Click)** | 强制从 GitHub 立即同步最新提交数据并弹出通知提醒 |
| **右键点击 (Right-Click)** | 直接在默认浏览器中打开个人 GitHub 主页 (`xdg-open`) |
| **面板内悬浮 (Hover)** | 实时高亮该日期并展示提交详情；右侧展示提交阶梯图例 (Legend) |
| **面板底部按钮** | 一键在浏览器中查看 GitHub 完整个人资料，或点击右上角关闭面板 |

---

## ⌨️ 快捷键与 IPC 远程控制

通过 Omarchy Shell IPC，你可以在终端或 Hyprland 快捷键中直接控制插件：

```bash
# 随时唤出/收起 GitHub 热力图面板
omarchy-shell io.github.chivopic.github-heatmap toggle

# 打开面板
omarchy-shell io.github.chivopic.github-heatmap open

# 关闭面板
omarchy-shell io.github.chivopic.github-heatmap close

# 立即刷新提交记录
omarchy-shell io.github.chivopic.github-heatmap refresh
```

### 绑定到 Hyprland 快捷键

编辑 `~/.config/hypr/bindings.lua`（或 `hyprland.conf`），添加你喜爱的快捷键：

```lua
-- 按 Super + Shift + G 随时唤出 GitHub 热力图
o.bind("SUPER_SHIFT", "G", function()
  hl.exec("omarchy-shell io.github.chivopic.github-heatmap toggle")
end)
```

---

## 🛠️ 安装与配置 (Installation & Configuration)

### 1. 本地安装

插件源码位于 `~/Projects/omarchy-github-heatmap`：

```bash
# 软链接到 Omarchy 用户插件目录
ln -s ~/Projects/omarchy-github-heatmap ~/.config/omarchy/plugins/io.github.chivopic.github-heatmap

# 刷新插件列表并启用
omarchy-shell shell rescanPlugins
omarchy plugin enable io.github.chivopic.github-heatmap right
```

### 2. 账号配置

插件会自动按如下优先级识别当前用户：
1. `~/.config/omarchy-github-heatmap/config.json` 中的 `username`
2. `gh api user -q .login`（GitHub CLI 登录用户）
3. `git config --get github.user`
4. 默认回退用户名 `chivopic`

如需切换为其他用户的热力图，只需运行：

```bash
python3 ~/Projects/omarchy-github-heatmap/backend.py set-user <your-github-username>
omarchy-shell io.github.chivopic.github-heatmap refresh
```

---

## ⚙️ 插件设置项 (Schema Defaults)

在 `~/.config/omarchy/shell.json` 的配置项中支持以下选项：

| 参数 | 类型 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- |
| `showCount` | boolean | `true` | 是否在顶栏图标旁显示提交数字 |
| `countMode` | string | `"today"` | 顶栏显示的数字模式：`"today"`（今日提交）或 `"total"`（年度总计） |
| `colorTheme` | string | `"github"` | 热力图配色方案：`"github"`（经典绿）或 `"accent"`（跟随系统强调色） |

---

## 📄 开源许可 (License)

本项目基于 [MIT](LICENSE) 许可证开源。
