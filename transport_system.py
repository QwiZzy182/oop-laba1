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
# =========================================================================
# 3. УПРАВЛЕНИЕ ХРАНИМЫМИ ДАННЫМИ ПО СИСТЕМЕ CRUD (2 класса)
# =========================================================================
class PassengerVehicleRepository:
    """Репозиторий, реализующий полный цикл CRUD для пассажирского транспорта."""

    def __init__(self) -> None:
        self._vehicles: Dict[str, PassengerVehicle] = {}

    def create(self, vehicle: PassengerVehicle) -> None:
        """[C]reate: Зарегистрировать новое транспортное средство."""
        if vehicle.vin in self._vehicles:
            raise DuplicateEntityError(f"Транспортное средство с VIN {vehicle.vin} уже существует.")
        self._vehicles[vehicle.vin] = vehicle

    def read_all(self) -> List[PassengerVehicle]:
        """[R]ead: Вернуть весь список пассажирского транспорта."""
        return list(self._vehicles.values())

    def read_by_vin(self, vin: str) -> PassengerVehicle:
        """[R]ead: Найти ТС по его уникальному VIN."""
        vin_upper = vin.strip().upper()
        if vin_upper not in self._vehicles:
            raise EntityNotFoundError(f"Пассажирское ТС с VIN {vin_upper} не найдено.")
        return self._vehicles[vin_upper]

    def update(self, vin: str, updated_vehicle: PassengerVehicle) -> None:
        """[U]pdate: Изменить параметры существующего ТС."""
        vin_upper = vin.strip().upper()
        if vin_upper not in self._vehicles:
            raise EntityNotFoundError(f"Транспорт с VIN {vin_upper} не найден для обновления.")
        if vin_upper != updated_vehicle.vin:
            raise ValidationError("Изменение VIN-кода при обновлении записи запрещено.")
        self._vehicles[vin_upper] = updated_vehicle

    def delete(self, vin: str) -> None:
        """[D]elete: Снять ТС с учета (удалить из каталога)."""
        vin_upper = vin.strip().upper()
        if vin_upper not in self._vehicles:
            raise EntityNotFoundError(f"Транспорт с VIN {vin_upper} не найден для удаления.")
        del self._vehicles[vin_upper]

    def clear(self) -> None:
        """Очистить локальное хранилище репозитория."""
        self._vehicles.clear()


class CargoVehicleRepository:
    """Репозиторий, реализующий полный цикл CRUD для грузового транспорта."""

    def __init__(self) -> None:
        self._vehicles: Dict[str, CargoVehicle] = {}

    def create(self, vehicle: CargoVehicle) -> None:
        """[C]reate: Зарегистрировать новый грузовик."""
        if vehicle.vin in self._vehicles:
            raise DuplicateEntityError(f"Грузовое ТС с VIN {vehicle.vin} уже существует.")
        self._vehicles[vehicle.vin] = vehicle

    def read_all(self) -> List[CargoVehicle]:
        """[R]ead: Получить весь список грузового транспорта."""
        return list(self._vehicles.values())

    def read_by_vin(self, vin: str) -> CargoVehicle:
        """[R]ead: Найти грузовое ТС по VIN."""
        vin_upper = vin.strip().upper()
        if vin_upper not in self._vehicles:
            raise EntityNotFoundError(f"Грузовое ТС с VIN {vin_upper} не найдено.")
        return self._vehicles[vin_upper]

    def update(self, vin: str, updated_vehicle: CargoVehicle) -> None:
        """[U]pdate: Обновить информацию о грузовом ТС."""
        vin_upper = vin.strip().upper()
        if vin_upper not in self._vehicles:
            raise EntityNotFoundError(f"Грузовик с VIN {vin_upper} не найден для обновления.")
        if vin_upper != updated_vehicle.vin:
            raise ValidationError("Изменение VIN-кода при обновлении записи запрещено.")
        self._vehicles[vin_upper] = updated_vehicle

    def delete(self, vin: str) -> None:
        """[D]elete: Удалить грузовик по его VIN."""
        vin_upper = vin.strip().upper()
        if vin_upper not in self._vehicles:
            raise EntityNotFoundError(f"Грузовик с VIN {vin_upper} не найден для удаления.")
        del self._vehicles[vin_upper]

    def clear(self) -> None:
        """Очистить локальное хранилище репозитория."""
        self._vehicles.clear()
