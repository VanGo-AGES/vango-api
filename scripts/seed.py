"""seed.py — Popula o banco de dados com dados de teste realistas.

Cenários incluídos
------------------
1. Rota Escolar Manhã (Zona Norte → Moinhos de Vento)
   - Motorista: Carlos Eduardo Oliveira
   - 3 passageiros aceitos (2 guardiões + dependentes, 1 passageiro direto)
   - 3 stops na rota (1 embarque por passageiro aceito)
   - 1 viagem finalizada + 1 viagem em andamento

2. Rota Empresarial Tarde (Cidade Baixa → Bela Vista)
   - Motorista: Roberto Alves Ferreira
   - 2 passageiros aceitos + 1 pendente
   - 2 stops na rota
   - 1 viagem iniciada

Uso
---
    # A partir da raiz do projeto (dentro do container ou venv ativo):
    python -m scripts.seed

    # Para limpar e re-popular:
    python -m scripts.seed --reset

Idempotência
------------
Sem --reset, o script detecta se o e-mail do primeiro motorista já existe e
encerra sem fazer nada, evitando duplicatas.
"""

import argparse

# Garante que src/ é encontrado mesmo rodando como script avulso
import os
import sys
import uuid
from datetime import UTC, datetime, time, timedelta

from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.domains.addresses.entity import AddressModel  # noqa: E402
from src.domains.dependents.entity import DependentModel  # noqa: E402
from src.domains.route_passangers.entity import RoutePassangerModel  # noqa: E402
from src.domains.route_passangers.schedule_entity import RoutePassangerScheduleModel  # noqa: E402
from src.domains.routes.entity import RouteModel  # noqa: E402
from src.domains.stops.entity import StopModel  # noqa: E402
from src.domains.trips.entity import AbsenceModel, TripModel, TripPassangerModel  # noqa: E402
from src.domains.users.entity import UserModel  # noqa: E402
from src.domains.vehicles.entity import VehicleModel  # noqa: E402
from src.infrastructure.database import Base, SessionLocal, engine  # noqa: E402
from src.infrastructure.security import hash_password  # noqa: E402

# ---------------------------------------------------------------------------
# Senha padrão para todos os usuários de teste
# ---------------------------------------------------------------------------
DEFAULT_PASSWORD = "senha123"

# ---------------------------------------------------------------------------
# Identificador de idempotência — e-mail único do primeiro motorista
# ---------------------------------------------------------------------------
SEED_ANCHOR_EMAIL = "carlos.oliveira@example.com"


# ===========================================================================
# Helpers
# ===========================================================================


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _days_ago(n: int) -> datetime:
    return _now() - timedelta(days=n)


def _make_user(
    name: str,
    email: str,
    phone: str,
    role: str,
    cpf: str | None = None,
) -> UserModel:
    return UserModel(
        id=uuid.uuid4(),
        name=name,
        email=email,
        phone=phone,
        password_hash=hash_password(DEFAULT_PASSWORD),
        role=role,
        cpf=cpf,
    )


def _make_address(
    user_id: uuid.UUID,
    label: str,
    street: str,
    number: str,
    neighborhood: str,
    zip_code: str,
    latitude: float | None = None,
    longitude: float | None = None,
    is_default: bool = False,
) -> AddressModel:
    return AddressModel(
        id=uuid.uuid4(),
        user_id=user_id,
        label=label,
        street=street,
        number=number,
        neighborhood=neighborhood,
        zip=zip_code,
        city="Porto Alegre",
        state="RS",
        latitude=latitude,
        longitude=longitude,
        is_default=is_default,
    )


def _make_route(
    driver_id: uuid.UUID,
    origin_address_id: uuid.UUID,
    destination_address_id: uuid.UUID,
    name: str,
    route_type: str,
    recurrence: str,
    expected_time: time,
    max_passengers: int,
    status: str = "ativa",
) -> RouteModel:
    invite_code = uuid.uuid4().hex[:5].upper()
    return RouteModel(
        id=uuid.uuid4(),
        driver_id=driver_id,
        origin_address_id=origin_address_id,
        destination_address_id=destination_address_id,
        name=name,
        route_type=route_type,
        recurrence=recurrence,
        expected_time=expected_time,
        max_passengers=max_passengers,
        status=status,
        invite_code=invite_code,
    )


