"""CLI for the UHB benchmark suite."""

import argparse
import sys
import json
from pathlib import Path

from . import (
    BenchmarkRunner, get_registry, discover_tasks,
    generate_profile, save_profile, compare_profiles, load_profile,
    ALL_DIMENSIONS,
)
from uhb.core.config import get_config


def cmd_profile(args):
    """Run a capability profile."""
    print(f"Profiling model: {args.model}")
    print(f"Tasks: {args.tasks or 'all'}")
    print(f"Seeds: {args.seeds}")
    print()

    # Discover built-in tasks
    registry = discover_tasks("uhb.benchmark.tasks")

    if args.tasks:
        task_ids = [t.strip() for t in args.tasks.split(",")]
    else:
        task_ids = None

    runner = BenchmarkRunner(args.model, registry=registry)
    try:
        results = runner.run_all(seeds=args.seeds, task_ids=task_ids)
    finally:
        runner.close()

    profile = generate_profile(args.model, results)
    print(json.dumps(profile, indent=2))

    if args.output:
        save_profile(profile, args.output)
        print(f"\nProfile saved to {args.output}")


def cmd_compare(args):
    """Compare multiple models."""
    profiles = []
    for path in args.profiles:
        profiles.append(load_profile(path))

    comparison = compare_profiles(profiles)

    print("=" * 70)
    print("Model Comparison")
    print("=" * 70)
    print()

    # Overall
    print("Overall Scores:")
    for model, score in comparison["overall"].items():
        print(f"  {model}: {score:.4f}")
    print()

    # Dimensions
    dims = comparison["dimensions"]
    models = comparison["models"]
    header = f"{'Dimension':<28}" + "".join(f"{m:<16}" for m in models)
    print(header)
    print("-" * len(header))

    for dim, scores in dims.items():
        row = f"  {dim:<26}"
        for model in models:
            s = scores.get(model)
            row += f"{s:<16.4f}" if s is not None else f"{'N/A':<16}"
        print(row)

    print()
    print("Dimension Winners:")
    for dim, winner in comparison.get("winners", {}).items():
        print(f"  {dim}: {winner}")


def main():
    parser = argparse.ArgumentParser(
        prog="uhb-benchmark",
        description="UHB Benchmark — profile AI coding models across 10 dimensions",
    )
    sub = parser.add_subparsers(dest="command", help="Commands")

    # profile
    p = sub.add_parser("profile", help="Run capability profile")
    p.add_argument("model", help="Model key (e.g., anthropic/claude-sonnet-4-6)")
    p.add_argument("--tasks", help="Comma-separated task IDs (default: all)")
    p.add_argument("--seeds", type=int, default=3, help="Seeds per task (default: 3)")
    p.add_argument("--output", "-o", help="Save profile to JSON file")
    p.set_defaults(func=cmd_profile)

    # compare
    c = sub.add_parser("compare", help="Compare saved profiles")
    c.add_argument("profiles", nargs="+", help="Profile JSON files to compare")
    c.set_defaults(func=cmd_compare)

    # list
    ls = sub.add_parser("list", help="List available tasks")
    ls.set_defaults(func=cmd_list)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


def cmd_list(args):
    """List all available benchmark tasks."""
    registry = discover_tasks("uhb.benchmark.tasks")
    specs = registry.list_all()

    print(f"{'Task ID':<24} {'Dimension':<28} {'Difficulty':<10} {'Name'}")
    print("-" * 90)
    for s in sorted(specs, key=lambda x: x.dimension):
        print(f"{s.task_id:<24} {s.dimension:<28} {s.difficulty:<10} {s.name}")

    print(f"\n{len(specs)} tasks across {len(registry.dimensions)} dimensions")


if __name__ == "__main__":
    main()
