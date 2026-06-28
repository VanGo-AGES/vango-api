"""seed_demo.py — Popula o banco para a live demo da rota PUCRS.

Comportamento
-------------
- Usuários (motorista + 3 passageiros): criados apenas se não existirem.
  Você pode editá-los manualmente no app sem perder os dados ao re-rodar.
- Rota PUCRS: excluída e recriada a cada execução (junto com stops e solicitações).

Uso
---
    python -m scripts.seed_demo

Dados criados
-------------
Motorista    : demo.motorista@vango.com
Passageiro 1 : demo.passageiro1@vango.com  — Fernanda (pending)
Passageiro 2 : demo.passageiro2@vango.com  — Lucas    (accepted + stop)
Passageiro 3 : demo.passageiro3@vango.com  — Juliana  (pending)

Rota PUCRS
  Tipo        : outbound
  Origem      : Av. Ipiranga, 6681 - Partenon (PUCRS)
  Destino     : Av. Juca Batista, 925 - Ipanema
  Horário     : 17:30
  Recorrência : seg, qua, dom

Senha padrão: senha123
"""

import os
import sys
import uuid
from datetime import UTC, datetime, time, timedelta

from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings  # noqa: E402
from src.domains.addresses.entity import AddressModel  # noqa: E402
from src.domains.dependents.entity import DependentModel  # noqa: E402, F401
from src.domains.route_passangers.entity import RoutePassangerModel  # noqa: E402
from src.domains.route_passangers.schedule_entity import RoutePassangerScheduleModel  # noqa: E402
from src.domains.routes.entity import RouteModel  # noqa: E402
from src.domains.stops.entity import StopModel  # noqa: E402
from src.domains.trips.entity import AbsenceModel, TripModel, TripPassangerModel  # noqa: E402, F401
from src.domains.users.entity import UserModel  # noqa: E402
from src.domains.vehicles.entity import VehicleModel  # noqa: E402
from src.infrastructure.database import Base, SessionLocal, engine  # noqa: E402
from src.infrastructure.routing.mapbox_routing_service import MapboxGeocodingService  # noqa: E402
from src.infrastructure.security import hash_password  # noqa: E402

_geocoding = MapboxGeocodingService(api_key=settings.mapbox_api_key)


def _geocode(street: str, number: str, neighborhood: str, zip_code: str) -> tuple[float | None, float | None]:
    result = _geocoding.geocode_address(
        street=street,
        number=number,
        neighborhood=neighborhood,
        zip_code=zip_code,
        city="Porto Alegre",
        state="RS",
    )
    if result:
        print(f"      geocoded {number} {street} → {result.latitude}, {result.longitude}")
        return result.latitude, result.longitude
    print(f"      WARN: geocoding falhou para {number} {street}, usando None")
    return None, None


DEFAULT_PASSWORD = "senha123"

DRIVER_EMAIL = "demo.motorista@vango.com"
PASSENGER1_EMAIL = "demo.passageiro1@vango.com"
PASSENGER2_EMAIL = "demo.passageiro2@vango.com"
PASSENGER3_EMAIL = "demo.passageiro3@vango.com"

ROUTE_NAME = "PUCRS"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _days_ago(n: int) -> datetime:
    return _now() - timedelta(days=n)


def _get_or_create_user(
    db: Session,
    email: str,
    name: str,
    phone: str,
    role: str,
    cpf: str | None = None,
) -> tuple[UserModel, bool]:
    existing = db.query(UserModel).filter_by(email=email).first()
    if existing:
        return existing, False

    user = UserModel(
        id=uuid.uuid4(),
        name=name,
        email=email,
        phone=phone,
        password_hash=hash_password(DEFAULT_PASSWORD),
        role=role,
        cpf=cpf,
    )
    db.add(user)
    db.flush()
    return user, True


