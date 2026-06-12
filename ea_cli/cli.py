"""ea_cli/cli.py — EulerAgent 命令行分发（python -m ea_cli <命令> 或 ea <命令>）"""
import os, sys, subprocess, argparse, textwrap

# Windows GBK 终端兼容
if sys.platform == "win32" and sys.stdout.encoding and sys.stdout.encoding.lower() in ("gbk", "gb2312"):
    sys.stdout.reconfigure(errors="replace") if hasattr(sys.stdout, "reconfigure") else None

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cmd_list():
    print(f"\n  {'命令':12s}  说明")
    print(f"  {'━' * 12}  {'━' * 40}")
    for name, (help_, action) in sorted(COMMANDS.items(), key=lambda kv: (callable(kv[1][1]), kv[0])):
        print(f"  {name:12s}  {help_}")
    print()


def cmd_status():
    import psutil
    running = [p for p in psutil.process_iter(['pid', 'name', 'cmdline'])
               if p.info['cmdline'] and any('agentmain' in c for c in p.info['cmdline'])]
    if running:
        print(f"🟢 运行中: {len(running)} 个进程")
        for p in running:
            print(f"   PID {p.info['pid']} — {' '.join(p.info['cmdline'][:3])}")
    else:
        print("⚫ EulerAgent 进程未运行")


def cmd_update():
    os.chdir(PROJECT_DIR)
    print("🔄 git pull...")
    r = subprocess.run(["git", "pull"], capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr)
    print("📦 pip install...")
    r2 = subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], capture_output=True, text=True)
    print(r2.stdout[-500:] if r2.stdout else "")
    if r2.returncode != 0:
        print(r2.stderr[-500:])


COMMANDS = {  # 名称: (说明, python argv 相对项目根 | 无参可调用)
    "gui":       ("启动桌面 GUI (qtapp)",              ["frontends/qtapp.py"]),
    "web":       ("启动 Streamlit Web 界面 (stapp2)",  ["-m", "streamlit", "run", "frontends/stapp2.py"]),
    "tui":       ("启动终端 TUI (tuiapp_v2)",          ["frontends/tuiapp_v2.py"]),
    "cli":       ("启动命令行对话 (agentmain)",        ["core/agentmain.py"]),
    "launch":    ("启动 webview 桌面壳 (launch.pyw)",  ["launch.pyw"]),
    "hub":       ("启动 Hub 服务管理面板 (hub.pyw)",   ["hub.pyw"]),
    "configure": ("运行初始配置向导 (configure_ekey)", ["assets/scripts/configure_ekey.py"]),
    "status":    ("检查运行状态", cmd_status),
    "update":    ("更新项目 (git pull + pip install)", cmd_update),
    "list":      ("列出所有命令", cmd_list),
}


def launch(argv, extra):
    cmd = [sys.executable] + argv + extra
    print(f"🚀 {' '.join(cmd)}")
    sys.stdout.flush()
    os.chdir(PROJECT_DIR)
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        prog="ea", description="EulerAgent 全局命令入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            示例:
              ea gui       启动桌面 GUI
              ea web       启动 Streamlit Web 界面
              ea tui       启动终端 TUI
              ea cli       启动命令行对话
              ea list      列出所有命令
        """))
    parser.add_argument("command", nargs="?", help="命令名")
    parser.add_argument("args", nargs="*", help="子命令参数")
    parser.add_argument("-v", "--version", action="store_true", help="显示版本")
    args, unknown = parser.parse_known_args()

    if args.version:
        return print("EulerAgent v0.1.0")
    if not args.command or args.command == "help":
        parser.print_help()
        return cmd_list()
    entry = COMMANDS.get(args.command)
    if not entry:
        print(f"❌ 未知命令: {args.command}（用 'ea list' 查看可用命令）")
        sys.exit(1)
    action = entry[1]
    if callable(action):
        return action()
    launch(action, list(args.args) + unknown)


if __name__ == "__main__":
    main()
