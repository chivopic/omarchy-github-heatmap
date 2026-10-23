#!/usr/bin/env python3
"""Run isolated QtQuick checks built from the production QML sinks/handlers."""

import os
import re
import subprocess
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
WIDGET = REPO / "BarWidget.qml"


def extract_function(source, name):
    match = re.search(rf"^  function {re.escape(name)}\([^\n]*\) \{{", source, re.M)
    if not match:
        raise AssertionError(f"Could not find production function {name}")
    start = source.index("{", match.start())
    depth = 0
    quote = None
    escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ('"', "'", "`"):
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[match.start():index + 1]
    raise AssertionError(f"Unclosed production function {name}")


def extract_text_properties(source, element_id):
    marker = f"id: {element_id}"
    marker_index = source.index(marker)
    start = source.rfind("Text {", 0, marker_index)
    if start < 0:
        raise AssertionError(f"Could not find production Text for {element_id}")
    depth = 0
    end = None
    for index in range(source.index("{", start), len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if end is None:
        raise AssertionError(f"Unclosed production Text for {element_id}")
    block = source[start:end]
    text = re.search(r"^\s*text:\s*(.+)$", block, re.M)
    text_format = re.search(r"^\s*textFormat:\s*(.+)$", block, re.M)
    if not text or not text_format:
        raise AssertionError(f"Production Text {element_id} must define text and textFormat")
    return text.group(1).strip(), text_format.group(1).strip()


def main():
    source = WIDGET.read_text(encoding="utf-8")
    display_text, display_format = extract_text_properties(source, "profileNameText")
    username_text, username_format = extract_text_properties(source, "profileUsernameText")
    username_property = re.search(r"^  property string username: (.+)$", source, re.M).group(1)
    display_property = re.search(r"^  property string displayName: (.+)$", source, re.M).group(1)
    apply_data = extract_function(source, "applyData")
    handle_result = extract_function(source, "handleRefreshResult")

    qml = f'''import QtQuick
import QtQuick.Window

Window {{
  id: window
  width: 1060
  height: 250
  visible: true
  color: "#171b24"

  QtObject {{
    id: root
    property var summary: ({{}})
    property string username: {username_property}
    property string displayName: {display_property}
    property bool isRefreshing: true
    property string octoGlyph: "octocat"
    property var notification: ({{}})

    {apply_data}

    {handle_result}

    function sendRefreshNotification(urgency, message) {{
      notification = {{ "urgency": urgency, "message": message }}
    }}
  }}

  Column {{
    anchors.fill: parent
    anchors.margins: 28
    spacing: 16

    Text {{
      color: "#f3f4f6"
      font.family: "monospace"
      font.pixelSize: 18
      text: "Production Text sinks and refresh-result handler"
      textFormat: Text.PlainText
    }}

    Text {{
      id: profileNameText
      color: "#86efac"
      font.family: "monospace"
      font.pixelSize: 20
      text: {display_text}
      textFormat: {display_format}
    }}

    Text {{
      id: profileUsernameText
      color: "#93c5fd"
      font.family: "monospace"
      font.pixelSize: 18
      text: {username_text}
      textFormat: {username_format}
    }}
  }}

  Timer {{
    interval: 100
    running: true
    repeat: false
    onTriggered: {{
      root.summary = {{ "displayName": "<img src='file:///tmp/nonexistent-heatmap-image.png'>", "username": "<img src='file:///tmp/nonexistent-heatmap-image.png'>" }}
      if (profileNameText.textFormat !== Text.PlainText || profileNameText.text !== root.displayName ||
          profileUsernameText.textFormat !== Text.PlainText ||
          profileUsernameText.text !== "@<img src='file:///tmp/nonexistent-heatmap-image.png'>") {{
        console.error("PlainText img/login case failed")
        Qt.exit(1)
        return
      }}
      root.summary = {{ "displayName": "<b>Unicode 名字 Δ</b>", "username": "<b>login</b>" }}
      if (profileNameText.text !== "<b>Unicode 名字 Δ</b>" || profileUsernameText.text !== "@<b>login</b>") {{
        console.error("PlainText b/Unicode case failed")
        Qt.exit(1)
        return
      }}
      root.summary = {{ "displayName": "陈 Zehong", "username": "octocat" }}
      if (profileNameText.text !== "陈 Zehong" || profileUsernameText.text !== "@octocat") {{
        console.error("PlainText ordinary Unicode case failed")
        Qt.exit(1)
        return
      }}

      root.handleRefreshResult(JSON.stringify({{
        "username": "octocat", "displayName": "Octocat", "totalContributions": 9, "weeks": []
      }}))
      if (root.notification.urgency !== "low" || !root.notification.message.includes("成功同步") ||
          root.summary.totalContributions !== 9) {{
        console.error("Fresh refresh result was not reported as success")
        Qt.exit(1)
        return
      }}

      root.handleRefreshResult(JSON.stringify({{
        "username": "octocat", "displayName": "Octocat", "totalContributions": 123, "weeks": [],
        "stale": true, "error": "fetch failed; showing cached data"
      }}))
      if (root.notification.urgency !== "normal" || !root.notification.message.includes("同步失败") ||
          !root.notification.message.includes("缓存") || root.summary.totalContributions !== 123) {{
        console.error("Stale refresh result was not reported as a cache fallback")
        Qt.exit(1)
        return
      }}

      root.handleRefreshResult(JSON.stringify({{
        "username": "bob", "stale": false, "error": "Failed to fetch GitHub contribution data"
      }}))
      if (root.notification.urgency !== "normal" || !root.notification.message.includes("同步失败") ||
          root.notification.message.includes("缓存") || root.summary.username !== "bob") {{
        console.error("Error refresh result was not reported without a stale-cache claim")
        Qt.exit(1)
        return
      }}

      root.handleRefreshResult("invalid JSON")
      if (!root.notification.message.includes("无法读取后端返回的数据") ||
          root.notification.message.includes("成功同步")) {{
        console.error("Malformed refresh result was reported incorrectly")
        Qt.exit(1)
        return
      }}

      console.log("QtQuick source harness passed: actual BarWidget Text bindings keep img/b markup literal and Unicode labels readable")
      console.log("QtQuick source harness passed: fresh, stale-cache, backend-error, and malformed refresh outcomes")
      Qt.quit()
    }}
  }}
}}
'''

    with tempfile.TemporaryDirectory(prefix="heatmap-qml-") as temp:
        temp_path = Path(temp)
        runtime = temp_path / "runtime"
        runtime.mkdir(mode=0o700)
        qml_path = temp_path / "harness.qml"
        qml_path.write_text(qml, encoding="utf-8")
        env = os.environ.copy()
        env["QT_QPA_PLATFORM"] = "offscreen"
        env["XDG_RUNTIME_DIR"] = str(runtime)
        try:
            result = subprocess.run(
                ["quickshell", "--path", str(qml_path)],
                cwd=REPO,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=20,
            )
        except subprocess.TimeoutExpired as error:
            output = error.stdout or b""
            print(output.decode("utf-8", errors="replace"), end="")
            raise SystemExit("QtQuick source harness timed out") from error
    print(result.stdout, end="")
    if result.returncode != 0 or "QtQuick source harness passed" not in result.stdout:
        raise SystemExit(result.returncode or 1)


if __name__ == "__main__":
    main()