# =========================================================================
# 4. ФАСАД СИСТЕМЫ УПРАВЛЕНИЯ АВТОПАРКОМ (1 класс)
# =========================================================================
class FleetManager:
    """Единый диспетчерский центр для работы с файлами и репозиториями автопарка."""

    def __init__(self) -> None:
        self.passenger_repo: PassengerVehicleRepository = PassengerVehicleRepository()
        self.cargo_repo: CargoVehicleRepository = CargoVehicleRepository()

    # --- Подсистема JSON (Пассажирский транспорт) ---
    def save_passenger_json(self, path: str) -> None:
        """Экспорт коллекции пассажирского транспорта в JSON-файл."""
        data = [v.to_dict() for v in self.passenger_repo.read_all()]
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except OSError as exc:
            raise DataFormatError(f"Ошибка сохранения JSON по пути {path}: {exc}") from exc

    def load_passenger_json(self, path: str) -> None:
        """Импорт коллекции пассажирского транспорта из JSON-файла."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise DataFormatError(f"Ошибка загрузки JSON из файла {path}: {exc}") from exc
        if not isinstance(data, list):
            raise DataFormatError("Неверная структура данных JSON (ожидался корневой список)")

        self.passenger_repo.clear()
        for item in data:
            self.passenger_repo.create(PassengerVehicle.from_dict(item))

    # --- Подсистема XML (Грузовой транспорт) ---
    def save_cargo_xml(self, path: str) -> None:
        """Экспорт коллекции грузового транспорта в XML-файл."""
        root = ET.Element("cargo_fleet")
        for vehicle in self.cargo_repo.read_all():
            root.append(vehicle.to_xml())
        tree = ET.ElementTree(root)
        try:
            tree.write(path, encoding="utf-8", xml_declaration=True)
        except OSError as exc:
            raise DataFormatError(f"Ошибка сохранения XML по пути {path}: {exc}") from exc

    def load_cargo_xml(self, path: str) -> None:
        """Импорт коллекции грузового транспорта из XML-файла."""
        try:
            tree = ET.parse(path)
        except (OSError, ET.ParseError) as exc:
            raise DataFormatError(f"Ошибка разбора структуры XML из файла {path}: {exc}") from exc
        root = tree.getroot()
        if root.tag != "cargo_fleet":
            raise DataFormatError(f"Некорректный корневой тег XML: <{root.tag}> вместо <cargo_fleet>")

        self.cargo_repo.clear()
        for elem in root.findall("vehicle"):
            self.cargo_repo.create(CargoVehicle.from_xml(elem))

    def print_fleet_report(self) -> None:
        """Вывод сводного отчета о состоянии всего автопарка."""
        print("=" * 85)
        print(" СВОДНАЯ ВЕДОМОСТЬ ТРАНСПОРТНЫХ СРЕДСТВ АВТОПАРКА")
        print("=" * 85)
        print("ПАССАЖИРСКИЙ АВТОТРАНСПОРТ (База JSON):")
        p_vehicles = self.passenger_repo.read_all()
        if not p_vehicles:
            print("  [Транспортные средства отсутствуют]")
        for pv in p_vehicles:
            print("  •", pv)

        print("\nГРУЗОВОЙ И СПЕЦИАЛЬНЫЙ АВТОТРАНСПОРТ (База XML):")
        c_vehicles = self.cargo_repo.read_all()
        if not c_vehicles:
            print("  [Транспортные средства отсутствуют]")
        for cv in c_vehicles:
            print("  •", cv)
        print("=" * 85)


# =========================================================================
# ДЕМОНСТРАЦИОННЫЙ СЦЕНАРИЙ И ТОЧКА ВХОДА В ПРОГРАММУ
# =========================================================================
def main() -> None:
    # 1. Проверка валидации данных и отработки бизнес-исключений
    print("--- 1. Проверка защитных барьеров (Валидация) ---")
    try:
        PassengerVehicle("VIN-FAIL", "Lada", "Vesta", -850000, "Седан", 5)
    except ValidationError as err:
        print(f"[Успешный перехват]: Заблокирована некорректная цена ТС -> {err}")

    try:
        CargoVehicle("VIN-OK", "KAMAZ", " ", 4500000, 15.0, 3)
    except ValidationError as err:
        print(f"[Успешный перехват]: Заблокирована пустая модель ТС -> {err}")

    # 2. Наполнение базы через CRUD-операции (Create)
    print("\n--- 2. Первичное формирование автопарка (CRUD: Create) ---")
    manager = FleetManager()

    # Добавление легковых автомобилей
    manager.passenger_repo.create(PassengerVehicle("VINPASS01", "Tesla", "Model S", 7500000, "Лифтбек", 5))
    manager.passenger_repo.create(PassengerVehicle("VINPASS02", "Mercedes-Benz", "Sprinter", 3800000, "Автобус", 19))

    # Добавление грузовиков
    manager.cargo_repo.create(CargoVehicle("VINCARGO01", "Scania", "R500", 9200000, 25.5, 3))
    manager.cargo_repo.create(CargoVehicle("VINCARGO02", "Volvo", "FH16", 11000000, 30.0, 4))

    manager.print_fleet_report()

    # 3. Модификация данных и точечное чтение (CRUD: Update и Read)
    print("\n--- 3. Корректировка параметров и чтение (CRUD: Update/Read) ---")
    # Считываем объект по VIN, создаем обновленную модель (например, изменилась цена)
    car_to_update = manager.passenger_repo.read_by_vin("VINPASS01")
    updated_car = PassengerVehicle(
        vin="VINPASS01",
        brand=car_to_update.brand,
        model=car_to_update.model,
        price=8200000.0,  # Изменили стоимость
        body_type=car_to_update.body_type,
        seats_count=car_to_update.seats_count
    )
    manager.passenger_repo.update("VINPASS01", updated_car)
    print("Цена на транспортное средство с VIN-кодом VINPASS01 успешно обновлена.")

    # Демонстрация удаления (CRUD: Delete)
    temp_truck = CargoVehicle("VINTEMP99", "GAZ", "Next", 1500000, 3.5, 2)
    manager.cargo_repo.create(temp_truck)
    print(f"Поставлен на временный учет GAZ. Всего грузовиков: {len(manager.cargo_repo.read_all())}")
    manager.cargo_repo.delete("VINTEMP99")
    print(f"Снят с учета (удален) GAZ. Осталось грузовиков в базе: {len(manager.cargo_repo.read_all())}")

    # 4. Синхронизация с постоянными хранилищами (Экспорт на диск)
    print("\n--- 4. Экспорт актуального состояния базы в файлы данных ---")
    json_path = "fleet_passengers.json"
    xml_path = "fleet_cargo.xml"

    manager.save_passenger_json(json_path)
    manager.save_cargo_xml(xml_path)
    print(f"Файлы '{json_path}' и '{xml_path}' успешно сгенерированы и сохранены.")

    # 5. Демонстрация полной независимой изоляции и десериализации данных
    print("\n--- 5. Инициализация чистого менеджера и чтение файлов ---")
    isolated_manager = FleetManager()
    isolated_manager.load_passenger_json(json_path)
    isolated_manager.load_cargo_xml(xml_path)

    # Демонстрируем восстановленный с жесткого диска каталог
    isolated_manager.print_fleet_report()


if __name__ == "__main__":
    main()
