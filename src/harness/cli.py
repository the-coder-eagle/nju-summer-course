"""Coding Agent Harness CLI — 命令行入口"""
import sys
import os
import shutil
import tempfile
import argparse


def cmd_auth(args):
    """凭据管理"""
    from harness.auth.cli import status, set_, clear
    if args.action == "status":
        status()
    elif args.action == "set":
        set_()
    elif args.action == "clear":
        clear()


def _project_root():
    """Find project root (parent of src/)."""
    d = os.path.dirname(os.path.abspath(__file__))  # .../src/harness
    while d and not os.path.isdir(os.path.join(d, "arena")):
        d = os.path.dirname(d)
    return d


def cmd_run(args):
    """修复一个 kata"""
    from harness.loop import run
    from harness.config import load_config
    from harness.llm.deepseek import DeepSeekClient

    kata = args.kata
    root = _project_root()
    arena_dir = os.path.join(root, "arena", kata)
    if not os.path.isdir(arena_dir):
        katas = os.listdir(os.path.join(root, "arena"))
        print(f"Unknown kata: {kata}")
        print(f"Available: {', '.join(katas)}")
        return

    sandbox = tempfile.mkdtemp()
    shutil.copytree(arena_dir, sandbox, dirs_exist_ok=True)

    llm = DeepSeekClient(model="deepseek-chat")
    cfg = load_config({"sandbox_root": sandbox, "retry_budget": 5})

    from harness.logging import EventLogger
    logger = EventLogger(args.log) if args.log else None

    print(f"Repairing {kata}...")
    events = []
    out = run(".", llm, cfg, on_event=lambda e: events.append(e), logger=logger)

    if logger:
        logger.close()
        print(f"Log saved to {args.log}")

    for i, e in enumerate(events):
        act = str(e['action']).split("(")[0].split(".")[-1]
        print(f"  Turn {i}: {act}")

    print(f"Result: {out.status} ({out.turns} turns)")
    if out.final_test_result:
        if out.final_test_result.exit_code == 0:
            print("Tests passed!")
        else:
            print(out.final_test_result.stdout[-300:])


def cmd_replay(args):
    """回放事件日志"""
    from harness.logging import replay_log
    events = replay_log(args.logfile)
    if not events:
        print("No events found.")
        return
    for e in events:
        print(f"T{e['turn']}: {e['action'][:80]}")
        if e.get("result"):
            print(f"    => {e['result'][:80]}")
    print(f"--- {len(events)} events")


def cmd_web(args):
    """启动 WebUI"""
    import uvicorn
    uvicorn.run("web.app:app", host="0.0.0.0", port=args.port, reload=True)


def main():
    parser = argparse.ArgumentParser(description="Coding Agent Harness")
    sub = parser.add_subparsers(dest="command")

    # auth
    p_auth = sub.add_parser("auth", help="Manage API key")
    p_auth.add_argument("action", choices=["status", "set", "clear"])

    # run
    p_run = sub.add_parser("run", help="Repair a kata")
    p_run.add_argument("kata", help="Kata name (e.g. kata_assertion)")
    p_run.add_argument("--log", help="Save events to JSONL file", default=None)

    # replay
    p_replay = sub.add_parser("replay", help="Replay an event log")
    p_replay.add_argument("logfile", help="JSONL log file")

    # web
    p_web = sub.add_parser("web", help="Start WebUI")
    p_web.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()
    if args.command == "auth":
        cmd_auth(args)
    elif args.command == "run":
        cmd_run(args)
    elif args.command == "replay":
        cmd_replay(args)
    elif args.command == "web":
        cmd_web(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
