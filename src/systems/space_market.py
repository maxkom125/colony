from .. import constants
from ..enums import ResourceType
from typing import Dict
from ..logger import logger # Import the logger
from ..entities.planet import Planet


class SpaceMarket:
    """Handles dynamic resource conversion rates and transactions."""

    def __init__(self):
        # Load fee
        self.fee_percent = constants.CONVERSION_FEE_PERCENT

        # --- Base Rates (Loaded from constants) ---
        self.base_sell_rates: dict[ResourceType, float] = {
            ResourceType.TRITANIUM: constants.SELL_TRITANIUM_RATE,
            ResourceType.PLASMA: constants.SELL_PLASMA_RATE,
        }
        self.base_buy_rates: dict[ResourceType, float] = {
            ResourceType.TRITANIUM: constants.BUY_TRITANIUM_RATE,
            ResourceType.PLASMA: constants.BUY_PLASMA_RATE,
        }

        # --- Current Rates (Initialize as copies of base rates) ---
        self.current_sell_rates = self.base_sell_rates.copy()
        self.current_buy_rates = self.base_buy_rates.copy()

    def _attempt_transaction(
        self,
        storage: dict[ResourceType, float],
        res_decrease: ResourceType,
        amount_decrease: float,
        res_increase: ResourceType,
        amount_increase: float,
    ) -> bool:
        """Checks funds and updates storage if transaction is possible."""
        available_amount = storage.get(res_decrease, 0)

        if available_amount < amount_decrease:
            logger.warning(
                f"Not enough {res_decrease} to perform transaction. Need {amount_decrease:.2f}, have {available_amount:.2f}"
            )
            return False

        storage[res_decrease] -= amount_decrease
        storage[res_increase] += amount_increase
        return True

    def _buy_sell_checks(
        self,
        resource: ResourceType,
        amount_of_resource: float,
    ) -> bool:
        if resource == ResourceType.CREDITS:
            logger.warning("Attempted to buy/sell Credits, which is not allowed.")
            return False
        if amount_of_resource <= 0:
            logger.warning(f"Conversion amount must be positive, got {amount_of_resource}.")
            return False
        return True

    def get_buy_cost(
        self,
        resource: ResourceType,
        amount_of_resource: float,
    ) -> float:
        """Calculates the amount of Credits needed to buy a resource."""
        rate = self.current_buy_rates.get(resource, float("inf"))
        credit_cost = amount_of_resource * rate
        credit_cost *= 1 + self.fee_percent  # Apply fee
        return credit_cost

    def get_sell_gain(
        self,
        resource: ResourceType,
        amount_of_resource: float,
    ) -> float:
        """Calculates the amount of Credits received from selling a resource."""
        rate = self.current_sell_rates.get(resource, 0)
        credit_gain = amount_of_resource * rate
        credit_gain *= 1 - self.fee_percent  # Apply fee
        return credit_gain

    def buy_resource(
        self,
        planet_storage: Dict[str, float],
        resource: ResourceType,
        amount_of_resource: float,
    ) -> bool:
        """Buys a resource using Credits."""
        # ---- Checks ----
        if not self._buy_sell_checks(resource, amount_of_resource):
            return False

        # ---- Calculation ----
        credit_cost = self.get_buy_cost(resource, amount_of_resource)

        # ---- Transaction ----
        transaction_successful = self._attempt_transaction(
            storage=planet_storage,
            res_decrease=ResourceType.CREDITS,
            amount_decrease=credit_cost,
            res_increase=resource,
            amount_increase=amount_of_resource,
        )
        # TODO: Adjust market rates based on the transaction.
        return transaction_successful

    def sell_resource(
        self,
        planet_storage: Dict[str, float],
        resource: ResourceType,
        amount_of_resource: float,
    ) -> bool:
        """Sells a resource for Credits."""
        # ---- Checks ----
        if not self._buy_sell_checks(resource, amount_of_resource):
            return False

        # ---- Calculation ----
        credit_gain = self.get_sell_gain(resource, amount_of_resource)

        # ---- Transaction ----
        transaction_successful = self._attempt_transaction(
            storage=planet_storage,
            res_decrease=resource,
            amount_decrease=amount_of_resource,
            res_increase=ResourceType.CREDITS,
            amount_increase=credit_gain,
        )
        # TODO: Adjust market rates based on the transaction.
        return transaction_successful
