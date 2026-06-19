# context.py
import tiktoken
from typing import List, Dict
import ai_model

class ConversationContext:
    def __init__(self, model: str = ai_model.model_name, max_tokens_threshold: int = 100_000):
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        self.messages: List[Dict] = []
        self.max_threshold = max_tokens_threshold
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def add_message(self, role: str, content: str, **kwargs):
        msg = {"role": role, "content": content}
        msg.update(kwargs)
        self.messages.append(msg)
        self.total_input_tokens += self._count_tokens(msg)

    def estimate_current_tokens(self) -> int:
        return sum(self._count_tokens(m) for m in self.messages)

    def apply_threshold_strategy(self):
        """超过阈值时：保留 system + 最后N轮对话"""
        while self.estimate_current_tokens() > self.max_threshold and len(self.messages) > 2:
            # 保留第一条(system)和最后 4 条消息
            keep = [self.messages[0]] + self.messages[-4:]
            self.messages = keep

    def _count_tokens(self, message: Dict) -> int:
        # 这个是AI给我的tokens预测算式时
        tokens = len(self.encoding.encode(message.get("content", "")))
        if message.get("tool_calls"):
            tokens += len(self.encoding.encode(str(message["tool_calls"])))
        tokens += 3  # role + formatting overhead
        return tokens