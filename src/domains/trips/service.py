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
    InvalidTripPassangerStatusError,
    NoPassangersToStartError,
    TripAlreadyInProgressError,
    TripNotFoundError,
    TripNotInProgressError,
    TripOwnershipError,
    TripPassangerNotFoundError,
    TripStopNotFoundError,
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
        """Retorna a trip (em qualquer status) pelo id, validando ownership."""

        trip = self.trip_repository.find_by_id(trip_id)

        if trip is None:
            raise TripNotFoundError(f"Viagem {trip_id} não encontrada.")

        if trip.route.driver_id != driver_id:
            raise TripOwnershipError("Motorista não é dono desta viagem.")

        return TripResponse(
            id=trip.id,
            route_id=trip.route_id,
            route_name=trip.route.name,
            vehicle_id=trip.vehicle_id,
            trip_date=trip.trip_date,
            status=trip.status,
            total_km=trip.total_km,
            started_at=trip.started_at,
            finished_at=trip.finished_at,
            trip_passangers=[self._build_trip_passanger_response(tp) for tp in trip.trip_passangers],
        )

    def _build_trip_passanger_response(self, tp: TripPassangerModel) -> TripPassangerResponse:
        """Resolve nome, endereço e telefone a partir do RoutePassanger."""
        rp = tp.route_passanger

        passanger_name = rp.dependent.name if rp.dependent_id else rp.user.name

        return TripPassangerResponse(
            id=tp.id,
            route_passanger_id=tp.route_passanger_id,
            passanger_name=str(passanger_name),
            status=tp.status,
            pickup_address_label=str(rp.pickup_address.label),
            boarded_at=tp.boarded_at,
            alighted_at=tp.alighted_at,
            user_phone=str(rp.user.phone),
        )

    # US09-TK08
    def get_next_stop(self, trip_id: UUID, driver_id: UUID) -> TripNextStopResponse | None:
        """Retorna a próxima parada pendente (trip_passanger.status='pendente')
        da trip.

        - Valida ownership igual ao get_current_trip.
        - Busca todos os trip_passangers da trip ordenados por Stop.order_index.
        - Retorna o primeiro com status='pendente'. Se não houver, retorna None.
        - O DTO inclui passanger_phone (telefone pro deeplink US13).
        """
        trip = self.trip_repository.find_by_id(trip_id)
        if trip is None:
            raise TripNotFoundError()

        if trip.route.driver_id != driver_id:
            raise TripOwnershipError()

        trip_passangers = self.trip_passanger_repository.find_by_trip(trip_id)

        for tp in trip_passangers:
            if tp.status == "pendente":
                stop = self.stop_repository.find_by_route_passanger_id(tp.route_passanger_id)
                if stop is None:
                    continue

                rp = tp.route_passanger
                passanger_name = rp.dependent.name if rp.dependent_id else rp.user.name
                passanger_phone = rp.user.phone

                return TripNextStopResponse.model_construct(
                    stop_id=stop.id,
                    order_index=stop.order_index,
                    address_label=rp.pickup_address.label,
                    passanger_name=passanger_name,
                    passanger_phone=passanger_phone,
                    trip_passanger_id=tp.id,
                    trip_passanger_status=tp.status,
                )

        return None

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
        trip = self.trip_repository.find_by_id(trip_id)
        if trip is None:
            raise TripNotFoundError(f"Viagem {trip_id} não encontrada.")
        if trip.route.driver_id != driver_id:
            raise TripOwnershipError("Motorista não é dono desta viagem.")
        if trip.status != "iniciada":
            raise TripNotInProgressError("A viagem não está em andamento.")

        tp = self.trip_passanger_repository.find_by_id(trip_passanger_id)
        if tp is None or tp.trip_id != trip_id:
            raise TripPassangerNotFoundError(f"Passageiro {trip_passanger_id} não encontrado na viagem.")

        if tp.status != "pendente":
            raise InvalidTripPassangerStatusError(f"Não é possível marcar presente um passageiro com status '{tp.status}'.")

        now = datetime.now(UTC)
        updated = self.trip_passanger_repository.update_status(trip_passanger_id, "presente", boarded_at=now)
        return self._build_trip_passanger_response(updated)

    # US09-TK10
    def mark_passanger_absent(self, trip_id: UUID, trip_passanger_id: UUID, driver_id: UUID) -> TripPassangerResponse:
        """Marca passageiro como não embarcado (ausente).

        Mesmas validações do board_passanger, mas:
        - Só pode marcar ausente quem está 'pendente'.
        - Atualiza status='ausente' (boarded_at permanece None).
        """
        trip = self.trip_repository.find_by_id(trip_id)
        if trip is None:
            raise TripNotFoundError(f"Viagem {trip_id} não encontrada.")
        if trip.route.driver_id != driver_id:
            raise TripOwnershipError("Motorista não é dono desta viagem.")
        if trip.status != "iniciada":
            raise TripNotInProgressError("A viagem não está em andamento.")

        tp = self.trip_passanger_repository.find_by_id(trip_passanger_id)
        if tp is None or tp.trip_id != trip_id:
            raise TripPassangerNotFoundError(f"Passageiro {trip_passanger_id} não encontrado na viagem.")

        if tp.status != "pendente":
            raise InvalidTripPassangerStatusError(f"Não é possível marcar ausente um passageiro com status '{tp.status}'.")

        updated = self.trip_passanger_repository.update_status(trip_passanger_id, "ausente")
        return self._build_trip_passanger_response(updated)

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
        trip = self.trip_repository.find_by_id(trip_id)
        if trip is None:
            raise TripNotFoundError()

        if trip.route.driver_id != driver_id:
            raise TripOwnershipError()

        if trip.status != "iniciada":
            raise TripNotInProgressError()

        stop = self.stop_repository.find_by_id(stop_id)
        if stop is None or stop.route_id != trip.route_id:
            raise TripStopNotFoundError()

        # Encontrar trip_passangers pendentes para essa stop
        pending_tps = [
            tp
            for tp in self.trip_passanger_repository.find_by_trip(trip_id)
            if tp.route_passanger_id == stop.route_passanger_id and tp.status == "pendente"
        ]

        updated_responses = []
        for tp in pending_tps:
            updated = self.trip_passanger_repository.update_status(tp.id, "ausente")
            updated_responses.append(self._build_trip_passanger_response(updated))

        return updated_responses

    # US09-TK12
    def alight_passanger(self, trip_id: UUID, trip_passanger_id: UUID, driver_id: UUID) -> TripPassangerResponse:
        """Registra desembarque manual de um passageiro.

        - Valida ownership e status da trip (ainda 'iniciada').
        - Valida que trip_passanger.status == 'presente' (só desembarca quem
          embarcou).
        - Atualiza alighted_at=now.
        """
        trip = self.trip_repository.find_by_id(trip_id)
        if trip is None:
            raise TripNotFoundError(f"Viagem {trip_id} não encontrada.")
        if trip.route.driver_id != driver_id:
            raise TripOwnershipError("Motorista não é dono desta viagem.")
        if trip.status != "iniciada":
            raise TripNotInProgressError("A viagem não está em andamento.")

        tp = self.trip_passanger_repository.find_by_id(trip_passanger_id)
        if tp is None or tp.trip_id != trip_id:
            raise TripPassangerNotFoundError(f"Passageiro {trip_passanger_id} não encontrado na viagem.")

        if tp.status != "presente":
            raise InvalidTripPassangerStatusError(f"Não é possível desembarcar um passageiro com status '{tp.status}'.")

        updated = self.trip_passanger_repository.update_status(trip_passanger_id, tp.status, alighted_at=datetime.now(UTC))
        return self._build_trip_passanger_response(updated)

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
