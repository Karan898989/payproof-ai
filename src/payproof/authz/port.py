from typing import Protocol
from ..domain.enums import RoleName
from ..domain.models import User, PaymentCase

class AuthorizationPort(Protocol):
    def is_authorized(
        self,
        user: User,
        action: str,
        resource: PaymentCase | None = None,
        context: dict | None = None,
    ) -> bool:
        """Determines if the user is authorized to perform action on resource."""
        ...
