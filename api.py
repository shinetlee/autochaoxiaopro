import requests

API_BASE = "https://school-api.chaoxiaopro.cn/api"
WEB_BASE = "https://school-web.chaoxiaopro.cn"


class ChaoxiaoAPI:
    def __init__(self, token: str):
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Origin": WEB_BASE,
            "Referer": f"{WEB_BASE}/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) "
                "Gecko/20100101 Firefox/149.0"
            ),
        })

    def _get(self, path: str, params: dict = None) -> dict:
        resp = self.session.get(f"{API_BASE}{path}", params=params, timeout=15)
        if not resp.text.strip():
            raise RuntimeError(f"空响应 (HTTP {resp.status_code})，token 可能已过期")
        return resp.json()

    def _post(self, path: str, data: dict) -> dict:
        resp = self.session.post(f"{API_BASE}{path}", json=data, timeout=15)
        if not resp.text.strip():
            raise RuntimeError(f"空响应 (HTTP {resp.status_code})，token 可能已过期")
        return resp.json()

    def get_courses(self, page_size: int = 50) -> list[dict]:
        """获取课程列表"""
        result = self._get("/student/learning/courses", params={"pageNo": 1, "pageSize": page_size})
        if result.get("code") != 200:
            raise RuntimeError(f"获取课程列表失败: {result}")
        return result["data"]["records"]

    def get_chapters(self, course_id: int, task_id: int) -> list[dict]:
        """获取某课程的所有章节及课时"""
        result = self._get(f"/student/learning/courses/{course_id}/chapters", params={"taskId": task_id})
        if result.get("code") != 200:
            raise RuntimeError(f"获取章节失败: {result}")
        return result["data"]

    def report_video_progress(self, courseware_id: int, task_id: int, watched_seconds: int) -> bool:
        """上报视频观看进度"""
        result = self._post("/student/learning/video-progress", {
            "coursewareId": courseware_id,
            "taskId": task_id,
            "watchedSeconds": watched_seconds,
        })
        return result.get("code") == 200

    def get_quiz(self, quiz_id: int, task_id: int) -> dict:
        """获取测验题目（含加密答案）"""
        result = self._get(f"/student/learning/quizzes/{quiz_id}", params={"taskId": task_id})
        if result.get("code") != 200:
            raise RuntimeError(f"获取测验失败: {result}")
        return result["data"]

    def submit_quiz(self, quiz_id: int, task_id: int, total_score: float, answers: list[dict]) -> bool:
        """提交测验答案"""
        result = self._post("/student/learning/quizzes/submit", {
            "quizId": quiz_id,
            "taskId": task_id,
            "totalScore": total_score,
            "answers": answers,
        })
        return result.get("code") == 200
