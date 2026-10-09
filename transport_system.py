import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Dict, List, Any

# =========================================================================
# 1. ИЕРАРХИЯ ИСКЛЮЧЕНИЙ (5 классов)
# =========================================================================
class VehicleError(Exception):
    """Базовое исключение для автопарка транспортных средств."""


class ValidationError(VehicleError):
    """Ошибка валидации данных (пустые строки, некорректные характеристики)."""


class DuplicateEntityError(VehicleError):
    """Ошибка при попытке добавить ТС с уже существующим VIN-кодом."""


class EntityNotFoundError(VehicleError):
    """Ошибка при поиске несуществующего транспортного средства."""


class DataFormatError(VehicleError):
    """Ошибка формата данных при чтении/записи JSON или XML."""
    
class Vehicle(ABC):
    """Абстрактный базовый класс транспортного средства."""

    def __init__(self, vin: str, brand: str, model: str, price: float) -> None:
        if not vin or not vin.strip():
            raise ValidationError("Идентификационный номер (VIN) не может быть пустым.")
        if not brand or not brand.strip():
            raise ValidationError("Марка транспортного средства не может быть пустой.")
        if not model or not model.strip():
            raise ValidationError("Модель транспортного средства не может быть пустой.")
        if price < 0:
            raise ValidationError(f"Стоимость ТС не может быть отрицательной: {price}")

        self.vin: str = vin.strip().upper()
        self.brand: str = brand.strip()
        self.model: str = model.strip()
        self.price: float = float(price)

    @abstractmethod
    def get_info(self) -> str:
        """Краткая информация о транспортном средстве."""

    def __str__(self) -> str:
        return self.get_info()


class PassengerVehicle(Vehicle):
    """Пассажирский транспорт (Легковые автомобили, автобусы). Хранится в JSON."""

    def __init__(self, vin: str, brand: str, model: str, price: float,
                 body_type: str, seats_count: int) -> None:
        super().__init__(vin, brand, model, price)
        if not body_type or not body_type.strip():
            raise ValidationError("Тип кузова должен быть указан.")
        if seats_count <= 0:
            raise ValidationError(f"Количество мест должно быть больше нуля: {seats_count}")

        self.body_type: str = body_type.strip()
        self.seats_count: int = seats_count

    def get_info(self) -> str:
        return (f"Пассажирский [VIN: {self.vin}]: {self.brand} {self.model} "
                f"({self.body_type}), мест: {self.seats_count}. Цена: {self.price} руб.")

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация объекта в словарь для сохранения в JSON."""
        return {
            "vin": self.vin,
            "brand": self.brand,
            "model": self.model,
            "price": self.price,
            "body_type": self.body_type,
            "seats_count": self.seats_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PassengerVehicle":
        """Десериализация объекта из словаря JSON."""
        try:
            return cls(
                vin=data["vin"],
                brand=data["brand"],
                model=data["model"],
                price=data["price"],
                body_type=data["body_type"],
                seats_count=data["seats_count"]
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise DataFormatError(f"Ошибка чтения данных PassengerVehicle: {exc}") from exc


class CargoVehicle(Vehicle):
    """Грузовой транспорт (Тягачи, фургоны, самосвалы). Хранится в XML."""

    def __init__(self, vin: str, brand: str, model: str, price: float,
                 load_capacity_tons: float, axles_count: int) -> None:
        super().__init__(vin, brand, model, price)
        if load_capacity_tons <= 0:
            raise ValidationError(f"Грузоподъемность должна быть больше нуля: {load_capacity_tons}")
        if axles_count < 2:
            raise ValidationError(f"Количество осей у грузового ТС не может быть меньше 2: {axles_count}")

        self.load_capacity_tons: float = load_capacity_tons
        self.axles_count: int = axles_count

    def get_info(self) -> str:
        return (f"Грузовой [VIN: {self.vin}]: {self.brand} {self.model}, "
                f"г/п: {self.load_capacity_tons} т., осей: {self.axles_count}. Цена: {self.price} руб.")

    def to_xml(self) -> ET.Element:
        """Сериализация объекта в XML-элемент."""
        elem = ET.Element("vehicle")
        ET.SubElement(elem, "vin").text = self.vin
        ET.SubElement(elem, "brand").text = self.brand
        ET.SubElement(elem, "model").text = self.model
        ET.SubElement(elem, "price").text = str(self.price)
        ET.SubElement(elem, "load_capacity_tons").text = str(self.load_capacity_tons)
        ET.SubElement(elem, "axles_count").text = str(self.axles_count)
        return elem

    @classmethod
    def from_xml(cls, element: ET.Element) -> "CargoVehicle":
        """Десериализация объекта из XML-элемента."""
        try:
            return cls(
                vin=element.findtext("vin", ""),
                brand=element.findtext("brand", ""),
                model=element.findtext("model", ""),
                price=float(element.findtext("price", "0")),
                load_capacity_tons=float(element.findtext("load_capacity_tons", "0")),
                axles_count=int(element.findtext("axles_count", "0"))
            )
        except (TypeError, ValueError) as exc:
            raise DataFormatError(f"Ошибка чтения данных CargoVehicle из XML: {exc}") from exc
