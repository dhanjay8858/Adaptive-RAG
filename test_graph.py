import sys
from src.rag.graph_builder import builder

def test():
    print("Testing graph builder with web search...")
    try:
        res = builder.invoke({
            "messages": [("user", "tell me today's news of INDIA?")]
        })
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
