#!/usr/bin/env python3
"""UHB — Universal Harness Benchmark — unified CLI.

Usage:
    uhb benchmark <model>      Profile a model across 10 dimensions
    uhb search <model>         Search for optimal harness configuration
    uhb evolve <model>         Evolve a harness genome
    uhb compile <model>        Compile optimal harness from profile
    uhb systems <system>       Benchmark an AI coding system
    uhb dashboard              Launch visualization dashboard
    uhb compare <a> <b>        Compare two models or systems
    uhb list                   List available models and tasks

No API key? Use mock models:
    uhb benchmark mock/medium
    uhb evolve mock/strong --generations 5
"""

import argparse
import sys
import os
import json
from pathlib import Path

# Project root directory
_UHB_ROOT = Path(__file__).resolve().parent.parent


def cmd_benchmark(args):
    """Run a capability profile benchmark."""
    from uhb.core.config import MODEL_REGISTRY
    from uhb.core.logging import configure_root
    from uhb.benchmark.tasks.registry import discover_tasks
    from uhb.benchmark.runner import BenchmarkRunner
    from uhb.benchmark.report import generate_profile, save_profile

    configure_root()

    model = args.model
    seeds = args.seeds
    task_str = args.tasks

    print(f"\n🧬 UHB Benchmark — Profiling: {model}")
    print(f"   Seeds per task: {seeds}")
    print(f"   Tasks: {task_str or 'all'}")
    print()

    # Discover tasks
    registry = discover_tasks("uhb.benchmark.tasks")
    task_ids = [t.strip() for t in task_str.split(",")] if task_str else None

    if not task_ids and registry.task_count == 0:
        # Fall back to directly importing known tasks
        _register_builtin_tasks(registry)

    print(f"   Loaded {registry.task_count} tasks across {len(registry.dimensions)} dimensions")
    print()

    # Run benchmark
    runner = BenchmarkRunner(model, registry=registry)
    try:
        results = runner.run_all(seeds=seeds, task_ids=task_ids)
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        sys.exit(1)
    finally:
        runner.close()

    # Generate profile
    profile = generate_profile(model, results)

    # Display results
    print("=" * 60)
    print("CAPABILITY PROFILE")
    print("=" * 60)
    print(f"Model:      {model}")
    print(f"Overall:    {profile['overall_score']:.3f}")
    print(f"Tasks:      {profile['tasks_passed']}/{profile['task_count']} passed")
    print()
    print("Dimensions:")
    for dim, score in sorted(profile['dimensions'].items()):
        if score is not None:
            bar = "█" * int(score * 30)
            print(f"  {dim:<28} {score:.2f} {bar}")
        else:
            print(f"  {dim:<28}  N/A")

    print()
    print("Per-Task Results:")
    for t in profile['per_task']:
        status = "✅" if t['passed'] else "❌"
        print(f"  {status} {t['task_id']:<24} {t['score']:.2f} ({t.get('latency_ms', 0):.0f}ms)")

    # Save
    if args.output:
        save_profile(profile, args.output)
        print(f"\n📁 Profile saved to {args.output}")
    elif args.save:
        out = f"data/results/{model.replace('/', '_')}_{_timestamp()}.json"
        save_profile(profile, str(_UHB_ROOT / out))
        print(f"\n📁 Profile saved to {out}")


def cmd_search(args):
    """Search for optimal harness configuration."""
    from uhb.core.logging import configure_root
    from uhb.evolution.harness_search import HarnessSearcher
    from uhb.evolution.genome import HarnessGenome

    configure_root()

    model = args.model
    method = args.method
    num = args.num_configs

    print(f"\n🔍 UHB Harness Search — Model: {model}")
    print(f"   Method: {method}, Configs: {num}")
    print()

    # Mock evaluator for demonstration
    def evaluate(genome):
        import random
        rng = random.Random(hash(genome.hash()) % 2**32)
        # Simulate: good harnesses have PLAN→CODE→TEST→REVIEW pattern
        genes = [g.value for g in genome.genes]
        score = 0.5
        if "plan" in genes:
            score += 0.1
        if "code" in genes and "test" in genes:
            score += 0.15
        if "review" in genes:
            score += 0.1
        if "repair" in genes:
            score += 0.05
        if genome.context_strategy == "full":
            score += 0.05
        if genome.retry_policy == "on_failure":
            score += 0.05
        return score + rng.uniform(-0.05, 0.05)

    searcher = HarnessSearcher(evaluate)

    if method == "grid":
        results = searcher.grid_search(max_configs=num)
    elif method == "random":
        results = searcher.random_search(num_configs=num)
    else:
        results = searcher.random_search(num_configs=num)

    print("Top 5 Harness Configurations:")
    print("-" * 60)
    for i, (genome, fitness) in enumerate(results[:5], 1):
        print(f"  {i}. {genome.display():<45} fitness={fitness:.3f}")
        print(f"     ctx={genome.context_strategy} tools={genome.tool_policy} retry={genome.retry_policy}")

    best = results[0][0]
    print()
    print(f"🏆 Best: {best.display()}")
    print(f"   Fitness: {results[0][1]:.3f}")

    if args.output:
        best.to_dict()
        json.dump(best.to_dict(), open(args.output, 'w'), indent=2)
        print(f"   Saved to {args.output}")