def _make_route_passanger(
    route_id: uuid.UUID,
    user_id: uuid.UUID,
    pickup_address_id: uuid.UUID,
    status: str = "accepted",
    dependent_id: uuid.UUID | None = None,
) -> RoutePassangerModel:
    kwargs: dict = dict(
        id=uuid.uuid4(),
        route_id=route_id,
        user_id=user_id,
        dependent_id=dependent_id,
        pickup_address_id=pickup_address_id,
        status=status,
        requested_at=_days_ago(7),
    )
    # joined_at has a server_default — only set explicitly for accepted passengers
    if status == "accepted":
        kwargs["joined_at"] = _days_ago(6)
    return RoutePassangerModel(**kwargs)


def _make_schedule(
    route_passanger_id: uuid.UUID,
    address_id: uuid.UUID,
    day_of_week: str,
) -> RoutePassangerScheduleModel:
    return RoutePassangerScheduleModel(
        id=uuid.uuid4(),
        route_passanger_id=route_passanger_id,
        address_id=address_id,
        day_of_week=day_of_week,
    )


def _make_stop(
    route_id: uuid.UUID,
    route_passanger_id: uuid.UUID,
    address_id: uuid.UUID,
    order_index: int,
    stop_type: str = "embarque",
) -> StopModel:
    return StopModel(
        id=uuid.uuid4(),
        route_id=route_id,
        route_passanger_id=route_passanger_id,
        address_id=address_id,
        order_index=order_index,
        type=stop_type,
    )


def _make_trip(
    route_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    trip_date: datetime,
    status: str,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    total_km: float | None = None,
) -> TripModel:
    return TripModel(
        id=uuid.uuid4(),
        route_id=route_id,
        vehicle_id=vehicle_id,
        trip_date=trip_date,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        total_km=total_km,
    )


def _make_trip_passanger(
    trip_id: uuid.UUID,
    route_passanger_id: uuid.UUID,
    status: str = "pendente",
    boarded_at: datetime | None = None,
    alighted_at: datetime | None = None,
) -> TripPassangerModel:
    return TripPassangerModel(
        id=uuid.uuid4(),
        trip_id=trip_id,
        route_passanger_id=route_passanger_id,
        status=status,
        boarded_at=boarded_at,
        alighted_at=alighted_at,
    )


def _make_absence(
    route_passanger_id: uuid.UUID,
    absence_date: datetime,
    reason: str | None = None,
    trip_id: uuid.UUID | None = None,
) -> AbsenceModel:
    return AbsenceModel(
        id=uuid.uuid4(),
        route_passanger_id=route_passanger_id,
        trip_id=trip_id,
        absence_date=absence_date,
        reason=reason,
    )


# ===========================================================================
# Reset
# ===========================================================================


def reset_db(db: Session) -> None:
    """Remove todos os registros em ordem reversa das FKs."""
    print("  Limpando banco de dados...")
    for model in [
        AbsenceModel,
        TripPassangerModel,
        TripModel,
        StopModel,
        RoutePassangerScheduleModel,
        RoutePassangerModel,
        RouteModel,
        DependentModel,
        VehicleModel,
        AddressModel,
        UserModel,
    ]:
        db.query(model).delete()
    db.commit()
    print("  Banco limpo.")


# ===========================================================================
# Seed principal
# ===========================================================================


