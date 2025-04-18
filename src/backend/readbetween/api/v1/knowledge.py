from fastapi import APIRouter
from readbetween.services.knowledge import KnowledgeService
from readbetween.models.schemas.response import resp_200, resp_500
from readbetween.services.knowledge_file import KnowledgeFileService
from readbetween.utils.logger_util import logger_util
from readbetween.models.v1.knowledge import KnowledgeCreate, KnowledgeUpdate

router = APIRouter(tags=["知识库管理"])


@router.post("/knowledge/create")
async def create_knowledge(knowledge_create: KnowledgeCreate):
    try:
        return resp_200(await KnowledgeService.create_knowledge(knowledge_create))
    except Exception as e:
        logger_util.error(f"create_knowledge error: {e}")
        return resp_500(message=str(e))


@router.post("/knowledge/delete")
async def delete_knowledge(id: str):
    try:
        # 删除对应文件记录
        await KnowledgeFileService.delete_by_kb_id(id)
        logger_util.info(f"delete_knowledge_files done {id=}")
        return resp_200(await KnowledgeService.delete_knowledge(id))
    except Exception as e:
        logger_util.error(f"delete_knowledge error: {e}")
        return resp_500(message=str(e))


@router.post("/knowledge/update")
async def update_knowledge(knowledge_update: KnowledgeUpdate):
    try:
        return resp_200(await KnowledgeService.update_knowledge(knowledge_update))
    except Exception as e:
        logger_util.error(f"update_knowledge error: {e}")
        return resp_500(message=str(e))


@router.get("/knowledge/one")
async def get_knowledge_by_id(kb_id: str):
    try:
        return resp_200(await KnowledgeService.get_knowledge_by_id(kb_id))
    except Exception as e:
        logger_util.error(f"list_knowledge error: {e}")
        return resp_500(message=str(e))


@router.get("/knowledge/list")
async def list_knowledge_by_page(page: int = 1, size: int = 10):
    try:
        return resp_200(await KnowledgeService.list_knowledge_by_page(page, size))
    except Exception as e:
        logger_util.error(f"list_knowledge error: {e}")
        return resp_500(message=str(e))