def cmd_evolve(args):
    """Evolve an optimal harness genome."""
    from uhb.core.logging import configure_root
    from uhb.evolution.genome import HarnessGenome
    from uhb.evolution.fitness import FitnessEvaluator
    from uhb.evolution.evolve import EvolutionEngine

    configure_root()

    model = args.model
    generations = args.generations
    population = args.population

    print(f"\n🧬 UHB Evolution — Model: {model}")
    print(f"   Generations: {generations}, Population: {population}")
    print()

    # Mock fitness evaluator
    def benchmark_fn(genome):
        import random
        rng = random.Random(hash(genome.hash()) % 2**32)
        genes = [g.value for g in genome.genes]
        # Base score from gene composition
        score = 0.5
        if "plan" in genes:
            score += 0.1
        if "code" in genes and "test" in genes:
            score += 0.15
        if "review" in genes:
            score += 0.1
        if "repair" in genes:
            score += 0.05
        if "research" in genes:
            score += 0.05
        score += rng.uniform(-0.05, 0.05)

        return {
            "success": min(1.0, score),
            "cost_usd": rng.uniform(0.1, 0.5),
            "time_seconds": rng.uniform(5, 30),
            "retries": rng.randint(0, 3),
            "autonomous": rng.random() > 0.2,
        }

    evaluator = FitnessEvaluator(benchmark_fn)
    engine = EvolutionEngine(
        evaluator=evaluator,
        population_size=population,
        elite_count=max(2, population // 10),
        seed=args.seed,
    )

    def progress_callback(gen, pop, pareto):
        print(f"  Gen {gen:>3}: best={pop.fitness_scores.get(pop.best_genome().hash()).combined:.3f}  "
              f"avg={pop.average_fitness():.3f}  "
              f"pareto={pareto.size}  diversity={pop.diversity():.2f}")

    results = engine.run(
        max_generations=generations,
        callback=progress_callback,
        early_stop_patience=args.patience,
    )

    print()
    print("=" * 60)
    print("EVOLUTION RESULTS")
    print("=" * 60)
    print(f"Best Genome:  {results['best_genome_display']}")
    print(f"Best Fitness: {results['best_fitness']:.3f}")
    print(f"Generations:  {results['generations_run']}")
    print(f"Pareto Size:  {results['pareto_size']}")

    if args.output:
        json.dump(results, open(args.output, 'w'), indent=2, default=str)
        print(f"\n📁 Results saved to {args.output}")


def cmd_compile(args):
    """Compile optimal harness from a profile."""
    from uhb.compiler.compile import compile_from_profile
    from uhb.compiler.export import export_to_json, export_to_yaml, export_to_python

    model = args.model
    fmt = args.format

    print(f"\n⚙️  UHB Compiler — Model: {model}")

    # Generate or load profile
    if args.profile:
        profile = json.load(open(args.profile))
    else:
        # Quick benchmark to get a profile
        from uhb.core.logging import configure_root
        configure_root()
        from uhb.benchmark.tasks.registry import discover_tasks
        _register_builtin_tasks(discover_tasks("uhb.benchmark.tasks"))

        from uhb.benchmark.runner import BenchmarkRunner
        from uhb.benchmark.report import generate_profile

        print("   Running quick profile (1 seed)...")
        registry = discover_tasks("uhb.benchmark.tasks")
        runner = BenchmarkRunner(model, registry=registry)
        try:
            results = runner.run_all(seeds=1)
        finally:
            runner.close()
        profile = generate_profile(model, results)

    # Compile
    harness = compile_from_profile(profile)

    print(f"\n   Compiled Harness:")
    print(f"   Genes:    {' → '.join(harness['genes'])}")
    print(f"   Context:  {harness['context_strategy']}")
    print(f"   Tools:    {harness['tool_policy']}")
    print(f"   Retry:    {harness['retry_policy']}")
    print(f"   Confidence: {harness['confidence']:.2f}")
    print(f"   Rationale: {harness['rationale']}")

    if args.output:
        if fmt == "json":
            export = export_to_json(harness, args.output)
        elif fmt == "yaml":
            export = export_to_yaml(harness, args.output)
        elif fmt == "python":
            export = export_to_python(harness, args.output)
        print(f"\n📁 Exported to {args.output}")


def cmd_compare(args):
    """Compare two models or saved profiles."""
    from uhb.core.logging import configure_root
    from uhb.benchmark.tasks.registry import discover_tasks
    from uhb.benchmark.runner import BenchmarkRunner
    from uhb.benchmark.report import generate_profile, compare_profiles

    configure_root()

    models = [args.model_a, args.model_b]

    print(f"\n📊 UHB Comparison: {args.model_a} vs {args.model_b}\n")

    profiles = []
    for model in models:
        print(f"  Profiling {model}...")
        registry = discover_tasks("uhb.benchmark.tasks")
        if registry.task_count == 0:
            _register_builtin_tasks(registry)

        runner = BenchmarkRunner(model, registry=registry)
        try:
            results = runner.run_all(seeds=2, task_ids=None)
        finally:
            runner.close()

        profile = generate_profile(model, results)
        profiles.append(profile)

    comparison = compare_profiles(profiles)

    # Display
    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    print(f"\nOverall:")
    for model, score in comparison['overall'].items():
        print(f"  {model}: {score:.3f}")

    print(f"\nDimension Breakdown:")
    header = f"  {'Dimension':<28}"
    for m in comparison['models']:
        short = m.split("/")[-1][:14]
        header += f" {short:<15}"
    print(header)
    print("  " + "-" * (28 + 16 * len(comparison['models'])))

    for dim in sorted(comparison['dimensions']):
        row = f"  {dim:<28}"
        for m in comparison['models']:
            score = comparison['dimensions'][dim].get(m)
            if score is not None:
                row += f" {score:<15.3f}"
            else:
                row += f" {'N/A':<15}"
        print(row)

    print(f"\n🏆 Dimension Winners:")
    for dim, winner in comparison.get('winners', {}).items():
        print(f"  {dim}: {winner}")


def cmd_list(args):
    """List available models and tasks."""
    from uhb.core.config import MODEL_REGISTRY
    from uhb.benchmark.tasks.registry import discover_tasks

    print("\n📋 Available Models:")
    print("-" * 50)
    for key, spec in MODEL_REGISTRY.items():
        print(f"  {key:<35} ({spec.provider})")
    print(f"\n  ...plus any model via OpenRouter")

    print("\n📋 Available Tasks:")
    print("-" * 50)
    registry = discover_tasks("uhb.benchmark.tasks")
    if registry.task_count == 0:
        _register_builtin_tasks(registry)
    for spec in sorted(registry.list_all(), key=lambda s: s.dimension):
        print(f"  {spec.task_id:<24} [{spec.dimension:<26}] {spec.name}")


def cmd_dashboard(args):
    """Launch the Streamlit dashboard."""
    import subprocess
    dashboard_path = _UHB_ROOT / "uhb" / "dashboard" / "app.py"
    print(f"\n🚀 Launching UHB Dashboard...")
    print(f"   Open http://localhost:8501 in your browser\n")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", str(dashboard_path),
        "--server.port", str(args.port),
        "--server.headless", "true",
    ])


