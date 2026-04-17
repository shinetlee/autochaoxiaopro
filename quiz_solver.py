import time
import json
from api import ChaoxiaoAPI
from decrypt import decrypt_answer

# 题型中文名
TYPE_NAMES = {
    "single_choice":   "单选题",
    "multiple_choice": "多选题",
    "true_false":      "判断题",
    "fill_blank":      "填空题",
    "essay":           "主观题",
}


def solve_quiz(api: ChaoxiaoAPI, quiz_id: int, task_id: int, mode: str, speed: float = 1.0, quiz_name: str = ""):
    """
    获取测验题目 → 解密答案 → 展示 → 提交
    mode: "instant" 立即提交 | "normal" 等待2分钟后提交
    """
    print(f"\n  📝 测验：{quiz_name or f'quiz#{quiz_id}'}")

    # 1. 获取题目
    quiz = api.get_quiz(quiz_id, task_id)
    questions = quiz.get("questions", [])
    total_score = quiz.get("totalScore", 0)

    print(f"     共 {len(questions)} 题，总分 {total_score} 分")

    # 2. 解密并展示每道题
    answers = []
    for i, q in enumerate(questions, 1):
        q_id    = q["id"]
        q_type  = q["type"]
        q_title = q["title"]
        q_score = q["score"]
        enc_ans = q.get("encryptedAnswer", "")
        options = q.get("optionList", [])
        option_labels = ["A", "B", "C", "D", "E", "F"]

        # 解密答案
        try:
            answer = decrypt_answer(enc_ans, q_type)
        except Exception as e:
            print(f"     ❌ 第{i}题解密失败: {e}，跳过")
            continue

        # 打印题目
        type_name = TYPE_NAMES.get(q_type, q_type)
        print(f"\n     [{i}] ({type_name} {q_score}分) {q_title}")

        if options:
            for label, opt in zip(option_labels, options):
                # 标记正确选项
                if q_type == "single_choice" and label == answer:
                    mark = " ◀ ✓"
                elif q_type == "multiple_choice" and label in answer:
                    mark = " ◀ ✓"
                else:
                    mark = ""
                print(f"          {label}. {opt}{mark}")

        # 判断题特殊展示
        if q_type == "true_false":
            ans_display = "正确 (true)" if answer == "true" else "错误 (false)"
            print(f"          答案：{ans_display}")
        elif q_type == "multiple_choice":
            print(f"          答案：{'、'.join(answer)}")
        else:
            print(f"          答案：{answer}")

        # 构造提交格式
        answers.append({
            "questionId": q_id,
            "answer":     answer,
            "score":      q_score,
        })

    if not answers:
        print("     ⚠️  没有可提交的答案，跳过")
        return False

    # 3. 按模式决定何时提交
    if mode == "simulate":
        wait = int(_random_wait() / speed)
        print(f"\n     ⏳ 等待 {wait}s 后提交（{speed:.1f}x）...")
        time.sleep(wait)

    # 4. 提交
    ok = api.submit_quiz(quiz_id, task_id, total_score, answers)
    if ok:
        print(f"     ✅ 测验提交成功！满分 {total_score} 分")
    else:
        print(f"     ❌ 测验提交失败")
    return ok


def _random_wait() -> int:
    import random
    return random.randint(110, 130)
