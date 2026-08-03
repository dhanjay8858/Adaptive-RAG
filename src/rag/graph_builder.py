"""
Graph builder module for the adaptive RAG system.
"""

from langchain_community.tools import TavilySearchResults, DuckDuckGoSearchRun
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate
from langgraph.constants import START, END
from langgraph.graph.state import StateGraph

from src.rag.reAct_agent import get_agent_executor
from src.rag.retriever_setup import get_retriever
from src.config.settings import Config
from src.llms.llm_setup import llm, get_structured_llm
from src.models.grade import Grade
from src.models.route_identifier import RouteIdentifier
from src.models.state import State
from src.tools.graph_tools import routing_tool, doc_tool

config = Config()


# Node implementations
def query_classifier(state: State):
    """
    Classify the query to determine if it's related to indexed documents.

    Args:
        state (State): The current state of the graph.

    Returns:
        dict: Updated state with route and latest_query.
    """
    question = state["messages"][-1].content
    
    # Format history for the prompt
    history_lines = []
    for msg in state["messages"][:-1]:
        role = "User" if msg.type == "human" else "AI"
        history_lines.append(f"{role}: {msg.content}")
    history_str = "\n".join(history_lines) if history_lines else "No previous history."
    
    retriever = get_retriever()
    context = retriever.invoke(question)
    print("docs received from Qdrant")
    print(context)

    llm_with_structured_output = get_structured_llm(RouteIdentifier)
    classify_prompt = PromptTemplate(
        template=config.prompt("classify_prompt"),
        input_variables=["question", "context", "history"]
    )
    chain = classify_prompt | llm_with_structured_output
    result = chain.invoke({"question": question, "context": context, "history": history_str})
    print("result received is in query classifier")
    print(result.route)

    return {"messages": state["messages"], "route": result.route, "latest_query": question}


def general_llm(state: State):
    """
    Fetch general common knowledge result from the LLM.

    Args:
        state (State): The current state of the graph.

    Returns:
        dict: Updated messages from LLM.
    """
    result = llm.invoke(state["messages"])
    print("inside general llm")
    print(result)
    return {"messages": result}


def retriever_node(state: State):
    """
    Retrieve results from vector stores using the reAct agent.

    Args:
        state (State): The current state of the graph.

    Returns:
        dict: Updated messages with tool calls.
    """
    messages = state["latest_query"]
    agent_executor = get_agent_executor()
    result = agent_executor.invoke({"input": messages})

    # Extract tool calls
    intermediate_steps = result.get("intermediate_steps", [])
    tool_calls = []
    if intermediate_steps:
        for action, tool_result in intermediate_steps:
            tool_calls.append({
                "tool": action.tool,
                "input": action.tool_input,
            })

    new_message = AIMessage(
        content=result["output"],
        additional_kwargs={"tool_calls": tool_calls},
    )

    return {
        "messages": [new_message]
    }


def grade(state: State):
    """
    Grade the results retrieved from vector stores.

    Args:
        state (State): The current state of the graph.

    Returns:
        dict: Updated state with binary_score.
    """
    grading_prompt = PromptTemplate(
        template=config.prompt("grading_prompt"),
        input_variables=["question", "context"]
    )
    context = state["messages"][-1].content
    question = state["latest_query"]

    llm_with_grade = get_structured_llm(Grade)

    chain_graded = grading_prompt | llm_with_grade
    result = chain_graded.invoke({"question": question, "context": context})

    print(result)
    return {"messages": state["messages"], "binary_score": result.binary_score}


def rewrite_query(state: State):
    """
    Rewrite the query to get better retrieval results.

    Args:
        state (State): State of the question.

    Returns:
        dict: Updated latest_query.
    """
    query = state["latest_query"]
    rewrite_prompt = PromptTemplate(
        template=config.prompt("rewrite_prompt"),
        input_variables=["query"]
    )
    chain = rewrite_prompt | llm
    result = chain.invoke({"query": query})
    print(result)

    return {
        "latest_query": result.content
    }


def generate(state: State):
    """
    Generate the final answer for the user.

    Args:
        state (State): State of the question.

    Returns:
        dict: Generated response.
    """
    context = state["messages"][-1].content

    generate_prompt = PromptTemplate(
        template=config.prompt("generate_prompt"),
        input_variables=["context"]
    )

    generate_chain = generate_prompt | llm
    result = generate_chain.invoke({"context": context})

    return {"messages": [{"role": "assistant", "content": result.content}]}


def web_search(state: State):
    """
    Search the web for the rewritten query.

    Args:
        state (State): The current state of the graph.

    Returns:
        dict: Search results as messages.
    """
    try:
        # Initialize the Tavily tool
        search_tool = TavilySearchResults()
        result = search_tool.invoke(state["latest_query"])
        
        if isinstance(result, list):
            contents = [item["content"] for item in result if "content" in item]
        else:
            contents = [str(result)]
    except Exception as e:
        print(f"Tavily search failed: {e}. Falling back to DuckDuckGo.")
        try:
            search_tool = DuckDuckGoSearchRun()
            result = search_tool.invoke(state["latest_query"])
            contents = [str(result)]
        except Exception as e2:
            print(f"DuckDuckGo search failed: {e2}")
            contents = ["I'm sorry, I couldn't search the web right now. Both Tavily and DuckDuckGo search services are currently unavailable or rate-limited. Please try again later."]
        
    print(contents)

    return {
        "messages": [{"role": "assistant", "content": "\n\n".join(contents)}]
    }


# Build the graph
graph = StateGraph(State)

graph.add_node("query_analysis", query_classifier)
graph.add_node("retriever", retriever_node)
graph.add_node("grade", grade)
graph.add_node("generate", generate)
graph.add_node("rewrite", rewrite_query)
graph.add_node("web_search", web_search)
graph.add_node("general_llm", general_llm)

graph.add_edge(START, "query_analysis")
graph.add_edge("web_search", "generate")
graph.add_edge("retriever", "grade")
graph.add_edge("rewrite", "retriever")
graph.add_conditional_edges("query_analysis", routing_tool)
graph.add_conditional_edges("grade", doc_tool)
graph.add_edge("generate", END)
graph.add_edge("general_llm", END)

builder = graph.compile()

