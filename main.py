from agent import SimpleAgent
agent = SimpleAgent()
x = input("请输入您的要求：")
answer = agent.run(x)
print("最终回答：", answer)