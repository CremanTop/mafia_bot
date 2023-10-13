from typing import Optional

from Role import Role


class Player:
    def __init__(self, chat_id, role: Role, virtual: bool = False):
        self.virtual: bool = virtual
        self.id: int = chat_id
        self.role: Role = role
        self.choosen_kill: int = 0
        self.choosen_doctor: int = 0
        self.choosen_beauty: int = 0
        self.choosen_godfather: int = 0
        self.choosen_barman: int = 0
        self.choosen_bodyguard: int = 0
        self.choosen_snitch: int = 0
        self.target: Optional[Player] = None
        self.old_target: Optional[Player] = None
        self.medium_who_contact: Optional[Player] = None
        self.choosed: bool = False
        self.mute: bool = False
        self.drunk: bool = False
        self.voted: bool = False
        self.voices: int = 0

    def __eq__(self, other):
        if not isinstance(other, Player):
            raise TypeError("Операнд справа должен иметь тип Player")
        return self.id == other.id

    def __ne__(self, other):
        if not isinstance(other, Player):
            raise TypeError("Операнд справа должен иметь тип Player")
        return self.id != other.id
