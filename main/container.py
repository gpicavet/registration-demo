from dependency_injector import containers, providers

from main.user_repository import UserRepository
from main.mail_service import MailService

class ApplicationContainer(containers.DeclarativeContainer):

    user_repository=providers.Factory(UserRepository)
    mail_service=providers.Factory(MailService)