def _get_or_create_address(
    db: Session,
    user_id: uuid.UUID,
    label: str,
    street: str,
    number: str,
    neighborhood: str,
    zip_code: str,
    latitude: float | None = None,
    longitude: float | None = None,
    is_default: bool = False,
) -> tuple[AddressModel, bool]:
    existing = db.query(AddressModel).filter_by(user_id=user_id, label=label).first()
    if existing:
        # Sempre atualiza coordenadas para garantir que o geocoding está correto
        existing.latitude = latitude
        existing.longitude = longitude
        db.flush()
        return existing, False

    addr = AddressModel(
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
    db.add(addr)
    db.flush()
    return addr, True


def _get_or_create_vehicle(
    db: Session,
    driver_id: uuid.UUID,
    plate: str,
    notes: str,
    capacity: int,
) -> tuple[VehicleModel, bool]:
    existing = db.query(VehicleModel).filter_by(driver_id=driver_id).first()
    if existing:
        return existing, False

    vehicle = VehicleModel(
        id=uuid.uuid4(),
        driver_id=driver_id,
        plate=plate,
        notes=notes,
        capacity=capacity,
        status=True,
    )
    db.add(vehicle)
    db.flush()
    return vehicle, True


def _delete_pucrs_route(db: Session, driver_id: uuid.UUID | None = None) -> None:
    routes = db.query(RouteModel).filter_by(name=ROUTE_NAME).all()

    for route in routes:
        rps = db.query(RoutePassangerModel).filter_by(route_id=route.id).all()
        for rp in rps:
            db.query(AbsenceModel).filter_by(route_passanger_id=rp.id).delete()
            db.query(TripPassangerModel).filter_by(route_passanger_id=rp.id).delete()
            db.query(RoutePassangerScheduleModel).filter_by(route_passanger_id=rp.id).delete()
            db.query(StopModel).filter_by(route_passanger_id=rp.id).delete()
            db.delete(rp)

        db.query(StopModel).filter_by(route_id=route.id).delete()
        db.delete(route)

    if routes:
        db.flush()
        print(f"  Rota '{ROUTE_NAME}' anterior removida.")

    # Remove os endereços de origem/destino do motorista para recriá-los atualizados
    if driver_id:
        for label in ("Origem PUCRS", "Destino PUCRS"):
            db.query(AddressModel).filter_by(user_id=driver_id, label=label).delete()
        db.flush()


# ---------------------------------------------------------------------------
# Seed principal
# ---------------------------------------------------------------------------


def seed_demo(db: Session) -> None:  # noqa: PLR0914
    print("Iniciando seed da demo...")

    # -----------------------------------------------------------------------
    # 1. Motorista e veículo
    # -----------------------------------------------------------------------
    print("  Verificando/criando motorista...")
    driver, driver_created = _get_or_create_user(
        db,
        email=DRIVER_EMAIL,
        name="Ricardo Mendes da Silva",
        phone="51999000001",
        role="driver",
        cpf="111.222.333-44",
    )
    print(f"    Motorista {'criado' if driver_created else 'já existe'}: {DRIVER_EMAIL}")

    vehicle, vehicle_created = _get_or_create_vehicle(
        db,
        driver_id=driver.id,
        plate="VNG-0001",
        notes="Van de demonstração",
        capacity=10,
    )
    if vehicle_created:
        print("    Veículo criado.")

    # Exclui a rota e os endereços do motorista antes de recriá-los
    _delete_pucrs_route(db, driver_id=driver.id)

    lat_origin, lon_origin = _geocode("Av. Ipiranga", "6681", "Partenon", "90619-900")
    addr_origin, _ = _get_or_create_address(
        db,
        user_id=driver.id,
        label="Origem PUCRS",
        street="Av. Ipiranga",
        number="6681",
        neighborhood="Partenon",
        zip_code="90619-900",
        latitude=lat_origin,
        longitude=lon_origin,
        is_default=True,
    )

    lat_dest, lon_dest = _geocode("Av. Juca Batista", "925", "Ipanema", "91770-001")
    addr_dest, _ = _get_or_create_address(
        db,
        user_id=driver.id,
        label="Destino PUCRS",
        street="Av. Juca Batista",
        number="925",
        neighborhood="Ipanema",
        zip_code="91770-001",
        latitude=lat_dest,
        longitude=lon_dest,
    )

    # -----------------------------------------------------------------------
    # 2. Passageiros (idempotentes)
    # -----------------------------------------------------------------------
    print("  Verificando/criando passageiros...")

    p1, p1_created = _get_or_create_user(
        db,
        email=PASSENGER1_EMAIL,
        name="Fernanda Oliveira Braga",
        phone="51988000002",
        role="passenger",
    )
    print(f"    Passageiro 1 {'criado' if p1_created else 'já existe'}: {PASSENGER1_EMAIL}")

    p2, p2_created = _get_or_create_user(
        db,
        email=PASSENGER2_EMAIL,
        name="Lucas Teixeira Ramos",
        phone="51977000003",
        role="passenger",
    )
    print(f"    Passageiro 2 {'criado' if p2_created else 'já existe'}: {PASSENGER2_EMAIL}")

    p3, p3_created = _get_or_create_user(
        db,
        email=PASSENGER3_EMAIL,
        name="Juliana Souza Pereira",
        phone="51966000004",
        role="passenger",
    )
    print(f"    Passageiro 3 {'criado' if p3_created else 'já existe'}: {PASSENGER3_EMAIL}")

    lat_p1, lon_p1 = _geocode("Rua Edilson João Prola", "95", "Ipanema", "91760-022")
    addr_p1, _ = _get_or_create_address(
        db,
        user_id=p1.id,
        label="Casa",
        street="Rua Edilson João Prola",
        number="95",
        neighborhood="Ipanema",
        zip_code="91760-022",
        latitude=lat_p1,
        longitude=lon_p1,
        is_default=True,
    )

    lat_p2, lon_p2 = _geocode("Av. Nonoai", "1736", "Nonoai", "91720-000")
    addr_p2, _ = _get_or_create_address(
        db,
        user_id=p2.id,
        label="Casa",
        street="Av. Nonoai",
        number="1736",
        neighborhood="Nonoai",
        zip_code="91720-000",
        latitude=lat_p2,
        longitude=lon_p2,
        is_default=True,
    )

    lat_p3, lon_p3 = _geocode("Av. Diário de Notícias", "300", "Cristal", "90810-080")
    addr_p3, _ = _get_or_create_address(
        db,
        user_id=p3.id,
        label="Casa",
        street="Av. Diário de Notícias",
        number="300",
        neighborhood="Cristal",
        zip_code="90810-080",
        latitude=lat_p3,
        longitude=lon_p3,
        is_default=True,
    )

    # -----------------------------------------------------------------------
    # 3. Criar a rota PUCRS
    # -----------------------------------------------------------------------
    print(f"  Criando rota '{ROUTE_NAME}'...")
    invite_code = uuid.uuid4().hex[:5].upper()
    route = RouteModel(
        id=uuid.uuid4(),
        driver_id=driver.id,
        origin_address_id=addr_origin.id,
        destination_address_id=addr_dest.id,
        name=ROUTE_NAME,
        route_type="outbound",
        recurrence="seg,qua,dom",
        expected_time=time(17, 30),
        max_passengers=vehicle.capacity,
        status="ativa",
        invite_code=invite_code,
    )
    db.add(route)
    db.flush()

    # -----------------------------------------------------------------------
    # 4. Passageiros na rota
    # -----------------------------------------------------------------------
    print("  Criando solicitações e passageiros na rota...")

    # Fernanda — accepted + stop
    rp1 = RoutePassangerModel(
        id=uuid.uuid4(),
        route_id=route.id,
        user_id=p1.id,
        dependent_id=None,
        pickup_address_id=addr_p1.id,
        status="accepted",
        requested_at=_days_ago(5),
        joined_at=_days_ago(4),
    )

    # Lucas — pending
    rp2 = RoutePassangerModel(
        id=uuid.uuid4(),
        route_id=route.id,
        user_id=p2.id,
        dependent_id=None,
        pickup_address_id=addr_p2.id,
        status="pending",
        requested_at=_days_ago(1),
    )

    # Juliana — pending
    rp3 = RoutePassangerModel(
        id=uuid.uuid4(),
        route_id=route.id,
        user_id=p3.id,
        dependent_id=None,
        pickup_address_id=addr_p3.id,
        status="pending",
        requested_at=_days_ago(2),
    )

    db.add_all([rp1, rp2, rp3])
    db.flush()

    # Stop para Fernanda
    db.add(
        StopModel(
            id=uuid.uuid4(),
            route_id=route.id,
            route_passanger_id=rp1.id,
            address_id=addr_p1.id,
            order_index=1,
            type="embarque",
        )
    )
    db.flush()

    # -----------------------------------------------------------------------
    # 5. Commit
    # -----------------------------------------------------------------------
    db.commit()
    print("\nSeed da demo concluído com sucesso!")
    _print_summary(invite_code)


def _print_summary(invite_code: str) -> None:
    print()
    print("=" * 60)
    print("RESUMO DO SEED DEMO")
    print("=" * 60)
    print()
    print(f"Senha padrão: {DEFAULT_PASSWORD}")
    print()
    print("Usuários (criados apenas uma vez — editáveis no app):")
    print(f"  {DRIVER_EMAIL:<35} — motorista")
    print(f"  {PASSENGER1_EMAIL:<35} — Fernanda (accepted + stop)")
    print(f"  {PASSENGER2_EMAIL:<35} — Lucas    (pending)")
    print(f"  {PASSENGER3_EMAIL:<35} — Juliana  (pending)")
    print()
    print("Rota PUCRS (recriada a cada execução):")
    print("  Tipo        : outbound")
    print("  Origem      : Av. Ipiranga, 6681 — Partenon (PUCRS)")
    print("  Destino     : Av. Juca Batista, 925 — Ipanema")
    print("  Horário     : 17:30")
    print("  Recorrência : seg, qua, dom")
    print(f"  Código      : {invite_code}")
    print()
    print("Roteiro da demo:")
    print("  1. Login como motorista (demo.motorista@vango.com)")
    print("  2. Tela de gerenciamento → ver rota PUCRS")
    print("  3. Gerenciar passageiros → aceitar Fernanda, recusar Juliana")
    print("  4. Visualizar mapa da rota")
    print("  5. Iniciar rota → pular passageiro → finalizar → ver métricas")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------


def main() -> None:
    Base.metadata.create_all(engine)

    db: Session = SessionLocal()
    try:
        seed_demo(db)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
