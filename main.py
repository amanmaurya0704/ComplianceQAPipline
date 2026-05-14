'''
Main execution point for azure-comp-orestration.
'''

import uuid
import json
import logging
from pprint import pprint
from dotenv import load_dotenv
load_dotenv(override=True)

from backend.src.graph.workflow import app

logging.basicConfig(level=logging.INFO, format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Compliance Orchestration Runner")

def run_cli_simulation():
    '''
    Simulate the video compliance audit request
    '''

    session_id = str(uuid.uuid4())
    logger.info(f"Starting compliance audit simulation with session ID: {session_id}")

    initial_input = {
        'video_url': "https://youtu.be/dT7S75eYhcQ",
        'video_id': f"vid_{session_id}",
        'compliance_result': [],
        'errors':[]
    }
    print("n-------------Initializing workflow ------------- ")
    print(f"Input Payload: {json.dumps(initial_input, indent=2)}")

    try:
        final_state = app.invoke(initial_input)
        print("\n-------------Workflow Execution Completed-------------")

        print("\n Compliance Audit Report--")
        print(f"Video ID: {final_state['video_id']}")
        print(f"Status: {final_state.get('final_status')}")
        print("\n [Voilation Detected]")

        results = final_state.get("compliance_result", [])

        if results:
            for issue in results:
                print(f" - [{issue.get('severity').upper()}] [{issue.get('category')}] [{issue.get('description')}]")
        else:
            print("No compliance issues detected. Video is compliant!")

        print("\n[Final Summary]")
        print(final_state.get('final_report'))
    except Exception as e:
        logger.error(f"Error during workflow execution: {e}")
        print("\nWorkflow execution failed. Please check logs for details.")

if __name__ == "__main__":
    run_cli_simulation()
