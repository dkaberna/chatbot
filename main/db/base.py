# Import all the models, so that Base has them before being imported by Alembic
from main.db.base_class import Base  # noqa
from main.models.chat import Chat, Message