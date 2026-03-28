from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.config import settings

# 1. Importações Absolutas do seu projeto
from src.infrastructure.database import Base
from src.domains.users.entity import UserModel
from src.domains.addresses.enitty import AddressModel
from src.domains.dependents.entity import DependentModel
from src.domains.routes.entity import RouteModel
from src.domains.route_passangers.entity import RoutePassangerModel
from src.domains.vehicles.entity import VehicleModel

_ = UserModel, AddressModel, DependentModel, RouteModel, RoutePassangerModel, VehicleModel

# Objeto de configuração do Alembic (lê o alembic.ini)
config = context.config

# 2. Configura a URL do banco dinamicamente vinda do seu settings/.env
# Isso ignora o que estiver escrito no alembic.ini
config.set_main_option("sqlalchemy.url", settings.database_url)

# Configura o logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. Define os metadados para que o Alembic saiba quais tabelas criar
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Modo Offline: Gera o SQL sem se conectar ao banco."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Modo Online: Conecta ao banco e aplica as mudanças."""
    # Cria o engine usando a configuração que injetamos acima
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
