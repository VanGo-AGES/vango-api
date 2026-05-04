"""US09 — TripService.

Orquestra o fluxo de execução de viagem:
- start_trip: cria TripModel + TripPassangerModel para cada passageiro
  aceito, pré-aplicando absences avisadas para o dia
- get_current_trip: retorna a viagem em andamento do motorista em uma rota
- get_next_stop: próxima parada pendente + info do passageiro
- board_passanger / mark_passanger_absent / skip_stop / alight_passanger:
  mutations do status por passageiro durante a viagem
- finish_trip: finaliza a viagem (status + finished_at + auto-alight)

Depende de: ITripRepository, ITripPassangerRepository, IAbsenceRepository,
IRouteRepository, IVehicleRepository (ou cheque equivalente), IStopRepository
e INotificationService.
"""

from datetime import UTC, datetime
from uuid import UUID

from src.domains.notifications.service import INotificationService
from src.domains.route_passangers.repository import IRoutePassangerRepository
from src.domains.routes.repository import IRouteRepository
from src.domains.stops.repository import IStopRepository
from src.domains.trips.dtos import (
    FinishTripRequest,
    StartTripRequest,
    TripNextStopResponse,
    TripPassangerResponse,
    TripResponse,
)
from src.domains.trips.entity import TripModel, TripPassangerModel
from src.domains.trips.errors import (
    NoPassangersToStartError,
    TripAlreadyInProgressError,
    TripNotFoundError,
    TripOwnershipError,
    VehicleNotOwnedError,
)
from src.domains.trips.repository import (
    IAbsenceRepository,
    ITripPassangerRepository,
    ITripRepository,
)
from src.domains.vehicles.repository import IVehicleRepository


