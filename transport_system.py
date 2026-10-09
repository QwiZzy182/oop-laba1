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
