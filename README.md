# 🧬 UHB — Universal Harness Benchmark

## AI Developer Research Platform

**One command to benchmark any model. No API key needed to try it.**

```bash
./setup.sh                        # Install everything
uhb benchmark mock/medium         # Profile a mock model (no API key)
uhb evolve mock/strong            # Evolve optimal harness
uhb compare mock/strong mock/weak # Compare two models
uhb dashboard                     # Launch visualization
```

---

## What UHB Answers

Traditional benchmarks ask: **"Which model is best?"**

UHB asks:
- 🤖 Which model is best **for this repository**?
- 🧬 Which **harness** should this model use?
- 🔧 Which **tools** maximize its performance?
- ⚡ Which **workflow** is optimal?
- 💰 What will it **cost**?
- 🛡️ How **autonomous** can it safely be?

---

## Quick Start

### 1. Install

```bash
cd uhb
bash setup.sh
```

That's it. No API keys, no config — works immediately with mock models.

### 2. Test with mock models

```bash
# Profile a mock model (simulates a mid-tier LLM)
uhb benchmark mock/medium

# Compare two mock models
uhb compare mock/strong mock/weak

# Search for optimal harness configuration
uhb search mock/medium --method grid --num-configs 100

# Evolve a harness genome
uhb evolve mock/strong --generations 10 --population 30
```

### 3. Use real models

```bash
export ANTHROPIC_API_KEY=sk-ant-...
uhb benchmark anthropic/claude-sonnet-4-6

export OPENAI_API_KEY=sk-...
uhb benchmark openai/gpt-4o
```

### 4. Visualize

```bash
uhb dashboard
# Open http://localhost:8501
```

---

## Commands

| Command | What it does |
|---|---|
| `uhb benchmark <model>` | Profile across 10 capability dimensions |
| `uhb search <model>` | Grid/random search for optimal harness |
| `uhb evolve <model>` | Genetic algorithm for harness optimization |
| `uhb compile <model>` | Generate optimal harness from profile |
| `uhb compare <a> <b>` | Side-by-side model comparison |
| `uhb systems <system>` | Benchmark an AI coding system (Claude Code, etc.) |
| `uhb dashboard` | Launch Streamlit visualization |
| `uhb list` | Show available models and tasks |

---

## Architecture

```
uhb/
├── uhb                  ← Unified CLI (one command to rule them all)
├── setup.sh             ← One-command install
├── uhb-core/            ← LLM abstraction + mock backend
├── uhb-benchmark/       ← 9 tasks × 10 dimensions
├── uhb-evolution/       ← Harness Genome 🧬 + genetic algorithm
├── uhb-compiler/        ← Meta-learning rules engine
├── uhb-environment/     ← 7 dev environment simulators
├── uhb-personality/     ← Behavioral fingerprinting
├── uhb-memory/          ← Memory benchmark (5 dimensions)
├── uhb-tools/           ← Tool ecology (12 tools × model matrix)
├── uhb-systems/         ← System-level benchmarking
├── uhb-community/       ← Community dataset + leaderboards
└── uhb-dashboard/       ← Streamlit visualization
```

## The Harness Genome 🧬

Every harness is DNA:

```
PLAN → RESEARCH → CODE → ANALYZE → TEST → REPAIR → TEST → REVIEW → COMMIT
```

12 gene types. 10 mutation operators. Evolves through genetic algorithm:

| Operator | Effect |
|---|---|
| `reorder` | Swap two steps |
| `duplicate` | Double a step (e.g., TEST → TEST → TEST) |
| `remove` | Delete a step |
| `merge` | Combine adjacent steps |
| `split` | Expand one step into two |
| `conditional` | Add if-then branching |
| `insert` | Add a new step |

## Mock Models

Built-in simulated models for instant testing:

| Model | Coding | Reasoning | Planning | Notes |
|---|---|---|---|---|
| `mock/strong` | 0.95 | 0.92 | 0.90 | Near-perfect |
| `mock/medium` | 0.75 | 0.70 | 0.65 | Mid-tier |
| `mock/weak` | 0.50 | 0.45 | 0.40 | Struggling |
| `mock/flaky` | 0.85 | 0.80 | 0.75 | 20% failure rate |

## Benchmarked Systems (Killer Feature)

Benchmark entire AI coding systems as black boxes:
- **Claude Code** — Anthropic's agentic coding CLI
- **Codex CLI** — OpenAI's coding agent
- **Aider** — Open-source AI pair programmer
- **OpenHands** — Autonomous coding agent
- **Cursor Agent** — IDE-integrated agent
- **Your own agent** — Plug in any system

---

## System Benchmark Dimensions

| Dimension | What's measured |
|---|---|
| Repository Understanding | Can it navigate and explain the codebase? |
| Architecture | Can it reason about system design? |
| Refactoring | Can it improve code without breaking? |
| Debugging | Can it find and fix bugs? |
| Testing | Can it write good tests? |
| Planning | Can it decompose complex tasks? |
| Documentation | Can it generate useful docs? |
| Autonomy | How much can it do without human input? |
| Recovery | Can it fix its own mistakes? |
| Cost | Total $ per completed task |