def cmd_systems(args):
    """Benchmark an AI coding system."""
    from uhb.core.logging import configure_root
    from uhb.systems.runner import SystemBenchmarkRunner
    from uhb.systems.targets.cli_wrapper import CLICodingSystem
    
    configure_root()
    
    system_name = args.system
    repo = Path(args.repo) if args.repo else _UHB_ROOT
    
    print(f"\n🖥️  UHB Systems Benchmark — System: {system_name}")
    print(f"   Repository: {repo}")
    print()
    
    if system_name.lower() == "aider":
        system = CLICodingSystem("Aider", "aider", r"> ")
    elif system_name.lower() == "claude":
        system = CLICodingSystem("Claude Code", "claude", r"> ")
    else:
        # Generic wrapper
        system = CLICodingSystem(system_name, system_name, r"> ")
    
    runner = SystemBenchmarkRunner(system, repo)
    try:
        profile = runner.run()
    finally:
        runner.system.teardown()
        
    print("\n" + profile.summary())
    
    if args.output:
        import json
        with open(args.output, "w") as f:
            json.dump(profile.to_dict(), f, indent=2)
        print(f"\n📁 Saved profile to {args.output}")


def _register_builtin_tasks(registry):
    """Register built-in task classes when auto-discovery fails."""
    from uhb.benchmark.tasks.base import TaskBase
    from uhb.benchmark.tasks.code_from_spec.task import CodeFromSpecTask
    from uhb.benchmark.tasks.debug_broken.task import DebugBrokenTask
    from uhb.benchmark.tasks.refactor.task import RefactorTask
    from uhb.benchmark.tasks.tool_use.task import ToolUseTask
    from uhb.benchmark.tasks.search_docs.task import SearchDocsTask
    from uhb.benchmark.tasks.plan_feature.task import PlanFeatureTask
    from uhb.benchmark.tasks.review_pr.task import ReviewPRTask
    from uhb.benchmark.tasks.long_context.task import LongContextTask
    from uhb.benchmark.tasks.self_repair.task import SelfRepairTask

    for cls in [CodeFromSpecTask, DebugBrokenTask, RefactorTask, ToolUseTask,
                SearchDocsTask, PlanFeatureTask, ReviewPRTask, LongContextTask,
                SelfRepairTask]:
        registry.register(cls)


