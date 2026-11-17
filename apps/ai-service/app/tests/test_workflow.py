from app.graph.workflow import build_workflow


class FakeAgent:
    async def __call__(self, state):
        return {}


class FakeRAGAgent:
    async def answer_question(self, question, project_id):
        return {
            "answer": "Test answer",
            "sources": [],
        }


def test_workflow_compiles():
    workflow = build_workflow(
        supervisor_agent=FakeAgent(),
        work_items_agent=FakeAgent(),
        users_agent=FakeAgent(),
        rag_agent=FakeRAGAgent(),
        generation_agent=FakeAgent(),
    )

    assert workflow is not None
