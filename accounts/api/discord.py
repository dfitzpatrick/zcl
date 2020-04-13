from accounts.auth.base import APICaller
import typing

class DiscordAPI(APICaller):

    def me(self) -> typing.Dict[str, typing.Any]:
        return self.get('/users/@me')

