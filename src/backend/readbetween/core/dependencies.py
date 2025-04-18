from readbetween.utils.local_embedding_manager import LocalEmbedManager
from readbetween.settings import get_config


def get_local_embed_manager():
    embedding_model = get_config("system.models.embedding.name")
    model_dir = get_config("system.models.base_dir")

    lem = LocalEmbedManager()
    lem.initialize(
        model_name=embedding_model,
        model_dir=model_dir
    )

    return lem