def seed(db: Session) -> None:  # noqa: PLR0914 (muitas variáveis locais, ok para seed)
    print("Iniciando seed...")

    # -----------------------------------------------------------------------
    # CENÁRIO 1 — Rota Escolar Manhã
    # Motorista: Carlos Eduardo Oliveira
    # Rota: Zona Norte → Colégio Moinhos de Vento (outbound, seg–sex, 07:00)
    # -----------------------------------------------------------------------
    print("  [Cenário 1] Criando motorista e veículo...")

    driver1 = _make_user(
        name="Carlos Eduardo Oliveira",
        email=SEED_ANCHOR_EMAIL,
        phone="51999110001",
        role="driver",
        cpf="123.456.789-01",
    )
    db.add(driver1)
    db.flush()

    vehicle1 = VehicleModel(
        id=uuid.uuid4(),
        driver_id=driver1.id,
        plate="IJK-1A23",
        notes="Sprinter branca — ar-condicionado e DVD",
        capacity=8,
        status=True,
    )
    db.add(vehicle1)
    db.flush()

    # Endereços da rota 1
    addr_origin1 = _make_address(
        user_id=driver1.id,
        label="Garagem",
        street="Avenida Assis Brasil",
        number="3970",
        neighborhood="Passo d'Areia",
        zip_code="91010-000",
        latitude=-30.0151,
        longitude=-51.1694,
        is_default=True,
    )
    addr_dest1 = _make_address(
        user_id=driver1.id,
        label="Colégio Moinhos",
        street="Rua Mostardeiro",
        number="50",
        neighborhood="Moinhos de Vento",
        zip_code="90430-000",
        latitude=-30.0248,
        longitude=-51.2010,
    )
    db.add_all([addr_origin1, addr_dest1])
    db.flush()

    route1 = _make_route(
        driver_id=driver1.id,
        origin_address_id=addr_origin1.id,
        destination_address_id=addr_dest1.id,
        name="Rota Escolar Zona Norte — Manhã",
        route_type="outbound",
        recurrence="seg,ter,qua,qui,sex",
        expected_time=time(7, 0),
        max_passengers=vehicle1.capacity,
        status="ativa",
    )
    db.add(route1)
    db.flush()

    # ---
    # Passageiro 1: Ana Paula Rodrigues (guardian) + dependente Mateus
    # ---
    print("  [Cenário 1] Criando passageiros e paradas...")

    guardian1 = _make_user(
        name="Ana Paula Rodrigues",
        email="ana.rodrigues@example.com",
        phone="51988220002",
        role="guardian",
    )
    db.add(guardian1)
    db.flush()

    dep1 = DependentModel(
        id=uuid.uuid4(),
        name="Mateus Rodrigues",
        guardian_id=guardian1.id,
    )
    db.add(dep1)
    db.flush()

    addr_pickup1 = _make_address(
        user_id=guardian1.id,
        label="Casa",
        street="Rua Ângelo Giusti",
        number="120",
        neighborhood="Passo d'Areia",
        zip_code="91030-430",
        latitude=-30.0128,
        longitude=-51.1720,
        is_default=True,
    )
    db.add(addr_pickup1)
    db.flush()

    rp1 = _make_route_passanger(
        route_id=route1.id,
        user_id=guardian1.id,
        pickup_address_id=addr_pickup1.id,
        status="accepted",
        dependent_id=dep1.id,
    )
    db.add(rp1)
    db.flush()

    # Schedules: seg a sex (usando o mesmo endereço para todos os dias)
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
        db.add(_make_schedule(rp1.id, addr_pickup1.id, day))

    # Stop 1 (embarque do Mateus/Ana Paula)
    stop1 = _make_stop(
        route_id=route1.id,
        route_passanger_id=rp1.id,
        address_id=addr_pickup1.id,
        order_index=1,
        stop_type="embarque",
    )
    db.add(stop1)
    db.flush()

    # ---
    # Passageiro 2: Fernanda Lima (guardian) + dependente Isabela
    # ---
    guardian2 = _make_user(
        name="Fernanda Lima",
        email="fernanda.lima@example.com",
        phone="51977330003",
        role="guardian",
    )
    db.add(guardian2)
    db.flush()

    dep2 = DependentModel(
        id=uuid.uuid4(),
        name="Isabela Lima",
        guardian_id=guardian2.id,
    )
    db.add(dep2)
    db.flush()

    addr_pickup2 = _make_address(
        user_id=guardian2.id,
        label="Casa",
        street="Avenida Assis Brasil",
        number="1256",
        neighborhood="Floresta",
        zip_code="90220-011",
        latitude=-30.0193,
        longitude=-51.1835,
        is_default=True,
    )
    db.add(addr_pickup2)
    db.flush()

    rp2 = _make_route_passanger(
        route_id=route1.id,
        user_id=guardian2.id,
        pickup_address_id=addr_pickup2.id,
        status="accepted",
        dependent_id=dep2.id,
    )
    db.add(rp2)
    db.flush()

    for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
        db.add(_make_schedule(rp2.id, addr_pickup2.id, day))

    stop2 = _make_stop(
        route_id=route1.id,
        route_passanger_id=rp2.id,
        address_id=addr_pickup2.id,
        order_index=2,
        stop_type="embarque",
    )
    db.add(stop2)
    db.flush()

    # ---
    # Passageiro 3: João Vitor Santos (passenger direto — sem dependente)
    # ---
    passenger1 = _make_user(
        name="João Vitor Santos",
        email="joao.santos@example.com",
        phone="51966440004",
        role="passenger",
    )
    db.add(passenger1)
    db.flush()

    addr_pickup3 = _make_address(
        user_id=passenger1.id,
        label="Casa",
        street="Rua Felipe Camarão",
        number="800",
        neighborhood="Higienópolis",
        zip_code="90550-031",
        latitude=-30.0340,
        longitude=-51.1910,
        is_default=True,
    )
    db.add(addr_pickup3)
    db.flush()

    rp3 = _make_route_passanger(
        route_id=route1.id,
        user_id=passenger1.id,
        pickup_address_id=addr_pickup3.id,
        status="accepted",
    )
    db.add(rp3)
    db.flush()

    for day in ["monday", "wednesday", "friday"]:
        db.add(_make_schedule(rp3.id, addr_pickup3.id, day))

    stop3 = _make_stop(
        route_id=route1.id,
        route_passanger_id=rp3.id,
        address_id=addr_pickup3.id,
        order_index=3,
        stop_type="embarque",
    )
    db.add(stop3)
    db.flush()

    # ---
    # Viagem 1A: finalizada (ontem)
    # ---
    print("  [Cenário 1] Criando viagens...")

    trip1_date = _days_ago(1).replace(hour=7, minute=0, second=0, microsecond=0)
    trip1_start = trip1_date.replace(hour=7, minute=2)
    trip1_finish = trip1_date.replace(hour=7, minute=48)

    trip1 = _make_trip(
        route_id=route1.id,
        vehicle_id=vehicle1.id,
        trip_date=trip1_date,
        status="finalizada",
        started_at=trip1_start,
        finished_at=trip1_finish,
        total_km=12.4,
    )
    db.add(trip1)
    db.flush()

    # Todos presentes na trip1
    for rp, boarded_delta, alighted_delta in [
        (rp1, 8, 46),
        (rp2, 15, 46),
        (rp3, 25, 46),
    ]:
        db.add(
            _make_trip_passanger(
                trip_id=trip1.id,
                route_passanger_id=rp.id,
                status="presente",
                boarded_at=trip1_start + timedelta(minutes=boarded_delta),
                alighted_at=trip1_start + timedelta(minutes=alighted_delta),
            )
        )

    # ---
    # Viagem 1B: em andamento (hoje, já iniciada)
    # ---
    trip2_date = _now().replace(hour=7, minute=0, second=0, microsecond=0)
    trip2_start = trip2_date.replace(hour=7, minute=1)

    trip2 = _make_trip(
        route_id=route1.id,
        vehicle_id=vehicle1.id,
        trip_date=trip2_date,
        status="iniciada",
        started_at=trip2_start,
    )
    db.add(trip2)
    db.flush()

    # rp1 e rp3 embarcaram; rp2 ainda pendente (atrasou)
    db.add(
        _make_trip_passanger(
            trip_id=trip2.id,
            route_passanger_id=rp1.id,
            status="presente",
            boarded_at=trip2_start + timedelta(minutes=6),
        )
    )
    db.add(
        _make_trip_passanger(
            trip_id=trip2.id,
            route_passanger_id=rp2.id,
            status="pendente",
        )
    )
    db.add(
        _make_trip_passanger(
            trip_id=trip2.id,
            route_passanger_id=rp3.id,
            status="presente",
            boarded_at=trip2_start + timedelta(minutes=22),
        )
    )
    db.flush()

    # Ausência registrada para rp2 (avisou com antecedência)
    db.add(
        _make_absence(
            route_passanger_id=rp2.id,
            absence_date=trip2_date,
            reason="Isabela está doente hoje.",
            trip_id=trip2.id,
        )
    )

    # -----------------------------------------------------------------------
    # CENÁRIO 2 — Rota Empresarial Tarde
    # Motorista: Roberto Alves Ferreira
    # Rota: Cidade Baixa → Bela Vista (inbound, seg/qua/sex, 17:45)
    # -----------------------------------------------------------------------
    print("  [Cenário 2] Criando motorista e veículo...")

    driver2 = _make_user(
        name="Roberto Alves Ferreira",
        email="roberto.ferreira@example.com",
        phone="51999550005",
        role="driver",
        cpf="987.654.321-00",
    )
    db.add(driver2)
    db.flush()

    vehicle2 = VehicleModel(
        id=uuid.uuid4(),
        driver_id=driver2.id,
        plate="RST-5B67",
        notes="Master prata — 12 lugares",
        capacity=12,
        status=True,
    )
    db.add(vehicle2)
    db.flush()

    addr_origin2 = _make_address(
        user_id=driver2.id,
        label="Ponto de partida",
        street="Rua da República",
        number="230",
        neighborhood="Cidade Baixa",
        zip_code="90050-320",
        latitude=-30.0424,
        longitude=-51.2198,
        is_default=True,
    )
    addr_dest2 = _make_address(
        user_id=driver2.id,
        label="Destino",
        street="Avenida Nilo Peçanha",
        number="2900",
        neighborhood="Bela Vista",
        zip_code="91330-001",
        latitude=-30.0101,
        longitude=-51.1602,
    )
    db.add_all([addr_origin2, addr_dest2])
    db.flush()

    route2 = _make_route(
        driver_id=driver2.id,
        origin_address_id=addr_origin2.id,
        destination_address_id=addr_dest2.id,
        name="Rota Empresarial Centro — Tarde",
        route_type="inbound",
        recurrence="seg,qua,sex",
        expected_time=time(17, 45),
        max_passengers=vehicle2.capacity,
        status="ativa",
    )
    db.add(route2)
    db.flush()

    # ---
    # Passageiro 4: Mariana Costa (passenger) — aceita
    # ---
    print("  [Cenário 2] Criando passageiros e paradas...")

    passenger2 = _make_user(
        name="Mariana Costa",
        email="mariana.costa@example.com",
        phone="51988660006",
        role="passenger",
    )
    db.add(passenger2)
    db.flush()

    addr_pickup4 = _make_address(
        user_id=passenger2.id,
        label="Trabalho",
        street="Avenida Borges de Medeiros",
        number="1501",
        neighborhood="Centro Histórico",
        zip_code="90020-021",
        latitude=-30.0340,
        longitude=-51.2175,
        is_default=True,
    )
    db.add(addr_pickup4)
    db.flush()

    rp4 = _make_route_passanger(
        route_id=route2.id,
        user_id=passenger2.id,
        pickup_address_id=addr_pickup4.id,
        status="accepted",
    )
    db.add(rp4)
    db.flush()

    for day in ["monday", "wednesday", "friday"]:
        db.add(_make_schedule(rp4.id, addr_pickup4.id, day))

    stop4 = _make_stop(
        route_id=route2.id,
        route_passanger_id=rp4.id,
        address_id=addr_pickup4.id,
        order_index=1,
        stop_type="embarque",
    )
    db.add(stop4)
    db.flush()

    # ---
    # Passageiro 5: Thiago Becker (passenger) — aceito
    # ---
    passenger3 = _make_user(
        name="Thiago Becker",
        email="thiago.becker@example.com",
        phone="51977770007",
        role="passenger",
    )
    db.add(passenger3)
    db.flush()

    addr_pickup5 = _make_address(
        user_id=passenger3.id,
        label="Escritório",
        street="Rua dos Andradas",
        number="1234",
        neighborhood="Centro Histórico",
        zip_code="90020-007",
        latitude=-30.0300,
        longitude=-51.2280,
        is_default=True,
    )
    db.add(addr_pickup5)
    db.flush()

    rp5 = _make_route_passanger(
        route_id=route2.id,
        user_id=passenger3.id,
        pickup_address_id=addr_pickup5.id,
        status="accepted",
    )
    db.add(rp5)
    db.flush()

    for day in ["monday", "wednesday", "friday"]:
        db.add(_make_schedule(rp5.id, addr_pickup5.id, day))

    stop5 = _make_stop(
        route_id=route2.id,
        route_passanger_id=rp5.id,
        address_id=addr_pickup5.id,
        order_index=2,
        stop_type="embarque",
    )
    db.add(stop5)
    db.flush()

    # ---
    # Passageiro 6: Juliana Fonseca (passenger) — ainda pendente (sem stop)
    # ---
    passenger4 = _make_user(
        name="Juliana Fonseca",
        email="juliana.fonseca@example.com",
        phone="51966880008",
        role="passenger",
    )
    db.add(passenger4)
    db.flush()

    addr_pickup6 = _make_address(
        user_id=passenger4.id,
        label="Casa",
        street="Rua General Lima e Silva",
        number="712",
        neighborhood="Cidade Baixa",
        zip_code="90050-100",
        latitude=-30.0443,
        longitude=-51.2202,
        is_default=True,
    )
    db.add(addr_pickup6)
    db.flush()

    # Status "pending" — ainda não aceita, portanto SEM stop e SEM schedule
    rp6 = _make_route_passanger(
        route_id=route2.id,
        user_id=passenger4.id,
        pickup_address_id=addr_pickup6.id,
        status="pending",
    )
    db.add(rp6)
    db.flush()

    # ---
    # Viagem 2A: em andamento (hoje, partida às 17h45)
    # ---
    print("  [Cenário 2] Criando viagem...")

    trip3_date = _now().replace(hour=17, minute=45, second=0, microsecond=0)
    trip3_start = trip3_date.replace(hour=17, minute=47)

    trip3 = _make_trip(
        route_id=route2.id,
        vehicle_id=vehicle2.id,
        trip_date=trip3_date,
        status="iniciada",
        started_at=trip3_start,
    )
    db.add(trip3)
    db.flush()

    db.add(
        _make_trip_passanger(
            trip_id=trip3.id,
            route_passanger_id=rp4.id,
            status="presente",
            boarded_at=trip3_start + timedelta(minutes=4),
        )
    )
    db.add(
        _make_trip_passanger(
            trip_id=trip3.id,
            route_passanger_id=rp5.id,
            status="pendente",
        )
    )
    # rp6 não entra na trip pois ainda está pendente na rota

    # -----------------------------------------------------------------------
    # Commit final
    # -----------------------------------------------------------------------
    db.commit()
    print("Seed concluído com sucesso!")
    _print_summary()


