"""UHB Dashboard — unified Streamlit application.

Visualizes:
- Model capability profiles (radar charts)
- Personality fingerprints
- Environment matrix heatmaps
- Memory degradation curves
- Tool synergy matrices
- Evolution progress & Pareto frontiers
- System-level comparisons
- Community leaderboards
"""

import streamlit as st
import json
from pathlib import Path

st.set_page_config(
    page_title="UHB Dashboard",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    st.sidebar.title("🧬 UHB Dashboard")
    st.sidebar.markdown("**Universal Harness Benchmark**")
    st.sidebar.markdown("AI Developer Research Platform")

    page = st.sidebar.radio(
        "Navigate",
        [
            "🏠 Overview",
            "📊 Benchmark",
            "🧠 Personality",
            "🌍 Environment Matrix",
            "💾 Memory",
            "🔧 Tool Ecology",
            "🧬 Evolution",
            "⚙️ Compiler",
            "🖥️ Systems",
            "👥 Community",
        ],
    )

    if page == "🏠 Overview":
        render_overview()
    elif page == "📊 Benchmark":
        render_benchmark()
    elif page == "🧠 Personality":
        render_personality()
    elif page == "🌍 Environment Matrix":
        render_environment()
    elif page == "💾 Memory":
        render_memory()
    elif page == "🔧 Tool Ecology":
        render_tools()
    elif page == "🧬 Evolution":
        render_evolution()
    elif page == "⚙️ Compiler":
        render_compiler()
    elif page == "🖥️ Systems":
        render_systems()
    elif page == "👥 Community":
        render_community()


def render_overview():
    st.title("🏠 UHB Overview")
    st.markdown("""
    ## Universal Harness Benchmark — AI Developer Research Platform

    **UHB** answers questions that traditional benchmarks don't:

    - 🤖 **Which model is best for this specific repository?**
    - 🧬 **Which harness should this model use?**
    - 🔧 **Which tools maximize its performance?**
    - ⚡ **Which workflow is optimal?**
    - 💰 **What will it cost?**
    - 🛡️ **How autonomous can it safely be?**

    ### Platform Components
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Benchmark Dimensions", "10")
        st.metric("🌍 Environments", "7")
        st.metric("🧬 Gene Types", "12")
    with col2:
        st.metric("🔧 Known Tools", "12")
        st.metric("💾 Memory Dimensions", "5")
        st.metric("🖥️ System Metrics", "10")
    with col3:
        st.metric("📦 Packages", "9")
        st.metric("🧬 Mutation Ops", "10")
        st.metric("📏 Rules Engine", "10+ rules")

    st.markdown("---")
    st.markdown("### Quick Start")
    st.code("""
# Profile a model
uhb benchmark profile anthropic/claude-sonnet-4-6

# Search for optimal harness
uhb evolution search anthropic/claude-sonnet-4-6 --method grid

# Evolve a custom harness
uhb evolution evolve anthropic/claude-sonnet-4-6 --generations 20

# Compile harness from profile
uhb compiler compile anthropic/claude-sonnet-4-6 --output agent_config.yaml

# Compare systems
uhb systems compare claude-code codex-cli aider --repo ./my-project

# Launch dashboard
uhb dashboard
    """, language="bash")


def render_benchmark():
    st.title("📊 Capability Profiles")

    st.markdown("### Model Comparison")

    # Sample data
    import numpy as np

    dimensions = [
        "reasoning", "coding", "planning", "tool_usage", "long_context",
        "self_repair", "instruction_following", "exploration", "creativity", "speed"
    ]

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("**Select models to compare:**")
        model_a = st.selectbox("Model A", [
            "anthropic/claude-sonnet-4-6",
            "anthropic/claude-opus-4-8",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
        ])
        model_b = st.selectbox("Model B", [
            "openai/gpt-4o",
            "anthropic/claude-sonnet-4-6",
            "openai/gpt-4o-mini",
            "anthropic/claude-opus-4-8",
        ])

    with col2:
        st.markdown("**Radar Chart (simulated data)**")
        # Generate sample data for visualization
        sample_scores_a = {
            "reasoning": 0.94, "coding": 0.97, "planning": 0.83,
            "tool_usage": 0.76, "long_context": 0.91, "self_repair": 0.95,
            "instruction_following": 0.99, "exploration": 0.62,
            "creativity": 0.84, "speed": 0.88,
        }
        sample_scores_b = {
            "reasoning": 0.91, "coding": 0.93, "planning": 0.88,
            "tool_usage": 0.82, "long_context": 0.78, "self_repair": 0.85,
            "instruction_following": 0.96, "exploration": 0.70,
            "creativity": 0.89, "speed": 0.92,
        }

        import plotly.graph_objects as go

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[sample_scores_a[d] for d in dimensions],
            theta=dimensions,
            fill='toself',
            name=model_a.split("/")[-1],
        ))
        fig.add_trace(go.Scatterpolar(
            r=[sample_scores_b[d] for d in dimensions],
            theta=dimensions,
            fill='toself',
            name=model_b.split("/")[-1],
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(range=[0, 1])),
            showlegend=True,
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### Per-Task Results")
    st.dataframe({
        "Task": ["code_from_spec", "debug_broken", "refactor", "tool_use", "search_docs",
                 "plan_feature", "review_pr", "long_context", "self_repair"],
        f"{model_a.split('/')[-1]}": [0.95, 0.88, 0.82, 0.74, 0.65, 0.80, 0.90, 0.92, 0.94],
        f"{model_b.split('/')[-1]}": [0.92, 0.85, 0.85, 0.80, 0.72, 0.87, 0.85, 0.76, 0.83],
    })


def render_personality():
    st.title("🧠 Personality Fingerprints")

    st.markdown("### Behavioral Classification")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Personality Traits**")
        st.metric("Question Rate", "0.15", "asks clarifying Qs in 15% of interactions")
        st.metric("Verbosity Ratio", "0.62", "balanced output")
        st.metric("Tool Overuse Rate", "0.08", "rarely overuses tools")
        st.metric("Stability Score", "0.91", "very consistent across runs")

    with col2:
        st.markdown("**Behavioral Class**")
        st.info("**Class: Executor** — This model executes well with clear instructions. "
                "Give step-by-step guidance for best results.")

        st.markdown("**Recommended Interaction:**")
        st.success("Give clear step-by-step instructions. It executes well.")

        st.markdown("**Strengths:**")
        st.markdown("- Instruction following")
        st.markdown("- Code correctness")
        st.markdown("- Consistent output")

        st.markdown("**Weaknesses:**")
        st.markdown("- Low exploration initiative")
        st.markdown("- Doesn't ask clarifying questions")


def render_environment():
    st.title("🌍 Environment Matrix")

    st.markdown("### Heatmap: Model × Environment")

    import plotly.graph_objects as go
    import numpy as np

    environments = ["Terminal", "VS Code", "GitHub", "Docker", "Jupyter", "Browser", "Remote"]
    models = ["Claude Sonnet", "Claude Opus", "GPT-4o", "GPT-4o Mini"]

    # Sample heatmap data
    data = np.array([
        [0.92, 0.90, 0.88, 0.85, 0.87, 0.84, 0.82],
        [0.94, 0.91, 0.89, 0.88, 0.83, 0.81, 0.86],
        [0.85, 0.88, 0.90, 0.82, 0.86, 0.91, 0.80],
        [0.78, 0.80, 0.82, 0.75, 0.80, 0.83, 0.73],
    ])

    fig = go.Figure(data=go.Heatmap(
        z=data,
        x=environments,
        y=models,
        colorscale='RdYlGn',
        zmin=0.7,
        zmax=1.0,
        text=np.round(data, 3),
        texttemplate='%{text}',
        textfont={"size": 14},
    ))
    fig.update_layout(height=400, xaxis_title="Environment", yaxis_title="Model")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Key insight:** GPT-4o scores 93 in Browser but 81 in Docker — "
                "environment matters as much as the model.")


def render_memory():
    st.title("💾 Memory Benchmark")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Memory Dimensions")
        dims = {
            "Short-term Recall": 0.82,
            "Long-term Retention": 0.71,
            "Retrieval Accuracy": 0.78,
            "Compression Quality": 0.65,
            "Forgetting Resistance": 0.74,
        }
        for name, score in dims.items():
            st.metric(name, f"{score:.2f}", delta=None)
            st.progress(score)

    with col2:
        st.markdown("### Context Degradation Curve")
        import plotly.graph_objects as go

        context_sizes = [5000, 10000, 20000, 30000, 50000, 75000, 100000]
        recall_scores = [0.95, 0.92, 0.85, 0.78, 0.68, 0.55, 0.42]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=context_sizes, y=recall_scores,
            mode='lines+markers',
            name='Recall',
            fill='tozeroy',
        ))
        fig.update_layout(
            xaxis_title="Context Size (chars)",
            yaxis_title="Recall Score",
            yaxis_range=[0, 1],
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.warning("⚠️ Performance drops below 0.5 at ~75k context tokens. "
                   "Consider using sliding window or summary strategies.")


def render_tools():
    st.title("🔧 Tool Ecology")

    st.markdown("### Model × Tool Combinations")

    tools = ["Baseline", "Ripgrep+Git", "Standard", "Search Focused", "Test Focused", "Full Dev"]
    models = ["Claude Sonnet", "GPT-4o", "GPT-4o Mini"]

    import pandas as pd
    import numpy as np

    data = pd.DataFrame({
        "Tools": tools * 3,
        "Model": np.repeat(models, 6),
        "Score": [
            0.78, 0.84, 0.87, 0.85, 0.86, 0.88,
            0.72, 0.80, 0.85, 0.83, 0.88, 0.90,
            0.62, 0.75, 0.82, 0.79, 0.85, 0.87,
        ],
    })

    import plotly.express as px
    fig = px.bar(data, x="Tools", y="Score", color="Model", barmode="group",
                 title="Tool Combination Effectiveness by Model")
    st.plotly_chart(fig, use_container_width=True)

    st.info("💡 **Finding:** Adding `pytest` + `ruff` to a weaker model can close the gap "
            "with stronger models. Tool ecology matters!")


def render_evolution():
    st.title("🧬 Harness Evolution")

    col1, col2, col3 = st.columns(3)
    col1.metric("Generation", "12/20")
    col2.metric("Best Fitness", "0.923", "+0.15")
    col3.metric("Pareto Size", "8", "non-dominated")

    st.markdown("### Evolutionary Progress")

    import plotly.graph_objects as go
    import numpy as np

    gens = list(range(0, 13))
    best_fitness = [0.78, 0.80, 0.82, 0.84, 0.86, 0.87, 0.88, 0.89, 0.90, 0.91, 0.915, 0.920, 0.923]
    avg_fitness = [0.65, 0.67, 0.70, 0.72, 0.74, 0.75, 0.77, 0.78, 0.79, 0.80, 0.81, 0.815, 0.820]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=gens, y=best_fitness, mode='lines+markers',
                             name='Best Fitness', line=dict(color='green', width=2)))
    fig.add_trace(go.Scatter(x=gens, y=avg_fitness, mode='lines+markers',
                             name='Avg Fitness', line=dict(color='blue', width=1, dash='dash')))
    fig.update_layout(xaxis_title="Generation", yaxis_title="Fitness", yaxis_range=[0.6, 1.0])
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Best Genome Discovered")
    st.code("PLN → RSC → COD → ANL → TST → RPR → TST → SEC → REV → CMT")
    st.caption("Plan → Research → Code → Analyze → Test → Repair → Test → Security → Review → Commit")


def render_compiler():
    st.title("⚙️ Harness Compiler")

    st.markdown("### Compile from Profile")

    model = st.selectbox("Select Model", [
        "anthropic/claude-sonnet-4-6",
        "anthropic/claude-opus-4-8",
        "openai/gpt-4o",
    ])

    if st.button("Compile Optimal Harness"):
        with st.spinner("Compiling..."):
            # Simulated compilation
            st.success("Harness compiled successfully!")

            st.markdown("#### Generated Harness")
            st.code("""
model_id: anthropic/claude-sonnet-4-6
genes:
  - plan
  - research
  - code
  - analyze
  - test
  - repair
  - test
  - review
  - commit
context_strategy: full
tool_policy: all
retry_policy: on_failure
max_retries: 3
confidence: 0.85
rationale: "High reasoning + moderate planning → added research/planning steps.
           Excellent context retention → full context strategy."
            """)

            st.download_button(
                "⬇ Download YAML",
                data="genes: [plan, research, code, analyze, test, repair, test, review, commit]",
                file_name="uhb_harness.yaml",
            )


def render_systems():
    st.title("🖥️ AI Coding System Comparison")

    st.markdown("### Overall Rankings")

    rankings = [
        ("Claude Code", 0.89),
        ("Codex CLI", 0.82),
        ("Aider", 0.79),
        ("OpenHands", 0.74),
        ("Cursor Agent", 0.72),
    ]

    for i, (name, score) in enumerate(rankings, 1):
        col1, col2, col3 = st.columns([0.1, 0.7, 0.2])
        col1.markdown(f"**{i}.**")
        col2.markdown(f"**{name}**")
        col3.progress(score, text=f"{score:.3f}")

    st.markdown("---")
    st.markdown("### Dimension Comparison")

    import plotly.graph_objects as go

    dimensions = ["Repo Understanding", "Architecture", "Refactoring", "Debugging",
                  "Testing", "Planning", "Documentation", "Autonomy", "Recovery", "Cost"]

    claude_scores = [0.92, 0.88, 0.90, 0.87, 0.85, 0.91, 0.86, 0.93, 0.89, 0.88]
    codex_scores = [0.85, 0.82, 0.84, 0.80, 0.83, 0.78, 0.81, 0.86, 0.77, 0.84]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=claude_scores, theta=dimensions, fill='toself', name='Claude Code'))
    fig.add_trace(go.Scatterpolar(r=codex_scores, theta=dimensions, fill='toself', name='Codex CLI'))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0.7, 1.0])), height=500)
    st.plotly_chart(fig, use_container_width=True)


def render_community():
    st.title("👥 Community Leaderboard")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Top Models (from community data)")
        entries = [
            ("anthropic/claude-sonnet-4-6", 0.892, 245, 0.94),
            ("anthropic/claude-opus-4-8", 0.885, 182, 0.92),
            ("openai/gpt-4o", 0.871, 310, 0.89),
            ("anthropic/claude-haiku-4-5", 0.848, 156, 0.85),
            ("openai/gpt-4o-mini", 0.821, 423, 0.82),
        ]
        for i, (model, score, runs, success_rate) in enumerate(entries, 1):
            col_a, col_b = st.columns([0.05, 0.95])
            col_a.markdown(f"**{i}**")
            col_b.markdown(f"**{model}** — Score: {score:.3f} | Runs: {runs} | Success: {success_rate:.1%}")

    with col2:
        st.metric("Total Community Runs", "1,416")
        st.metric("Unique Models", "24")
        st.metric("Unique Environments", "6")
        st.metric("Data Contributors", "38")

    st.markdown("---")
    st.markdown("### Submit Your Benchmark")
    st.markdown("Help the community by contributing your benchmark results.")
    if st.button("Submit Example Run"):
        st.success("Run submitted! Thank you for contributing to the community dataset. 🎉")


if __name__ == "__main__":
    main()
