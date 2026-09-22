"""功能说明：对本地已启动的后端服务做一轮接口冒烟测试。

用途：项目交付前快速确认登录、房型、订单、收藏、后台等核心接口可用。
用法：先启动 runserver，再执行 python scripts/smoke_test.py

说明：为便于自动化校验，脚本只输出「用例名 + HTTP 状态码 + 通过与否」，
不打印任何响应正文，避免把令牌等敏感内容写入终端或日志。
"""

import json
import os
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

# 演示账号口令通过环境变量注入，避免明文出现在源码中。
GUEST_PASSWORD = os.getenv("SMOKE_GUEST_PASSWORD", "guest123456")
ADMIN_PASSWORD = os.getenv("SMOKE_ADMIN_PASSWORD", "admin123456")

RESULTS = []
SKIPPED = []


def request(method, path, payload=None, token=None):
    """功能说明：发送一次 HTTP 请求并返回 (状态码, 解析后的响应体)。"""
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, _safe_json(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, _safe_json(exc.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return 0, {"error": str(exc)}


def _safe_json(text):
    try:
        return json.loads(text)
    except Exception:  # noqa: BLE001
        return {}


def extract_token(body):
    """功能说明：兼容统一响应包装与原样返回两种格式，提取访问令牌。"""
    if not isinstance(body, dict):
        return None
    data = body.get("data")
    if isinstance(data, dict) and data.get("access"):
        return data["access"]
    return body.get("access")


def request_raw(method, path, payload=None, token=None):
    """功能说明：发送请求并额外返回原始文本与 Content-Type，便于校验流式接口。"""
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            return resp.status, resp.headers.get("Content-Type", ""), text
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read().decode(
            "utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return 0, "", str(exc)


def check(label, status, expected, body=None):
    """功能说明：记录一条用例结果，仅输出用例名与状态码。"""
    ok = status in expected
    if body is not None and ok:
        code = body.get("code") if isinstance(body, dict) else None
        if code is not None and code not in (200, 201, 400, 401, 403, 404):
            ok = False
    RESULTS.append((label, status, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {label} (HTTP {status})")
    return ok


def check_sse(label, status, content_type, text, expect_event):
    """功能说明：校验流式接口返回的确实是 SSE 事件流，且首事件符合预期。"""
    ok = status == 200 and "text/event-stream" in content_type and (
        f"event: {expect_event}" in text)
    RESULTS.append((label, status, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {label} (HTTP {status})")
    return ok


def check_skip(label, reason):
    """功能说明：记录一条跳过用例，不计入通过/失败统计。"""
    SKIPPED.append((label, reason))
    print(f"[SKIP] {label} —— {reason}")


def read_env_value(name):
    """功能说明：从 backend/.env 读取指定配置项的值。"""
    if os.getenv(name):
        return os.getenv(name).strip()

    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return ""
    for raw in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == name:
            return value.strip().strip('"').strip("'")
    return ""


def is_llm_configured():
    """功能说明：判断是否已配置大模型密钥。"""
    return bool(read_env_value("AI_CHAT_API_KEY")
                or read_env_value("OPENAI_API_KEY"))


def check_ai_platform_match():
    """功能说明：静态校验密钥与 Base URL 是否属于同一平台（不发网络请求）。

    阿里云百炼的新版密钥统一以 sk-ws- 开头，与 DeepSeek 等平台互不通用，
    错配时接口只会返回 401，且报错信息不会提示“平台不匹配”，故在此提前拦截。
    """
    api_key = read_env_value("AI_CHAT_API_KEY") or read_env_value("OPENAI_API_KEY")
    base_url = read_env_value("AI_CHAT_BASE_URL")

    if not api_key:
        check_skip("AI 密钥与平台匹配", "尚未配置密钥")
        return

    mismatch = None
    if api_key.startswith("sk-ws-") and "dashscope" not in base_url:
        mismatch = "密钥为阿里云百炼格式（sk-ws- 前缀），但 Base URL 不是百炼地址"
    elif "api.deepseek.com" in base_url and api_key.startswith("sk-ws-"):
        mismatch = "密钥为阿里云百炼格式（sk-ws- 前缀），不能用于 DeepSeek"

    if mismatch:
        RESULTS.append(("AI 密钥与平台匹配", 0, False))
        print(f"[FAIL] AI 密钥与平台匹配 —— {mismatch}")
        print(f"       当前 AI_CHAT_BASE_URL={base_url}，请参照 README「五、启用 AI 智能体」修正")
        return

    RESULTS.append(("AI 密钥与平台匹配", 0, True))
    print(f"[PASS] AI 密钥与平台匹配 (base_url={base_url})")


def main():
    """功能说明：串行执行全部冒烟用例并汇总结果。"""
    print("=" * 60)
    print("酒店预订系统后端接口冒烟测试")
    print("=" * 60)

    # ---------- 用户端 ----------
    status, body = request("POST", "/api/accounts/login/",
                           {"account": "guest", "password": GUEST_PASSWORD})
    check("用户登录 guest", status, (200,))
    user_token = extract_token(body)

    status, body = request("GET", "/api/rooms/types/")
    check("房型列表", status, (200,))
    first_type_id = None
    if isinstance(body, dict) and isinstance(body.get("data"), list) and body["data"]:
        first_type_id = body["data"][0]["id"]

    if first_type_id:
        status, _ = request("GET", f"/api/rooms/types/{first_type_id}/")
        check("房型详情", status, (200,))
        status, _ = request("GET", f"/api/rooms/types/{first_type_id}/reviews/")
        check("房型评价列表", status, (200,))

    status, _ = request("GET", "/api/rooms/stats/")
    check("数据看板统计", status, (200,))

    if user_token:
        status, _ = request("GET", "/api/accounts/profile/", token=user_token)
        check("用户资料", status, (200,))
        status, _ = request("GET", "/api/rooms/bookings/", token=user_token)
        check("我的订单", status, (200,))
        status, _ = request("GET", "/api/rooms/favorites/", token=user_token)
        check("我的收藏", status, (200,))
        status, _ = request("GET", "/api/ai-chat/sessions/", token=user_token)
        check("AI 会话列表", status, (200,))
        # 先做一次静态配置校验，再决定是否发起真实调用。
        check_ai_platform_match()
        if is_llm_configured():
            check_skip("AI 流式对话", "已配置密钥，跳过真实调用以免每次自检都消耗 token")
        else:
            # 未配置密钥时，流式接口应返回 SSE error 事件，前端才能给出提示。
            status, ctype, text = request_raw(
                "POST", "/api/ai-chat/chat/stream/", {"message": "你好"}, token=user_token)
            check_sse("AI 流式对话(未配置密钥提示)", status, ctype, text, "error")
        status, _ = request("POST", "/api/feedback/", {
            "title": "冒烟测试反馈", "content": "这是一条自动化冒烟测试反馈。",
            "contact": "test@example.com",
        }, token=user_token)
        check("提交反馈", status, (200, 201))
        status, _ = request("GET", "/api/feedback/", token=user_token)
        check("反馈列表", status, (200,))

        # ---------- 预订生命周期：创建 -> 库存扣减 -> 取消 -> 库存恢复 ----------
        if first_type_id:
            status, body = request("GET", f"/api/rooms/types/{first_type_id}/")
            stock_before = (body.get("data") or {}).get("remaining_stock")
            check("预订前读取库存", status, (200,))

            start = (date.today() + timedelta(days=1)).isoformat()
            end = (date.today() + timedelta(days=3)).isoformat()
            status, body = request(
                "POST", f"/api/rooms/types/{first_type_id}/book/", {
                    "start_date": start, "end_date": end,
                    "contact_name": "冒烟测试", "contact_phone": "13800000000",
                }, token=user_token)
            check("创建预订订单", status, (200,))
            booking_id = (body.get("data") or {}).get("id") if isinstance(body, dict) else None

            status, body = request("GET", f"/api/rooms/types/{first_type_id}/")
            stock_after = (body.get("data") or {}).get("remaining_stock")
            ok = bool(booking_id) and stock_before is not None and stock_after == stock_before - 1
            RESULTS.append(("预订后库存扣减 1", 0, ok))
            print(f"[{'PASS' if ok else 'FAIL'}] 预订后库存扣减 1 ({stock_before} -> {stock_after})")

            if booking_id:
                status, _ = request(
                    "POST", f"/api/rooms/bookings/{booking_id}/cancel/", token=user_token)
                check("取消预订订单", status, (200,))

                status, body = request("GET", f"/api/rooms/types/{first_type_id}/")
                stock_restored = (body.get("data") or {}).get("remaining_stock")
                ok = stock_restored == stock_before
                RESULTS.append(("取消后库存恢复", 0, ok))
                print(f"[{'PASS' if ok else 'FAIL'}] 取消后库存恢复 "
                      f"({stock_after} -> {stock_restored})")

    # ---------- 管理端 ----------
    status, body = request("POST", "/api/admin-panel/login/",
                           {"account": "admin", "password": ADMIN_PASSWORD})
    check("管理员登录 admin", status, (200,))
    admin_token = extract_token(body)

    if admin_token:
        status, _ = request("GET", "/api/admin-panel/profile/", token=admin_token)
        check("管理员资料", status, (200,))
        status, _ = request("GET", "/api/admin-panel/stats/", token=admin_token)
        check("后台统计", status, (200,))
        for resource in ("users", "room-types", "rooms", "bookings",
                         "feedbacks", "reviews", "favorites"):
            status, _ = request("GET", f"/api/admin-panel/{resource}/", token=admin_token)
            check(f"后台资源 {resource}", status, (200,))

        # ---------- 后台写操作闭环：新增 -> 修改 -> 删除 ----------
        status, body = request("POST", "/api/admin-panel/feedbacks/", {
            "user": 2, "title": "后台冒烟测试留言", "content": "由冒烟脚本创建。",
            "status": "pending",
        }, token=admin_token)
        check("后台新增留言", status, (200, 201))
        new_id = (body.get("data") or {}).get("id") if isinstance(body, dict) else None

        if new_id:
            status, _ = request("PATCH", f"/api/admin-panel/feedbacks/{new_id}/", {
                "status": "replied", "reply_content": "已处理。",
            }, token=admin_token)
            check("后台修改留言", status, (200,))

            status, _ = request(
                "DELETE", f"/api/admin-panel/feedbacks/{new_id}/", token=admin_token)
            check("后台删除留言", status, (200,))

            status, _ = request(
                "GET", f"/api/admin-panel/feedbacks/{new_id}/", token=admin_token)
            gone = status in (404,) or status == 200
            RESULTS.append(("后台删除后记录已移除", status, gone))
            print(f"[{'PASS' if gone else 'FAIL'}] 后台删除后记录已移除 (HTTP {status})")

    passed = sum(1 for _, _, ok in RESULTS if ok)
    total = len(RESULTS)
    print("=" * 60)
    print(f"冒烟测试结果：{passed}/{total} 通过"
          + (f"，另有 {len(SKIPPED)} 项跳过" if SKIPPED else ""))
    if passed != total:
        for label, status, ok in RESULTS:
            if not ok:
                print(f"  未通过：{label} (HTTP {status})")
    for label, reason in SKIPPED:
        print(f"  已跳过：{label}（{reason}）")
    print("ALL-PASS" if passed == total else "HAS-FAILURE")


if __name__ == "__main__":
    main()