def _print_summary() -> None:
    print()
    print("=" * 60)
    print("RESUMO DO SEED")
    print("=" * 60)
    print()
    print("Credenciais (todos os usuários):")
    print(f"  Senha: {DEFAULT_PASSWORD}")
    print()
    print("Usuários criados:")
    print("  carlos.oliveira@example.com   — motorista (Rota Escolar)")
    print("  roberto.ferreira@example.com  — motorista (Rota Empresarial)")
    print("  ana.rodrigues@example.com     — guardian  (+ dep. Mateus)")
    print("  fernanda.lima@example.com     — guardian  (+ dep. Isabela)")
    print("  joao.santos@example.com       — passenger (aceito)")
    print("  mariana.costa@example.com     — passenger (aceita)")
    print("  thiago.becker@example.com     — passenger (aceito)")
    print("  juliana.fonseca@example.com   — passenger (pendente)")
    print()
    print("Rotas:")
    print("  Rota Escolar Zona Norte — Manhã  (outbound, seg–sex, 07:00)")
    print("    3 stops | 1 viagem finalizada + 1 em andamento")
    print("  Rota Empresarial Centro — Tarde  (inbound, seg/qua/sex, 17:45)")
    print("    2 stops | 1 viagem em andamento | 1 passageiro pendente")
    print("=" * 60)


# ===========================================================================
# Entry-point
# ===========================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed do banco de dados VanGo")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Apaga todos os dados antes de popular (idempotente sem esta flag).",
    )
    args = parser.parse_args()

    # Garante que as tabelas existam (útil se rodar antes do alembic)
    Base.metadata.create_all(engine)

    db: Session = SessionLocal()
    try:
        if args.reset:
            reset_db(db)
        else:
            existing = db.query(UserModel).filter_by(email=SEED_ANCHOR_EMAIL).first()
            if existing:
                print("Seed já executado anteriormente. " "Use --reset para limpar e re-popular.")
                return

        seed(db)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
