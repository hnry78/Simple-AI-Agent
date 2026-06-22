# agent.py
import uuid
import json
import sys
import platform
from datetime import datetime
from typing import List, Dict, Any
from tools import TOOL_REGISTRY
from context import ConversationContext
from llm_client import LLMClient
from observability import TrajectoryLogger
import ai_model

class SimpleAgent:
    def __init__(self, model: str = ai_model.model_name, max_turns: int = 15, ctx_threshold: int = 80000):
        self.llm = LLMClient(model)
        self.ctx = ConversationContext(model, ctx_threshold)
        self.max_turns = max_turns
        self.run_id = uuid.uuid4().hex[:12]
        self.logger = TrajectoryLogger(self.run_id)
        self.tools_schema = [
            {"type": "function", "function": {"name": "calculator", "description": "Evaluate a math expression", "parameters": {"type": "object", "properties": {"expr": {"type": "string"}}, "required": ["expr"]}}},
            {"type": "function", "function": {"name": "read_file", "description": "Read file content", "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}}},
            {"type": "function", "function": {"name": "write_file", "description": "Write content to file", "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}, "content": {"type": "string"}}, "required": ["filepath", "content"]}}},
            {"type": "function", "function": {"name": "run_bash", "description": "Run a shell command.Use Python via: python -c \"...\"  ", "parameters": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}}},
            {"type": "function", "function": {"name": "delete_file", "description": "Delete a file", "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}}},
        ]

    @staticmethod
    def detect_env() -> str:
        os_name = platform.system()
        info = [
            f"OS: {os_name}",
            f"Platform: {sys.platform}",
            f"Python: {sys.version}",
        ]
        if os_name == "Windows":
            info.append("Tip: Use 'python' (not 'python3') and 'dir' (not 'ls') in shell commands.")
        else:
            info.append("Tip: Use 'python3' in shell commands.")
        return "\n".join(info)

    def run(self, user_prompt: str) -> str:
        env_info = self.detect_env()
        self.ctx.add_message("system", (
            "You are a helpful assistant. Use tools when needed.\n\n"
            f"### Current Environment\n{env_info}\n\n"
            "Turn efficiency guidelines (each turn costs LLM inference — minimize turns):\n"
            "- PLAN AHEAD: Think through the full solution, then EXECUTE in the fewest possible tools calls. "
            "Prefer one comprehensive Python script over multiple sequential steps.\n"
            "- BATCH read+process+output: Instead of: read file → analyze step1 → analyze step2 → write output (4 turns), "
            "do: read file → write & run ONE Python script that does all processing + generates output (2 turns).\n"
            "- Prefer writing a .py file and running it: for multi-step logic, write a complete Python script "
            "via write_file, then run it via run_bash. This avoids splitting work across multiple turns.\n"
            "- For batch math (mean, stdev, etc.), use one Python one-liner or script, not individual calculator calls.\n"
            "- Use Python's statistics/csv/pandas modules when processing tabular data — do all analysis in one shot."
        ))
        self.ctx.add_message("user", user_prompt)
        self.logger.log_step("init", {"prompt": user_prompt})

        for turn in range(1, self.max_turns + 1):
            self.ctx.apply_threshold_strategy()
            self.logger.log_step("context_trim", {"tokens_before": self.ctx.estimate_current_tokens()})
            response = self.llm.chat_completion(self.ctx.messages, self.tools_schema)
            print(f"DEBUG: response type = {type(response)}, value = {response}") # 🔍 打印查看
            msg = response.choices[0].message
            self.ctx.add_message(msg.role, msg.content, tool_calls=msg.tool_calls)
            self.ctx.total_output_tokens += response.usage.completion_tokens
            self.logger.log_step("llm_response", {"turn": turn, "tool_calls": bool(msg.tool_calls)})

            if not msg.tool_calls:
                final_answer = msg.content
                self.logger.log_step("finish", {"answer": final_answer})
                return final_answer

            # 执行工具和错误恢复
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                self.logger.log_step("tool_call", {"name": fn_name, "args": fn_args})

                try:
                    if fn_name in TOOL_REGISTRY:
                        res = TOOL_REGISTRY[fn_name](**fn_args)
                    else:
                        res = {"status": "error", "output": f"Tool '{fn_name}' not found"}
                except Exception as e:
                    res = {"status": "error", "output": f"ExecutionError: {e}"}

                # 工具结果回写 Context，供下一轮 LLM 参考
                self.ctx.add_message("tool", json.dumps(res), tool_call_id=tc.id)
                self.logger.log_step("tool_result", res)

        return f"[Stop] Reached max turns ({self.max_turns}). Last context: ..."