# observability.py
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from context import ConversationContext

class TrajectoryLogger:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, f"{run_id}.jsonl")
        self.steps = []

    def log_step(self, event: str, data: Dict[str, Any]):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "run_id": self.run_id,
            "event": event,
            "data": data
        }
        self.steps.append(entry)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def finalize(self, ctx: ConversationContext, input_cost_per_m: float, output_cost_per_m: float):
        total_input = ctx.total_input_tokens
        total_output = ctx.total_output_tokens
        cost = (total_input * input_cost_per_m + total_output * output_cost_per_m) / 1_000_000
        summary = {
            "run_id": self.run_id,
            "total_steps": len(self.steps),
            "input_tokens": total_input,
            "output_tokens": total_output,
            "estimated_cost_usd": round(cost, 5),
            "completed_at": datetime.now().isoformat()
        }
        self.log_step("summary", summary)
        return summary