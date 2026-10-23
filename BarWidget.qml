import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Commons as Commons
import qs.Ui

// GitHub Commit Heatmap Bar Widget for Omarchy
// Displays GitHub contribution heatmap and streaks on click.
BarWidget {
  id: root
  moduleName: "io.github.chivopic.github-heatmap"

  readonly property string scriptPath: String(Qt.resolvedUrl("backend.py")).replace(/^file:\/\//, "")
  readonly property bool showCount: setting("showCount", true) === true
  readonly property string countMode: setting("countMode", "today")
  readonly property string colorTheme: setting("colorTheme", "github")

  // State from backend
  property var summary: ({})
  property string username: summary.username || "chivopic"
  property string displayName: summary.displayName || username
  property string avatarUrl: summary.avatarUrl || ("https://github.com/" + username + ".png")
  property int totalContributions: Number(summary.totalContributions || 0)
  property int todayCount: Number(summary.todayCount || 0)
  property int currentStreak: Number(summary.currentStreak || 0)
  property int longestStreak: Number(summary.longestStreak || 0)
  property int activeDays: Number(summary.activeDays || 0)
  property var weeks: summary.weeks || []
  property string updatedAt: summary.updatedAt || ""

  // UI state
  property bool popupOpen: false
  property bool isRefreshing: false
  property var hoveredDay: null

  // GitHub Octocat glyph (Nerd Font)
  readonly property string octoGlyph: "󰊤"

  readonly property string buttonCountText: {
    if (!showCount) return ""
    if (countMode === "total") return " " + totalContributions
    return todayCount > 0 ? " " + todayCount : " " + totalContributions
  }

  readonly property string buttonText: octoGlyph + buttonCountText

  readonly property string tooltipText: "GitHub 贡献热力图 · @" + username +
    "\n今日提交: " + todayCount + " 次 · 连续打卡: " + currentStreak + " 天" +
    "\n年度总计: " + totalContributions + " 次 · 最长连续: " + longestStreak + " 天" +
    "\n左键: 查看热力图 · 中键: 刷新数据 · 右键: 打开 GitHub 主页"

  function close() { popupOpen = false }
  function toggle() { popupOpen = !popupOpen }

  function applyData(raw) {
    isRefreshing = false
    try {
      const parsed = JSON.parse(String(raw || ""))
      if (parsed && typeof parsed === "object" && parsed.username &&
          (typeof parsed.totalContributions === "number" || parsed.error)) {
        summary = parsed
        return !parsed.error && !parsed.stale
      }
    } catch (e) {
      console.warn("github-heatmap: failed to parse backend output: " + e)
    }
    return false
  }

  function handleRefreshResult(raw) {
    const fresh = applyData(raw)
    let detail = ""
    let hasStaleCache = false
    try {
      const parsed = JSON.parse(String(raw || ""))
      if (parsed && parsed.error) detail = parsed.error
      hasStaleCache = !!(parsed && parsed.stale)
    } catch (e) {
      detail = "无法读取后端返回的数据"
    }

    sendRefreshNotification(
      fresh ? "low" : "normal",
      fresh ? "已成功同步 @" + root.username + " 的最新提交记录"
        : "同步失败" + (hasStaleCache ? "，正在显示 @" + root.username + " 的缓存" : "") +
          (detail ? "：" + detail : "")
    )
  }

  function sendRefreshNotification(urgency, message) {
    Quickshell.execDetached([
      "omarchy", "notification", "send",
      "-g", root.octoGlyph, "-u", urgency, "-t", "3500",
      "GitHub 贡献数据", message
    ])
  }

  function fetchStatus() {
    if (!statusProc.running) {
      statusProc.running = true
    }
  }

  function forceRefresh() {
    if (!refreshProc.running) {
      isRefreshing = true
      refreshProc.running = true
    }
  }

  function openGithubProfile() {
    Quickshell.execDetached(["xdg-open", "https://github.com/" + username])
  }

  function getCellColor(level, isThemeAccent) {
    if (isThemeAccent) {
      switch (level) {
        case 1: return Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.25)
        case 2: return Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.50)
        case 3: return Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.75)
        case 4: return Color.accent
        default: return Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.08)
      }
    } else {
      // Classic GitHub dark theme greens
      switch (level) {
        case 1: return "#0e4429"
        case 2: return "#006d32"
        case 3: return "#26a641"
        case 4: return "#39d353"
        default: return Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.08)
      }
    }
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  Component.onCompleted: fetchStatus()

  // Periodic refresh every 15 minutes
  Timer {
    interval: 900000
    running: true
    repeat: true
    onTriggered: root.fetchStatus()
  }

  // Shell IPC target
  IpcHandler {
    target: "io.github.chivopic.github-heatmap"

    function refresh(): void { root.forceRefresh() }
    function open(): void { root.popupOpen = true }
    function close(): void { root.popupOpen = false }
    function toggle(): void { root.popupOpen = !root.popupOpen }
  }

  Process {
    id: statusProc
    command: ["/usr/bin/python3", "-I", root.scriptPath, "get"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: root.applyData(text)
    }
  }

  Process {
    id: refreshProc
    command: ["/usr/bin/python3", "-I", root.scriptPath, "refresh"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        root.handleRefreshResult(text)
      }
    }
  }

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: root.buttonText
    tooltipText: root.tooltipText
    horizontalMargin: 8.5
    onPressed: function(mouseButton) {
      if (mouseButton === Qt.LeftButton) {
        root.popupOpen = !root.popupOpen
      } else if (mouseButton === Qt.MiddleButton) {
        root.forceRefresh()
      } else if (mouseButton === Qt.RightButton) {
        root.openGithubProfile()
      }
    }
  }

  PopupCard {
    id: popup
    anchorItem: root
    bar: root.bar
    owner: root
    open: root.popupOpen
    contentWidth: popup.fittedContentWidth(Style.space(745))
    contentHeight: popup.fittedContentHeight(cardColumn.implicitHeight)

    Column {
      id: cardColumn
      anchors.fill: parent
      spacing: Style.space(12)

      // 1. Header: User Info & Stat Badges
      Item {
        width: parent.width
        height: Style.space(42)
        implicitHeight: height
        // User Avatar & Name
        Row {
          anchors.left: parent.left
          anchors.verticalCenter: parent.verticalCenter
          spacing: Style.space(10)
          Rectangle {
            width: Style.space(36)
            height: Style.space(36)
            radius: Style.space(18)
            color: Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.1)
            clip: true

            Image {
              anchors.fill: parent
              source: root.avatarUrl
              fillMode: Image.PreserveAspectCrop
              smooth: true
              visible: status === Image.Ready
            }

            Text {
              anchors.centerIn: parent
              visible: !avatarUrl || parent.children[0].status !== Image.Ready
              text: "󰊤"
              color: Color.accent
              font.family: Style.font.family
              font.pixelSize: Style.font.heading
            }
          }

          Column {
            anchors.verticalCenter: parent.verticalCenter
            spacing: 1

            Row {
              spacing: Style.space(6)
              Text {
                id: profileNameText
                text: root.displayName
                textFormat: Text.PlainText
                color: Color.foreground
                font.family: Style.font.family
                font.pixelSize: Style.font.title
                font.bold: true
              }
              Text {
                id: profileUsernameText
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 1
                text: "@" + root.username
                textFormat: Text.PlainText
                color: Color.muted
                font.family: Style.font.family
                font.pixelSize: Style.font.caption
              }
            }

            Text {
              text: "GitHub 提交活动看板"
              color: Color.muted
              font.family: Style.font.family
              font.pixelSize: Style.font.caption
            }
          }
        }

        // Stats Badges
        Row {
          anchors.right: parent.right
          anchors.verticalCenter: parent.verticalCenter
          spacing: Style.space(6)

          Repeater {
            model: [
              { label: "年度提交", value: root.totalContributions, unit: "次" },
              { label: "当前连续", value: root.currentStreak, unit: "天" },
              { label: "最长连续", value: root.longestStreak, unit: "天" },
              { label: "今日提交", value: root.todayCount, unit: "次" }
            ]

            delegate: Rectangle {
              required property var modelData
              width: Style.space(72)
              height: Style.space(38)
              radius: Style.space(6)
              color: Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.05)
              border.width: 1
              border.color: Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.08)

              Column {
                anchors.centerIn: parent
                spacing: 0

                Row {
                  anchors.horizontalCenter: parent.horizontalCenter
                  spacing: 1
                  Text {
                    text: modelData.value
                    color: Color.accent
                    font.family: Style.font.family
                    font.pixelSize: Style.font.body
                    font.bold: true
                  }
                  Text {
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 1
                    text: modelData.unit
                    color: Color.muted
                    font.family: Style.font.family
                    font.pixelSize: 8
                  }
                }

                Text {
                  anchors.horizontalCenter: parent.horizontalCenter
                  text: modelData.label
                  color: Color.muted
                  font.family: Style.font.family
                  font.pixelSize: Style.font.caption - 1
                }
              }
            }
          }

          // Refresh Button
          Rectangle {
            width: Style.space(38)
            height: Style.space(38)
            radius: Style.space(6)
            color: refreshHover.hovered ? Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.12)
                                       : Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.05)
            border.width: 1
            border.color: Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.08)

            Text {
              id: refreshIcon
              anchors.centerIn: parent
              text: "󰑐"
              color: root.isRefreshing ? Color.accent : Color.foreground
              font.family: Style.font.family
              font.pixelSize: Style.font.title
              rotation: root.isRefreshing ? 360 : 0

              Behavior on rotation {
                NumberAnimation { duration: 800; loops: Animation.Infinite }
              }
            }

            HoverHandler { id: refreshHover }

            MouseArea {
              anchors.fill: parent
              cursorShape: Qt.PointingHandCursor
              onClicked: root.forceRefresh()
            }
          }
        }
      }

      // Separator Line
      Rectangle {
        width: parent.width
        height: 1
        color: Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.08)
      }

      // 2. Heatmap Grid Area
      Item {
        width: parent.width
        height: Style.space(120)
        implicitHeight: height

        // Month Labels Header
        Row {
          id: monthLabelsRow
          anchors.left: gridContainer.left
          anchors.leftMargin: Style.space(24)
          anchors.top: parent.top
          spacing: Style.space(3)
          Repeater {
            model: root.weeks

            delegate: Item {
              required property var modelData
              width: Style.space(10)
              height: Style.space(14)

              Text {
                text: modelData.monthLabel || ""
                color: Color.muted
                font.family: Style.font.family
                font.pixelSize: 9
                visible: text !== ""
              }
            }
          }
        }

        // Main Grid with Weekdays on left
        Row {
          id: gridContainer
          anchors.top: monthLabelsRow.bottom
          anchors.topMargin: Style.space(4)
          anchors.horizontalCenter: parent.horizontalCenter
          spacing: Style.space(4)

          // Left Weekday Labels Column
          Column {
            width: Style.space(20)
            spacing: Style.space(3)

            Repeater {
              model: [
                { name: "", show: false },
                { name: "一", show: true },
                { name: "", show: false },
                { name: "三", show: true },
                { name: "", show: false },
                { name: "五", show: true },
                { name: "", show: false }
              ]

              delegate: Item {
                required property var modelData
                width: Style.space(20)
                height: Style.space(10)

                Text {
                  anchors.right: parent.right
                  anchors.rightMargin: Style.space(4)
                  anchors.verticalCenter: parent.verticalCenter
                  text: modelData.show ? modelData.name : ""
                  color: Color.muted
                  font.family: Style.font.family
                  font.pixelSize: 8
                }
              }
            }
          }

          // 53 Columns of Weeks
          Row {
            id: weeksRow
            spacing: Style.space(3)
            Repeater {
              model: root.weeks

              delegate: Column {
                required property var modelData
                spacing: Style.space(3)

                Repeater {
                  model: modelData.days

                  delegate: Rectangle {
                    required property var modelData
                    readonly property bool isEmpty: modelData.empty === true
                    readonly property bool isToday: modelData.isToday === true
                    readonly property bool isHovered: root.hoveredDay && root.hoveredDay.date === modelData.date && !isEmpty

                    width: Style.space(10)
                    height: Style.space(10)
                    radius: Style.space(2)
                    color: isEmpty ? "transparent" : root.getCellColor(modelData.level, root.colorTheme === "accent")
                    border.width: isHovered ? 1.5 : (isToday ? 1 : 0)
                    border.color: isHovered ? Color.foreground : (isToday ? Color.accent : "transparent")

                    // Scale up on hover
                    scale: isHovered ? 1.35 : 1.0
                    z: isHovered ? 10 : 1

                    Behavior on scale {
                      NumberAnimation { duration: 100 }
                    }

                    MouseArea {
                      anchors.fill: parent
                      enabled: !isEmpty
                      hoverEnabled: true
                      cursorShape: Qt.PointingHandCursor

                      onEntered: {
                        root.hoveredDay = modelData
                      }
                      onExited: {
                        if (root.hoveredDay && root.hoveredDay.date === modelData.date) {
                          root.hoveredDay = null
                        }
                      }
                      onClicked: {
                        root.openGithubProfile()
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }

      // 3. Bottom Information & Legend Bar
      Item {
        width: parent.width
        height: Style.space(24)
        implicitHeight: height
        // Cell hover detail text or summary
        Row {
          anchors.left: parent.left
          anchors.verticalCenter: parent.verticalCenter
          spacing: Style.space(6)

          Text {
            anchors.verticalCenter: parent.verticalCenter
            text: {
              if (root.hoveredDay) {
                var dStr = root.hoveredDay.date
                var count = root.hoveredDay.count
                var countStr = count > 0 ? (count + " 次提交贡献") : "当天无提交记录"
                return dStr + " · " + countStr + (root.hoveredDay.isToday ? " (今天)" : "")
              }
              return "过去一年提交共 " + root.totalContributions + " 次 · 活跃天数 " + root.activeDays + " 天"
            }
            color: root.hoveredDay ? Color.accent : Color.foreground
            font.family: Style.font.family
            font.pixelSize: Style.font.caption
            font.bold: root.hoveredDay !== null
          }
        }

        // Legend: Less [][][][][] More
        Row {
          anchors.right: parent.right
          anchors.verticalCenter: parent.verticalCenter
          spacing: Style.space(4)

          Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "少"
            color: Color.muted
            font.family: Style.font.family
            font.pixelSize: Style.font.caption - 1
          }

          Repeater {
            model: [0, 1, 2, 3, 4]

            delegate: Rectangle {
              required property int modelData
              width: Style.space(10)
              height: Style.space(10)
              radius: Style.space(2)
              color: root.getCellColor(modelData, root.colorTheme === "accent")
            }
          }

          Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "多"
            color: Color.muted
            font.family: Style.font.family
            font.pixelSize: Style.font.caption - 1
          }
        }
      }

      // 4. Footer: Actions & Shortcuts
      Item {
        width: parent.width
        height: Style.space(28)
        implicitHeight: height
        // Open in Browser Link Button
        Rectangle {
          anchors.left: parent.left
          anchors.verticalCenter: parent.verticalCenter
          height: Style.space(26)
          width: openBtnContent.implicitWidth + Style.space(16)
          radius: Style.space(6)
          color: openBtnHover.hovered ? Qt.rgba(Color.accent.r, Color.accent.g, Color.accent.b, 0.15)
                                     : Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.05)
          border.width: 1
          border.color: openBtnHover.hovered ? Color.accent
                                            : Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.08)

          Row {
            id: openBtnContent
            anchors.centerIn: parent
            spacing: Style.space(6)

            Text {
              anchors.verticalCenter: parent.verticalCenter
              text: ""
              color: openBtnHover.hovered ? Color.accent : Color.foreground
              font.family: Style.font.family
              font.pixelSize: Style.font.body
            }

            Text {
              anchors.verticalCenter: parent.verticalCenter
              text: "在浏览器中查看 GitHub 主页"
              color: openBtnHover.hovered ? Color.accent : Color.foreground
              font.family: Style.font.family
              font.pixelSize: Style.font.caption
            }
          }

          HoverHandler { id: openBtnHover }

          MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: {
              root.openGithubProfile()
              root.close()
            }
          }
        }

        // Updated time on right
        Row {
          anchors.right: parent.right
          anchors.verticalCenter: parent.verticalCenter
          spacing: Style.space(8)

          Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.updatedAt ? ("上次更新: " + root.updatedAt) : ""
            color: Color.muted
            font.family: Style.font.family
            font.pixelSize: Style.font.caption - 1
          }

          // Close button
          Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            width: Style.space(22)
            height: Style.space(22)
            radius: Style.space(4)
            color: closeHover.hovered ? Qt.rgba(Color.foreground.r, Color.foreground.g, Color.foreground.b, 0.1) : "transparent"

            Text {
              anchors.centerIn: parent
              text: "✕"
              color: Color.muted
              font.family: Style.font.family
              font.pixelSize: Style.font.caption
            }

            HoverHandler { id: closeHover }

            MouseArea {
              anchors.fill: parent
              cursorShape: Qt.PointingHandCursor
              onClicked: root.close()
            }
          }
        }
      }
    }
  }
}
