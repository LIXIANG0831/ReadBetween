from readbetween.models.dao.conversation_knowledge_link import ConversationKnowledgeLinkDao
from readbetween.services.base import BaseService


class ConversationKnowledgeLinkService(BaseService):
    @classmethod
    async def get_attached_knowledge(cls, conv_id: str):
        return await ConversationKnowledgeLinkDao.get_attached_knowledge(conv_id=conv_id)