import argparse
import json
from pathlib import Path

from pipeline.config import Settings
from pipeline.orchestrator import Orchestrator


def main() -> int:
    parser = argparse.ArgumentParser(description="Heritage AI short film pipeline")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate")
    run_parser = subcommands.add_parser("run")
    run_parser.add_argument("--stage", choices=["keyframes", "shots", "music", "narration", "assemble", "script"])
    run_parser.add_argument("--shot")
    run_parser.add_argument("--script", type=Path, help="Generate a storyboard and film from a screenplay file")
    run_parser.add_argument("--force", action="store_true")
    subcommands.add_parser("status")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    orchestrator = Orchestrator(Settings.from_environment(root))

    if args.command == "validate":
        storyboard = orchestrator.validate()
        print(f"SUCCESS: storyboard valid ({len(storyboard['shots'])} shots)")
        return 0
    if args.command == "status":
        cache = orchestrator.cache.data
        print(json.dumps({
            "storyboard": str(root / "storyboard.json"),
            "cache_entries": len(cache),
            "outputs": str(root / "outputs"),
        }, indent=2))
        return 0

    print("[1/6] Validating storyboard ........ SUCCESS")
    step = 2
    for label, stage in [
        ("Generating keyframes", "keyframes"),
        ("Generating video shots", "shots"),
        ("Generating original music", "music"),
        ("Generating narration", "narration"),
        ("Assembling final film", "assemble"),
    ]:
        if args.stage and args.stage not in ("script", stage):
            continue
        print(f"[{step}/6] {label} ........ IN PROGRESS")
        step += 1
    try:
        results = orchestrator.run(
            args.stage, args.shot, args.force, script_path=args.script
        )
    except Exception as error:
        print(f"FAILED: {error}")
        return 1
    print(f"SUCCESS: completed {', '.join(results.keys())}")
    for stage, files in results.items():
        for file in files:
            print(f"  {stage}: {file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