class TripService:
    def __init__(
        self,
        trip_repository: ITripRepository,
        trip_passanger_repository: ITripPassangerRepository,
        absence_repository: IAbsenceRepository,
        route_repository: IRouteRepository,
        route_passanger_repository: IRoutePassangerRepository,
        stop_repository: IStopRepository,
        vehicle_repository: IVehicleRepository,
        notification_service: INotificationService,
    ) -> None:
        self.trip_repository = trip_repository
        self.trip_passanger_repository = trip_passanger_repository
        self.absence_repository = absence_repository
        self.route_repository = route_repository
        self.route_passanger_repository = route_passanger_repository
        self.stop_repository = stop_repository
        self.vehicle_repository = vehicle_repository
        self.notification_service = notification_service

    # US09-TK06
    def start_trip(self, route_id: UUID, driver_id: UUID, data: StartTripRequest) -> TripResponse:
        """Inicia a execução de uma rota."""

        route = self.route_repository.find_by_id(route_id)
        if route is None:
            raise TripNotFoundError(f"Rota {route_id} não encontrada.")

        if route.driver_id != driver_id:
            raise TripOwnershipError("Motorista não é dono desta rota.")

        vehicle = self.vehicle_repository.find_by_id(data.vehicle_id)
        if vehicle.driver_id != driver_id:
            raise VehicleNotOwnedError("Veículo não pertence ao motorista.")

        existing = self.trip_repository.find_in_progress_by_route(route_id)
        if existing is not None:
            raise TripAlreadyInProgressError("Já existe uma viagem iniciada para esta rota.")

        accepted = self.route_passanger_repository.find_by_route_and_status(route_id, "accepted")
        if not accepted:
            raise NoPassangersToStartError("Nenhum passageiro aceito na rota.")

        now = datetime.now(UTC)
        trip_date = data.trip_date or now

        trip = TripModel(
            route_id=route_id,
            vehicle_id=data.vehicle_id,
            trip_date=trip_date,
            status="iniciada",
            started_at=now,
        )
        saved_trip = self.trip_repository.save(trip)

        absences = self.absence_repository.find_by_route_and_date(route_id, trip_date)
        absent_ids = {a.route_passanger_id for a in absences}

        trip_passangers = [
            TripPassangerModel(
                trip_id=saved_trip.id,
                route_passanger_id=rp.id,
                status="ausente" if rp.id in absent_ids else "pendente",
            )
            for rp in accepted
        ]
        self.trip_passanger_repository.save_all(trip_passangers)

        self.route_repository.update(route_id, {"status": "em_andamento"})

        self.notification_service.notify_trip_started(saved_trip)

        return TripResponse(
            id=saved_trip.id,
            route_id=route_id,
            route_name=route.name,
            vehicle_id=data.vehicle_id,
            trip_date=trip_date,
            status="iniciada",
            started_at=now,
            finished_at=None,
            total_km=None,
            trip_passangers=[],
        )

    # US09-TK07
    def get_current_trip(self, trip_id: UUID, driver_id: UUID) -> TripResponse:
        """Retorna a trip (em qualquer status) pelo id, validando ownership.

        - Busca trip_repository.find_by_id.
        - Se não existir → TripNotFoundError.
        - Se route.driver_id != driver_id → TripOwnershipError.
        - Monta TripResponse com trip_passangers (resolvendo nomes, endereços,
          telefone via RoutePassanger.user/dependent/pickup_address).
        """
        pass

    # US09-TK08
    def get_next_stop(self, trip_id: UUID, driver_id: UUID) -> TripNextStopResponse | None:
        """Retorna a próxima parada pendente (trip_passanger.status='pendente')
        da trip.

        - Valida ownership igual ao get_current_trip.
        - Busca todos os trip_passangers da trip ordenados por Stop.order_index.
        - Retorna o primeiro com status='pendente'. Se não houver, retorna None.
        - O DTO inclui passanger_phone (telefone pro deeplink US13).
        """
        pass

    # US09-TK09
    def board_passanger(self, trip_id: UUID, trip_passanger_id: UUID, driver_id: UUID) -> TripPassangerResponse:
        """Confirma embarque de um passageiro na trip.

        - Valida ownership da trip.
        - Valida que trip.status == 'iniciada' (senão TripNotInProgressError).
        - Valida que trip_passanger existe e pertence à trip.
        - Valida transição: só pode marcar presente quem está 'pendente'
          (se já está 'ausente', InvalidTripPassangerStatusError).
        - Atualiza status='presente', boarded_at=now.
        - Retorna TripPassangerResponse do registro atualizado.
        """
        pass

    # US09-TK10
    def mark_passanger_absent(self, trip_id: UUID, trip_passanger_id: UUID, driver_id: UUID) -> TripPassangerResponse:
        """Marca passageiro como não embarcado (ausente).

        Mesmas validações do board_passanger, mas:
        - Só pode marcar ausente quem está 'pendente'.
        - Atualiza status='ausente' (boarded_at permanece None).
        """
        pass

    # US09-TK11
    def skip_stop(self, trip_id: UUID, stop_id: UUID, driver_id: UUID) -> list[TripPassangerResponse]:
        """Pula uma parada inteira — marca todos os trip_passangers daquela
        parada como 'ausente'.

        - Valida ownership e status da trip.
        - Valida que o stop pertence à rota da trip (TripStopNotFoundError).
        - Identifica os trip_passangers associados à stop (via
          stop.route_passanger_id) que ainda estão 'pendente'.
        - Atualiza todos para 'ausente'.
        - Retorna a lista atualizada.
        """
        pass

    # US09-TK12
    def alight_passanger(self, trip_id: UUID, trip_passanger_id: UUID, driver_id: UUID) -> TripPassangerResponse:
        """Registra desembarque manual de um passageiro.

        - Valida ownership e status da trip (ainda 'iniciada').
        - Valida que trip_passanger.status == 'presente' (só desembarca quem
          embarcou).
        - Atualiza alighted_at=now.
        """
        pass

    # US09-TK13
    def finish_trip(self, trip_id: UUID, driver_id: UUID, data: FinishTripRequest) -> TripResponse:
        """Finaliza a viagem.

        - Valida ownership.
        - Valida que trip.status == 'iniciada' (senão TripAlreadyFinishedError).
        - Para todos os trip_passangers com status='presente' e alighted_at IS
          NULL, preenche alighted_at=now (bulk update no repo).
        - Atualiza trip: status='finalizada', finished_at=now, total_km do payload.
        - Atualiza a rota: status='ativa' (volta a ficar disponível).
        - Dispara notify_trip_finished.
        - Retorna TripResponse final.
        """
        pass