def _timestamp():
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def main():
    parser = argparse.ArgumentParser(
        prog="uhb",
        description="🧬 UHB — Universal Harness Benchmark — AI Developer Research Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quick start:
  uhb benchmark mock/medium          # Profile a mock model (no API key needed)
  uhb search mock/medium             # Search for optimal harness
  uhb evolve mock/strong --generations 5  # Evolve a harness genome
  uhb compare mock/strong mock/weak  # Compare two models
  uhb list                           # List all available models and tasks
  uhb dashboard                      # Launch visualization dashboard

Use real models by setting API keys:
  export ANTHROPIC_API_KEY=sk-ant-...
  uhb benchmark anthropic/claude-sonnet-4-6
        """,
    )
    sub = parser.add_subparsers(dest="command", help="Commands")

    # benchmark
    b = sub.add_parser("benchmark", help="Profile a model across 10 dimensions")
    b.add_argument("model", help="Model key (e.g., mock/medium, anthropic/claude-sonnet-4-6)")
    b.add_argument("--tasks", "-t", help="Comma-separated task IDs (default: all)")
    b.add_argument("--seeds", "-s", type=int, default=3, help="Seeds per task (default: 3)")
    b.add_argument("--output", "-o", help="Save profile to JSON file")
    b.add_argument("--save", action="store_true", help="Auto-save profile to data/results/")
    b.set_defaults(func=cmd_benchmark)

    # search
    s = sub.add_parser("search", help="Search for optimal harness configuration")
    s.add_argument("model", help="Model key")
    s.add_argument("--method", "-m", choices=["grid", "random"], default="grid", help="Search method")
    s.add_argument("--num-configs", "-n", type=int, default=100, help="Configurations to try")
    s.add_argument("--output", "-o", help="Save best harness to JSON")
    s.set_defaults(func=cmd_search)

    # evolve
    e = sub.add_parser("evolve", help="Evolve optimal harness genome")
    e.add_argument("model", help="Model key")
    e.add_argument("--generations", "-g", type=int, default=10, help="Generations (default: 10)")
    e.add_argument("--population", "-p", type=int, default=30, help="Population size (default: 30)")
    e.add_argument("--patience", type=int, default=3, help="Early stop patience")
    e.add_argument("--seed", type=int, default=42, help="Random seed")
    e.add_argument("--output", "-o", help="Save results to JSON")
    e.set_defaults(func=cmd_evolve)

    # compile
    c = sub.add_parser("compile", help="Compile optimal harness from profile")
    c.add_argument("model", help="Model key")
    c.add_argument("--profile", "-p", help="Existing profile JSON (runs benchmark if omitted)")
    c.add_argument("--format", "-f", choices=["json", "yaml", "python"], default="yaml")
    c.add_argument("--output", "-o", help="Export file path")
    c.set_defaults(func=cmd_compile)

    # compare
    cmp = sub.add_parser("compare", help="Compare two models")
    cmp.add_argument("model_a", help="First model key")
    cmp.add_argument("model_b", help="Second model key")
    cmp.set_defaults(func=cmd_compare)

    # list
    ls = sub.add_parser("list", help="List available models and tasks")
    ls.set_defaults(func=cmd_list)

    # systems
    sys_p = sub.add_parser("systems", help="Benchmark an AI coding system")
    sys_p.add_argument("system", help="System command or name (e.g., aider, claude)")
    sys_p.add_argument("--repo", "-r", help="Path to repository to benchmark on")
    sys_p.add_argument("--output", "-o", help="Save profile to JSON file")
    sys_p.set_defaults(func=cmd_systems)

    # dashboard
    d = sub.add_parser("dashboard", help="Launch Streamlit dashboard")
    d.add_argument("--port", "-p", type=int, default=8501, help="Port (default: 8501)")
    d.set_defaults(func=cmd_dashboard)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
