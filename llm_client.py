import os
from openai import OpenAI, RateLimitError, APIError, AuthenticationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests
import ai_model

class LLMClient:
    def __init__(self, model: str = ai_model.model_name):
        self.api_key = ai_model.api_key
        self.base_url = ai_model.base_url
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.model = model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        # 仅对限流和临时网络错误重试，认证错误直接抛出以便快速定位
        retry=retry_if_exception_type((RateLimitError, APIError))
    )
    def chat_completion(self, messages: list, tools: list = None):


        kwargs = {
            "model": self.model, 
            "messages": messages, 
            "timeout": 60
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        return self.client.chat.completions.create(**kwargs)