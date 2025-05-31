import logging
from logging import Logger
from src.app.core.config import settings

# Define o nível de log a partir das configurações (padrão INFO)
LOG_LEVEL = getattr(logging, getattr(settings, 'log_level', 'INFO').upper(), logging.INFO)

# Formato de log padrão: timestamp, nível, logger e mensagem
LOG_FORMAT = '%(asctime)s %(levelname)s [%(name)s] %(message)s'

# Configura a configuração básica de logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
)

# Logger raiz para a aplicação
logger: Logger = logging.getLogger('vector_service')

# Ajusta nível específico para uvicorn, se desejado
logging.getLogger('uvicorn').handlers = logging.root.handlers
logging.getLogger('uvicorn.access').handlers = logging.root.handlers
logging.getLogger('uvicorn.error').handlers = logging.root.handlers

# Exemplo de uso:
# from src.app.core.logger import logger
# logger.info('Aplicação iniciada com sucesso')