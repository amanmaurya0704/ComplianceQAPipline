'''
This module defines the DAG: Directed Acyclic Graph that orchestrates the video compliance audit process.
It connects the nodes using the StateGraph from Lnaggraph

START -> index_video_node -> audit_content_node -> END
'''

from langgraph.graph import StateGraph, END
from backend.src.graph.state import VideoAuditState
from backend.src.graph.nodes import(
    index_video_node,
    audio_content_node
)

def create_graph():
    '''
    Construct and Compile the langgraph workflow

    Returns:
    Compiled Graph: runnable graph object for execution
    '''

    # initalise the graph with state schema
    workflow = StateGraph(VideoAuditState)
    # add the nodes 
    workflow.add_node("indexer", index_video_node)
    workflow.add_node("auditor", audio_content_node)
    #define the edges
    #efine the entry point
    workflow.set_entry_point("indexer")
    workflow.add_edge("indexer","auditor")
    workflow.add_edge("auditor",END)

    app = workflow.compile()

    return app

app = create_graph()
