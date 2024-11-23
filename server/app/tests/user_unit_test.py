import unittest
from unittest.mock import MagicMock, Mock

from api.user.user_model import User
from api.user.user_repo import UserRepo
from api.user.user_service import UserService

class TestUserService(unittest.TestCase):  
    def setUp(self):
        self.user_repo = MagicMock(spec=UserRepo)
        self.service = UserService(self.user_repo)

    def test_add(self):
        user = User(id=1)
        self.user_repo.add.return_value = user

        user = self.service.add(user)


        self.assertEquals(user.id, 1)
        self.user_repo.add.assert_called_once()


if __name__ == '__main__':
    unittest.main()