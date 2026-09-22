"""一键停止酒店预订系统的服务：前端(Vite) / 后端(Django) / MySQL。

设计要点：
1. 不按进程名批量杀，一律先按端口反查 PID，再精确关闭，避免误伤机器上其他
   python.exe / node.exe 进程。
2. MySQL 使用官方 mysqladmin shutdown 优雅关闭，保证 InnoDB 正常刷盘，
   不使用 taskkill 强杀。
3. 口令通过 MYSQL_PWD 环境变量传递，不出现在命令行参数中。
"""

import os
import pathlib
import subprocess
import sys
import time

BASE_DIR = pathlib.Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
MYSQL_BIN = pathlib.Path(r"D:\mysql\mysql-8.0.46-winx64\bin")

# 端口 -> (名称, 是否优雅关闭)
SERVICES = {
    5173: "前端 Vite",
    8000: "后端 Django",
    3306: "MySQL 数据库",
}


def listen_pids() -> dict:
    """返回 {端口: {PID, ...}}，仅统计处于 LISTENING 状态的套接字。"""
    proc = subprocess.run(
        ["netstat", "-ano"], capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    mapping: dict = {}
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[0].upper() == "TCP" and parts[-2].upper() == "LISTENING":
            try:
                port = int(parts[1].rsplit(":", 1)[-1])
                pid = int(parts[-1])
            except ValueError:
                continue
            mapping.setdefault(port, set()).add(pid)
    return mapping


def read_env() -> dict:
    """读取 backend/.env 中的配置项。"""
    env_file = BACKEND_DIR / ".env"
    if not env_file.exists():
        return {}
    data = {}
    for raw in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def stop_mysql(pids: set) -> bool:
    """通过 mysqladmin shutdown 优雅关闭 MySQL。"""
    admin = MYSQL_BIN / "mysqladmin.exe"
    cfg = read_env()
    password = cfg.get("DB_PASSWORD", "")
    user = cfg.get("DB_USER", "root")
    host = cfg.get("DB_HOST", "127.0.0.1")
    port = cfg.get("DB_PORT", "3306")

    if not admin.exists():
        print(f"  ! 未找到 mysqladmin（{admin}），改用强制结束")
        return force_kill(pids)

    env = dict(os.environ)
    if password:
        env["MYSQL_PWD"] = password

    proc = subprocess.run(
        [str(admin), f"-u{user}", f"-h{host}", f"-P{port}",
         "--protocol=tcp", "shutdown"],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", env=env, timeout=30,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()[:200]
        print(f"  ! mysqladmin 返回码 {proc.returncode}：{detail}")
        print("  → 改用强制结束")
        return force_kill(pids)

    print("  √ 已发送优雅关闭指令（等待刷盘退出…）")
    return True


def force_kill(pids: set) -> bool:
    """按 PID 精确强制结束进程。"""
    ok = True
    for pid in sorted(pids):
        proc = subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if proc.returncode == 0:
            print(f"  √ 已结束 PID {pid}")
        else:
            ok = False
            print(f"  ! PID {pid} 结束失败：{(proc.stderr or '').strip()[:120]}")
    return ok


def wait_release(port: int, timeout: float = 15.0) -> bool:
    """等待端口释放。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if port not in listen_pids():
            return True
        time.sleep(0.5)
    return False


def main() -> int:
    print("=" * 58)
    print("停止酒店预订系统服务")
    print("=" * 58)

    listening = listen_pids()

    running = {p: listening[p] for p in SERVICES if p in listening}
    if not running:
        print("\n三个服务均未运行（8000 / 5173 / 3306 都没有监听），无需操作。")
        return 0

    # MySQL 放最后关，避免前后端还在写数据时连接被切断。
    order = [5173, 8000, 3306]
    for port in order:
        name = SERVICES[port]
        pids = running.get(port)
        if not pids:
            print(f"\n[{name}] 未运行，跳过")
            continue

        pid_text = ", ".join(str(p) for p in sorted(pids))
        print(f"\n[{name}] 运行中，端口 {port}，PID {pid_text}")

        if port == 3306:
            stop_mysql(pids)
        else:
            force_kill(pids)

        if wait_release(port):
            print(f"  √ 端口 {port} 已释放")
        else:
            print(f"  ! 端口 {port} 仍在监听，可能未完全退出")

    print("\n" + "=" * 58)
    print("最终状态")
    print("=" * 58)
    left = listen_pids()
    for port, name in SERVICES.items():
        state = f"仍在运行(PID {', '.join(map(str, sorted(left[port])))})" if port in left else "已停止"
        print(f"  {name:14} {port:5}  {state}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
