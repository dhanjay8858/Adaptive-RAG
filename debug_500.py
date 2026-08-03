import asyncio
import traceback
from src.api.routes import rag_query
from src.models.query_request import QueryRequest
from src.core.config import settings

async def test():
    req = QueryRequest(query="tell me today's news of INDIA?", session_id="test_session")
    try:
        res = await rag_query(req)
        print("Success:", res)
    except Exception as e:
        print("Error occurred!")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
