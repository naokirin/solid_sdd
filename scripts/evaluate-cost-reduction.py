#!/usr/bin/env python3
"""Evaluate execution cost and Task launch reduction between Before and After models.

This script compares the traditional fine-grained solid_sdd execution model
against the consolidated slice / checkpoint model introduced in docs/cost-reduction-plan.md.
"""
import json
import sys
from pathlib import Path


def evaluate_arithmetic_api() -> dict[str, any]:
    # Analysis based on examples/arithmetic-api/work-plan.json (11 Scenarios)
    
    # --- BEFORE MODEL ---
    # 11 WorkPlan items (W1-W11)
    # Outer: intake + critique + brief + critique + decompose + critique + integration verify + critique = 8 Tasks
    # Each item loop (11 items):
    #   judge (1) + critique (1) + apply-api (1) + critique (1) + apply-dbc (1) + critique (1)
    #   + derive-tests (1) + critique (1) + implement (1) + verify (1) + critique (1) = 11 Tasks/item
    # Total Before = 8 + (11 * 11) = 129 Tasks!
    # Critique count Before = 4 (outer) + (11 * 5) = 59 Critiques
    
    before_item_count = 11
    before_tasks_per_item = 11
    before_outer_tasks = 8
    before_total_tasks = before_outer_tasks + (before_item_count * before_tasks_per_item)
    before_critiques = 4 + (before_item_count * 5)
    # Average task latency estimated at ~25 seconds (including subagent spin up & API response)
    before_est_time_minutes = (before_total_tasks * 25) / 60.0

    # --- AFTER MODEL (cost-reduction-plan.md) ---
    # WorkPlan grouped into 2 Coherent Slices:
    #   Slice 1: Calculator Operations (Add/Sub/Mul/Div/Rem + Zero Divisor errors)
    #   Slice 2: Single-slot Memory Operations (Clear/Recall/Add/Subtract)
    # Outer: intake + brief + decompose + critique(work_plan) + integration verify + critique(integration) = 6 Tasks
    # Each Slice loop (2 Slices):
    #   Plan Slice (1) + Implement Slice (1) + Verify Slice (1) = 3 Tasks/slice
    # Critique count After: 2 (WorkPlan Review + Integration Review) (plus Failure-Driven only on error)
    
    after_item_count = 2
    after_tasks_per_slice = 3
    after_outer_tasks = 4
    after_total_tasks = after_outer_tasks + (after_item_count * after_tasks_per_slice)
    after_critiques = 2
    after_est_time_minutes = (after_total_tasks * 25) / 60.0

    task_reduction_pct = ((before_total_tasks - after_total_tasks) / before_total_tasks) * 100
    critique_reduction_pct = ((before_critiques - after_critiques) / before_critiques) * 100
    time_reduction_pct = ((before_est_time_minutes - after_est_time_minutes) / before_est_time_minutes) * 100

    return {
        "example": "examples/arithmetic-api",
        "before": {
            "workplan_items": before_item_count,
            "total_tasks": before_total_tasks,
            "critique_launches": before_critiques,
            "estimated_minutes": round(before_est_time_minutes, 1),
        },
        "after": {
            "workplan_slices": after_item_count,
            "total_tasks": after_total_tasks,
            "critique_launches": after_critiques,
            "estimated_minutes": round(after_est_time_minutes, 1),
        },
        "reduction": {
            "task_count_savings_pct": round(task_reduction_pct, 1),
            "critique_count_savings_pct": round(critique_reduction_pct, 1),
            "estimated_time_savings_pct": round(time_reduction_pct, 1),
        }
    }


def main():
    res = evaluate_arithmetic_api()
    print("=== solid_sdd Cost & Time Reduction Comparison ===")
    print(f"Target Example: {res['example']}\n")
    print(f"BEFORE Model (Micro-Tasks & Multi-Pass Critique):")
    print(f"  - WorkPlan Items: {res['before']['workplan_items']}")
    print(f"  - Total Subagent Tasks: {res['before']['total_tasks']}")
    print(f"  - Critique Launches: {res['before']['critique_launches']}")
    print(f"  - Estimated Wall-Clock Time: ~{res['before']['estimated_minutes']} minutes\n")

    print(f"AFTER Model (Coherent Slices, Plan->Implement->Verify, Checkpoint Critique):")
    print(f"  - WorkPlan Slices: {res['after']['workplan_slices']}")
    print(f"  - Total Subagent Tasks: {res['after']['total_tasks']}")
    print(f"  - Critique Launches: {res['after']['critique_launches']}")
    print(f"  - Estimated Wall-Clock Time: ~{res['after']['estimated_minutes']} minutes\n")

    print(f"REDUCTION HIGHLIGHTS:")
    print(f"  - Task Launch Reduction: -{res['reduction']['task_count_savings_pct']}%")
    print(f"  - Critique Launch Reduction: -{res['reduction']['critique_count_savings_pct']}%")
    print(f"  - Wall-Clock Time Savings: -{res['reduction']['estimated_time_savings_pct']}%\n")

if __name__ == "__main__":
    main()
