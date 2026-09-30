from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional


# =========================
# Models
# =========================

class Person(ABC):
    def __init__(self, person_id: int, name: str, phone: str):
        self._person_id = int(person_id)
        self.name = name
        self.phone = phone

    @property
    def person_id(self) -> int:
        return self._person_id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValueError("Name is required.")
        self._name = value

    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValueError("Phone is required.")
        self._phone = value

    @abstractmethod
    def get_role(self) -> str:
        pass


class Member(Person):
    def __init__(self, member_id: int, name: str, phone: str, age: int):
        super().__init__(member_id, name, phone)
        self.age = age
        self.__trainer_id: Optional[int] = None

    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int) -> None:
        value = int(value)
        if value < 12 or value > 100:
            raise ValueError("Age must be between 12 and 100.")
        self._age = value

    @property
    def trainer_id(self) -> Optional[int]:
        return self.__trainer_id

    def assign_trainer(self, trainer_id: int) -> None:
        self.__trainer_id = int(trainer_id)

    def remove_trainer(self) -> None:
        self.__trainer_id = None

    def get_role(self) -> str:
        return "Member"

    def to_dict(self) -> dict:
        return {
            "id": self.person_id,
            "name": self.name,
            "phone": self.phone,
            "age": self.age,
            "trainer_id": self.trainer_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Member":
        member = cls(int(data["id"]), data["name"], data["phone"], int(data["age"]))
        if data.get("trainer_id") is not None:
            member.assign_trainer(int(data["trainer_id"]))
        return member


class Trainer(Person):
    def __init__(self, trainer_id: int, name: str, phone: str, specialization: str):
        super().__init__(trainer_id, name, phone)
        self.specialization = specialization

    @property
    def specialization(self) -> str:
        return self._specialization

    @specialization.setter
    def specialization(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValueError("Specialization is required.")
        self._specialization = value

    def get_role(self) -> str:
        return "Trainer"

    def to_dict(self) -> dict:
        return {
            "id": self.person_id,
            "name": self.name,
            "phone": self.phone,
            "specialization": self.specialization,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Trainer":
        return cls(int(data["id"]), data["name"], data["phone"], data["specialization"])


class Membership:
    def __init__(self, membership_id: int, member_id: int, start_date: str, end_date: str, price: float):
        self._membership_id = int(membership_id)
        self.member_id = int(member_id)
        self.start_date = self._validate_date(start_date)
        self.end_date = self._validate_date(end_date)
        if self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date.")
        self.price = float(price)
        if self.price <= 0:
            raise ValueError("Membership price must be greater than zero.")

    @staticmethod
    def _validate_date(value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError as exc:
            raise ValueError("Date must use YYYY-MM-DD format.") from exc

    @property
    def membership_id(self) -> int:
        return self._membership_id

    @property
    def status(self) -> str:
        today = date.today()
        start = datetime.strptime(self.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(self.end_date, "%Y-%m-%d").date()
        if today < start:
            return "Upcoming"
        if today > end:
            return "Expired"
        return "Active"

    def is_active(self) -> bool:
        return self.status == "Active"

    def is_expired(self) -> bool:
        return self.status == "Expired"

    def renew(self, start_date: str, end_date: str, price: float) -> "Membership":
        return Membership(self.membership_id, self.member_id, start_date, end_date, price)

    def to_dict(self) -> dict:
        return {
            "id": self.membership_id,
            "member_id": self.member_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "price": self.price,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Membership":
        return cls(int(data["id"]), int(data["member_id"]), data["start_date"], data["end_date"], float(data["price"]))


class Payment(ABC):
    def __init__(self, payment_id: int, member_id: int, amount: float, payment_date: str | None = None):
        self._payment_id = int(payment_id)
        self.member_id = int(member_id)
        self.amount = float(amount)
        if self.amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")
        self.payment_date = payment_date or datetime.now().strftime("%Y-%m-%d")
        datetime.strptime(self.payment_date, "%Y-%m-%d")

    @property
    def payment_id(self) -> int:
        return self._payment_id

    @abstractmethod
    def process_payment(self) -> str:
        pass

    @abstractmethod
    def payment_type(self) -> str:
        pass

    def to_dict(self) -> dict:
        return {
            "id": self.payment_id,
            "member_id": self.member_id,
            "amount": self.amount,
            "date": self.payment_date,
            "type": self.payment_type(),
        }


class CashPayment(Payment):
    def process_payment(self) -> str:
        return f"Cash payment of {self.amount:.2f} processed."

    def payment_type(self) -> str:
        return "Cash"


class CardPayment(Payment):
    def process_payment(self) -> str:
        return f"Card payment of {self.amount:.2f} processed."

    def payment_type(self) -> str:
        return "Card"


def payment_from_dict(data: dict) -> Payment:
    payment_class = CashPayment if data.get("type") == "Cash" else CardPayment
    return payment_class(int(data["id"]), int(data["member_id"]), float(data["amount"]), data.get("date"))


class Attendance:
    def __init__(self, attendance_id: int, member_id: int, attendance_date: str | None = None):
        self._attendance_id = int(attendance_id)
        self.member_id = int(member_id)
        self.attendance_date = attendance_date or datetime.now().strftime("%Y-%m-%d")
        datetime.strptime(self.attendance_date, "%Y-%m-%d")

    @property
    def attendance_id(self) -> int:
        return self._attendance_id

    def mark_attendance(self) -> bool:
        return True

    def to_dict(self) -> dict:
        return {"id": self.attendance_id, "member_id": self.member_id, "date": self.attendance_date}

    @classmethod
    def from_dict(cls, data: dict) -> "Attendance":
        return cls(int(data["id"]), int(data["member_id"]), data.get("date"))


# =========================
# File Handling
# =========================

class FileManager:
    """Handles JSON persistence for the application."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load(self, filename: str) -> list[dict[str, Any]]:
        path = self.data_dir / filename
        if not path.exists():
            return []
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(f"Could not load {filename}: {exc}") from exc

    def save(self, filename: str, data: list[dict[str, Any]]) -> None:
        path = self.data_dir / filename
        try:
            with path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        except OSError as exc:
            raise RuntimeError(f"Could not save {filename}: {exc}") from exc


# =========================
# Business Logic / Composition
# =========================

class Gym:
    """Main service/facade containing gym business rules and application objects."""

    FILES = {
        "members": "members.json",
        "trainers": "trainers.json",
        "memberships": "memberships.json",
        "payments": "payments.json",
        "attendance": "attendance.json",
    }

    def __init__(self, file_manager: Optional[FileManager] = None):
        self.file_manager = file_manager or FileManager()
        self.members: list[Member] = []
        self.trainers: list[Trainer] = []
        self.memberships: list[Membership] = []
        self.payments: list[Payment] = []
        self.attendances: list[Attendance] = []
        self.load_data()

    @staticmethod
    def _next_id(items: list) -> int:
        ids = []
        for item in items:
            for attr in ("person_id", "membership_id", "payment_id", "attendance_id"):
                if hasattr(item, attr):
                    ids.append(getattr(item, attr))
                    break
        return max(ids, default=0) + 1

    def add_member(self, name: str, phone: str, age: int) -> Member:
        member = Member(self._next_id(self.members), name, phone, age)
        self.members.append(member)
        return member

    def get_member(self, member_id: int) -> Member:
        for member in self.members:
            if member.person_id == int(member_id):
                return member
        raise ValueError("Member not found.")

    def update_member(self, member_id: int, name: str, phone: str, age: int) -> Member:
        member = self.get_member(member_id)
        member.name = name
        member.phone = phone
        member.age = age
        return member

    def delete_member(self, member_id: int) -> None:
        member = self.get_member(member_id)
        if any(m.member_id == member.person_id for m in self.memberships):
            raise ValueError("Cannot delete a member with membership records.")
        self.members.remove(member)

    def search_members(self, query: str) -> list[Member]:
        query = query.strip().lower()
        return [m for m in self.members if query in m.name.lower() or query in str(m.person_id) or query in m.phone]

    def add_trainer(self, name: str, phone: str, specialization: str) -> Trainer:
        trainer = Trainer(self._next_id(self.trainers), name, phone, specialization)
        self.trainers.append(trainer)
        return trainer

    def get_trainer(self, trainer_id: int) -> Trainer:
        for trainer in self.trainers:
            if trainer.person_id == int(trainer_id):
                return trainer
        raise ValueError("Trainer not found.")

    def assign_trainer(self, member_id: int, trainer_id: int) -> None:
        member = self.get_member(member_id)
        self.get_trainer(trainer_id)
        member.assign_trainer(trainer_id)

    def get_membership(self, membership_id: int) -> Membership:
        for membership in self.memberships:
            if membership.membership_id == int(membership_id):
                return membership
        raise ValueError("Membership not found.")

    def get_active_membership(self, member_id: int) -> Optional[Membership]:
        for membership in self.memberships:
            if membership.member_id == int(member_id) and membership.is_active():
                return membership
        return None

    def create_membership(self, member_id: int, start_date: str, end_date: str, price: float) -> Membership:
        self.get_member(member_id)
        if self.get_active_membership(member_id):
            raise ValueError("A member cannot have two active memberships.")
        membership = Membership(self._next_id(self.memberships), member_id, start_date, end_date, price)
        self.memberships.append(membership)
        return membership

    def renew_membership(self, member_id: int, start_date: str, end_date: str, price: float) -> Membership:
        return self.create_membership(member_id, start_date, end_date, price)

    def filter_memberships(self, status: str) -> list[Membership]:
        if status == "All":
            return self.memberships.copy()
        return [m for m in self.memberships if m.status == status]

    def add_payment(self, member_id: int, amount: float, payment_type: str) -> Payment:
        self.get_member(member_id)
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")
        payment_cls = CashPayment if payment_type == "Cash" else CardPayment
        payment = payment_cls(self._next_id(self.payments), member_id, amount)
        self.payments.append(payment)
        return payment

    def record_attendance(self, member_id: int, attendance_date: Optional[str] = None) -> Attendance:
        self.get_member(member_id)
        if not self.get_active_membership(member_id):
            raise ValueError("Attendance cannot be recorded: membership is not active.")
        attendance = Attendance(self._next_id(self.attendances), member_id, attendance_date)
        self.attendances.append(attendance)
        return attendance

    def dashboard(self) -> dict:
        active = len(self.filter_memberships("Active"))
        expired = len(self.filter_memberships("Expired"))
        total_payments = sum(p.amount for p in self.payments)
        today = date.today().isoformat()
        today_attendance = sum(a.attendance_date == today for a in self.attendances)
        return {
            "total_members": len(self.members),
            "total_trainers": len(self.trainers),
            "active_memberships": active,
            "expired_memberships": expired,
            "total_payments": total_payments,
            "today_attendance": today_attendance,
        }

    def save_data(self) -> None:
        self.file_manager.save(self.FILES["members"], [m.to_dict() for m in self.members])
        self.file_manager.save(self.FILES["trainers"], [t.to_dict() for t in self.trainers])
        self.file_manager.save(self.FILES["memberships"], [m.to_dict() for m in self.memberships])
        self.file_manager.save(self.FILES["payments"], [p.to_dict() for p in self.payments])
        self.file_manager.save(self.FILES["attendance"], [a.to_dict() for a in self.attendances])

    def load_data(self) -> None:
        self.members = [Member.from_dict(x) for x in self.file_manager.load(self.FILES["members"])]
        self.trainers = [Trainer.from_dict(x) for x in self.file_manager.load(self.FILES["trainers"])]
        self.memberships = [Membership.from_dict(x) for x in self.file_manager.load(self.FILES["memberships"])]
        self.payments = [payment_from_dict(x) for x in self.file_manager.load(self.FILES["payments"])]
        self.attendances = [Attendance.from_dict(x) for x in self.file_manager.load(self.FILES["attendance"])]
