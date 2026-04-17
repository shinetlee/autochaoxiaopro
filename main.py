"""
main.py — 交互式入口（已修改：token 自动从 token.txt 读取）

用法：
    pip install requests pycryptodome
    python main.py
"""

import sys
from api import ChaoxiaoAPI
from flusher import flush_course


# ============================================================
#  token 现在从 token.txt 自动读取（无需修改脚本）
# ============================================================
def load_token() -> str:
    try:
        with open("token.txt", "r", encoding="utf-8") as f:
            token = f.read().strip()
        if not token:
            raise ValueError("token.txt 内容为空")
        return token
    except FileNotFoundError:
        print("❗ 未找到 token.txt 文件！")
        print("   请在当前目录创建 token.txt，并把你的 token 粘贴进去（纯文本，一行即可）")
        sys.exit(1)
    except Exception as e:
        print(f"❗ 读取 token.txt 失败: {e}")
        print("   请检查文件是否存在、是否有读权限、内容是否正确")
        sys.exit(1)


def select_courses(courses: list[dict]) -> list[dict]:
    print("\n" + "=" * 55)
    print("📋 你的课程列表：")
    print("=" * 55)
    for i, c in enumerate(courses, 1):
        progress = c.get("progressPercent", 0)
        watched  = c.get("totalWatchedSeconds", 0)
        total    = c.get("totalDuration", 0)
        tag      = c.get("taskCustomTag", "")
        end_at   = (c.get("courseEndAt") or "")[:10]
        bar      = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
        print(f"  [{i}] {c['name']}  [{tag}]")
        print(f"       {bar} {progress}%  ({watched}/{total} 课时)  截止 {end_at}")
        print()

    while True:
        raw = input(f"请输入课程编号 (1~{len(courses)}，多个用逗号，all=全部): ").strip()
        if raw.lower() == "all":
            return courses
        try:
            indices  = [int(x.strip()) for x in raw.split(",")]
            selected = [courses[i - 1] for i in indices if 1 <= i <= len(courses)]
            if selected:
                return selected
        except (ValueError, IndexError):
            pass
        print("  ❗ 输入有误，请重新输入")


def select_mode() -> tuple[str, float]:
    """
    返回 (mode, speed)：
      mode  = "simulate" | "instant"
      speed = 1.0（正常）| N（倍速，仅 simulate 有效）
    """
    print("\n" + "=" * 55)
    print("⚙️  选择刷课模式：")
    print("  [1] 🕐 正常速度（模拟观看视频的正常速度）")
    print("  [2] 🚀 倍速模式（可自定义 1~3 倍速，若原视频禁止倍速播放，有被检测的风险）")
    print("  [3] ⚡ 立即完成（强制立即完成所有课时，为防止检测，。除非实在来不及，不建议使用该功能。你可能会被导员叫去谈心。）")
    print("=" * 55)
    while True:
        raw = input("请输入模式编号 (1 / 2 / 3): ").strip()
        if raw == "1":
            return "simulate", 1.0
        if raw == "2":
            speed = _input_speed()
            return "simulate", speed
        if raw == "3":
            return "instant", 1.0
        print("  ❗ 请输入 1、2 或 3")


def _input_speed() -> float:
    print("  请输入倍速（1.0~3.0，支持小数，例如 1.5 / 2 / 2.5）：")
    while True:
        raw = input("  倍速：").strip()
        try:
            v = float(raw)
            if 1.0 <= v <= 3.0:
                return v
            print("  ❗ 请输入 1.0~3.0 之间的数字")
        except ValueError:
            print("  ❗ 格式错误，请重新输入")


def main():
    token = load_token()

    print("\n🚀 chaoxiaopro 自动刷课系统")
    print("   正在获取课程列表...")

    try:
        api     = ChaoxiaoAPI(token)
        courses = api.get_courses()
    except RuntimeError as e:
        print(f"❌ 获取课程失败: {e}")
        sys.exit(1)

    if not courses:
        print("❗ 未找到任何课程")
        sys.exit(0)

    selected        = select_courses(courses)
    mode, speed     = select_mode()

    if mode == "instant":
        mode_label = "立即完成"
    elif speed == 1.0:
        mode_label = "正常速度"
    else:
        mode_label = f"{speed:.1f}x 倍速"

    print(f"\n{'='*55}")
    print(f"即将刷以下课程（{mode_label}）：")
    for c in selected:
        print(f"  · {c['name']}  当前进度 {c.get('progressPercent', 0)}%")
    print("=" * 55)
    if input("确认开始？(y/n): ").strip().lower() != "y":
        print("已取消")
        sys.exit(0)

    for course in selected:
        try:
            flush_course(api, course, mode, speed)
        except RuntimeError as e:
            print(f"❌ 刷课出错: {e}")

    print("\n✅ 所有任务完成！")


if __name__ == "__main__":
    main()