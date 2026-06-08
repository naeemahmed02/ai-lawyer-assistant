from ..rag.rag_pipeline import RAGPipeline
from asgiref.sync import async_to_sync
from ...services.llm.exception import LLMGenerationError


class RagService:

    def generate(
        self,
        *,
        query,
        case_id,
        history,
    ):

        rag_pipeline = RAGPipeline()

        response = async_to_sync(rag_pipeline.run)(
            query=query,
            case_id=case_id,
            history=history,
        )

        if not response:
            raise LLMGenerationError("Empty response received from pipeline.")

        return response
