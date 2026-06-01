from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .nodes import make_classify_node
from .state import AgentState


def build_graph(model: BaseChatModel, review_threshold: float = 0.7) -> CompiledStateGraph:
    builder = StateGraph(AgentState)
    builder.add_node("classify", make_classify_node(model, review_threshold))
    builder.add_edge(START, "classify")
    builder.add_edge("classify", END)
    return builder.compile()
