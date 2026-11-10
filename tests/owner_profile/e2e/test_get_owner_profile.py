from uuid import uuid4

from tests.owner_profile.e2e.conftest import OWNER_PROFILES_PATH, auth, valid_payload

MY_OWNER_PROFILE_PATH = '/api/v1/owner-profiles/me'


def _error(message):
    return {'success': False, 'message': message, 'data': None, 'detail': None}


class TestGetOwnerProfile:
    async def test_returns_200_with_the_profile_the_user_registered(self, client):
        user_uuid = uuid4()
        registered = await client.post(
            OWNER_PROFILES_PATH, json=valid_payload(), headers=auth(user_uuid)
        )

        response = await client.get(MY_OWNER_PROFILE_PATH, headers=auth(user_uuid))

        assert response.status_code == 200
        assert response.json() == registered.json()

    async def test_returns_404_when_the_user_has_no_owner_profile(self, client):
        response = await client.get(MY_OWNER_PROFILE_PATH, headers=auth(uuid4()))

        assert response.status_code == 404
        assert response.json() == _error('You do not have an owner profile.')

    async def test_returns_401_without_a_token(self, client):
        response = await client.get(MY_OWNER_PROFILE_PATH)

        assert response.status_code == 401
        assert response.json() == _error('You must sign in to continue.')
