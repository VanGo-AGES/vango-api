from sqlalchemy.orm import Session

from src.domains.addresses.entity import AddressModel
from src.domains.routes.repository import IAddressRepository


class AddressRepositoryImpl(IAddressRepository):
    def __init__(self, session: Session):
        self.session = session

    def save(self, address: AddressModel) -> AddressModel:
        self.session.add(address)
        self.session.commit()
        self.session.refresh(address)
        return address
