import time
import random
from api import ChaoxiaoAPI
from quiz_solver import solve_quiz


def _rand_step() -> int:
    """随机取本轮上报的视频秒数（110~130s）"""
    return random.randint(110, 130)


def flush_course(api: ChaoxiaoAPI, course: dict, mode: str, speed: float = 1.0):
    course_id   = course["id"]
    task_id     = course["taskId"]
    course_name = course["name"]

    if mode == "instant":
        mode_label = "⚡ 立即完成"
    elif speed == 1.0:
        mode_label = "🕐 正常速度（每轮等待 110~130s）"
    else:
        mode_label = f"🚀 {speed:.1f}x 倍速（每轮等待 {110/speed:.0f}~{130/speed:.0f}s）"

    print(f"\n{'='*55}")
    print(f"📚 课程：{course_name}  (courseId={course_id} taskId={task_id})")
    print(f"   模式：{mode_label}")
    print(f"{'='*55}")

    stats = {"done": 0, "skip": 0, "fail": 0}


    while True:
        # 每次循环都刷新最新章节状态（解锁的课时会立即出现）
        chapters = api.get_chapters(course_id, task_id)
        found_pending = False

        for chapter in chapters:
            chapter_name = chapter["name"]
            contents     = chapter.get("contents") or []

            # 只处理「未完成 + 未锁定」的课时
            pending  = [c for c in contents if c.get("studyStatus") != "completed" and not c.get("isLocked", False)]
            done_cnt = sum(1 for c in contents if c.get("studyStatus") == "completed")
            lock_cnt = sum(1 for c in contents if c.get("isLocked", False))

            if not pending:
                continue  # 已完成的章节不打印，避免刷屏

            found_pending = True
            print(f"\n📖 {chapter_name}")
            print(f"   共 {len(contents)} 项 | 已完成 {done_cnt} | 正在处理 {len(pending)} | 锁定 {lock_cnt}")

            for item in pending:
                content_type = item.get("contentType")
                name         = item.get("contentName", "未知")
                content_id   = item.get("contentId")

                if content_type == "courseware":
                    _flush_video(api, item, task_id, mode, speed, name, content_id, stats)

                elif content_type == "quiz":
                    print(f"\n  🔲 {name}  (quizId={content_id})")
                    ok = solve_quiz(api, content_id, task_id, mode, speed, name)
                    stats["done" if ok else "fail"] += 1

                else:
                    print(f"\n  ⚠️  {name}  未知类型 {content_type!r}，跳过")
                    stats["skip"] += 1

        # 本轮没有找到任何待处理内容 → 全部完成，退出循环
        if not found_pending:
            break

    print(f"\n{'='*55}")
    print(f"🎉 课程《{course_name}》完成")
    print(f"   成功 {stats['done']} | 跳过 {stats['skip']} | 失败 {stats['fail']}")
    print(f"{'='*55}\n")


def _flush_video(api, item, task_id, mode, speed, name, cw_id, stats):
    content = item.get("content")
    if not content:
        print(f"\n  ⚠️  {name}：无 content 数据，跳过")
        stats["skip"] += 1
        return

    duration = content.get("videoDuration", 0)
    if duration <= 0:
        print(f"\n  ⚠️  {name}：视频时长为 0，跳过")
        stats["skip"] += 1
        return

    print(f"\n  ▶ {name}  (coursewareId={cw_id} 时长={duration}s / {duration//60}分{duration%60}秒)")

    if mode == "instant":
        ok = api.report_video_progress(cw_id, task_id, duration)
        print(f"  {'✅ 完成！' if ok else '❌ 上报失败'}")
        stats["done" if ok else "fail"] += 1
        time.sleep(3)
    else:
        ok = _flush_simulate(api, cw_id, task_id, duration, speed)
        print(f"  {'✅ 完成！' if ok else '❌ 上报失败'}")
        stats["done" if ok else "fail"] += 1


def _flush_simulate(api: ChaoxiaoAPI, cw_id: int, task_id: int, duration: int, speed: float) -> bool:

    watched = 0
    ok = True

    while True:
        step = _rand_step()           # 本轮上报的视频秒数
        real_wait = step / speed      # 实际等待秒数

        if watched + step >= duration:
            break

        watched += step
        ok = api.report_video_progress(cw_id, task_id, watched)
        print(f"    {'✅' if ok else '❌'} 上报 {watched}s / {duration}s"
              f"  ⏳ 等待 {real_wait:.1f}s（{speed:.1f}x）...")
        time.sleep(real_wait)

    # 收尾：上报精确总时长
    ok = api.report_video_progress(cw_id, task_id, duration)
    print(f"    {'✅' if ok else '❌'} 收尾上报 {duration}s（完成）")
    return ok