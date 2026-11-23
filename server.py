import asyncio
import secrets
import time
from html import escape
from urllib.parse import parse_qs

from mcp.server import MCPServer
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    AuthorizeError,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    RegistrationError,
    TokenError,
    construct_redirect_uri,
)
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from sqlalchemy.engine import make_url
from sshtunnel import SSHTunnelForwarder
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response

from app.include.config import config
from app.include.logging_config import logger as log
from app.integrations import StDiaryMCP, StPostgreSQLMCP, StSleepMCP


class OAuthProvider(OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]):
    def __init__(self):
        self.issuer_url = "https://mcp.sleeptery.ru"
        self.resource_url = f"{self.issuer_url}/mcp"
        self.scopes = ["mcp:access"]
        self.login_path = "/oauth/login"
        self.settings = AuthSettings(
            issuer_url=self.issuer_url,
            resource_server_url=self.resource_url,
            required_scopes=self.scopes,
            validate_token_resource=True,
            client_registration_options=ClientRegistrationOptions(
                enabled=True,
                valid_scopes=self.scopes,
                default_scopes=self.scopes,
            ),
        )

        self._clients: dict[str, OAuthClientInformationFull] = {}
        self._pending: dict[str, tuple[AuthorizationCode, str | None]] = {}
        self._codes: dict[str, AuthorizationCode] = {}
        self._access_tokens: dict[str, AccessToken] = {}
        self._refresh_tokens: dict[str, RefreshToken] = {}

    def _matches_api_token(self, token: str) -> bool:
        api_token = config.MCP_API_TOKEN
        return bool(api_token) and secrets.compare_digest(token.encode(), api_token.encode())

    async def get_client(self, client_id: str):
        return self._clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull):
        for uri in client_info.redirect_uris or []:
            loopback = uri.scheme == "http" and uri.host in {"localhost", "127.0.0.1", "[::1]"}
            if (uri.scheme != "https" and not loopback) or uri.fragment or not uri.host:
                raise RegistrationError("invalid_redirect_uri", "Use HTTPS or a loopback HTTP URL")
        if len(client_info.model_dump_json()) > 8192 or len(self._clients) >= 1024:
            raise RegistrationError("invalid_client_metadata", "Client registration limit reached")
        self._clients[client_info.client_id] = client_info

    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams):
        if params.resource not in (None, self.resource_url):
            raise AuthorizeError("invalid_target", "Unknown MCP resource")

        now = time.time()
        self._pending = {
            key: entry for key, entry in self._pending.items()
            if entry[0].expires_at > now
        }
        if len(self._pending) >= 256:
            raise AuthorizeError("temporarily_unavailable", "Too many pending logins")
        login_id = secrets.token_urlsafe(32)
        self._pending[login_id] = (
            AuthorizationCode(
                code=secrets.token_urlsafe(32),
                scopes=params.scopes or self.scopes,
                expires_at=now + 300,
                client_id=client.client_id,
                code_challenge=params.code_challenge,
                redirect_uri=params.redirect_uri,
                redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
                resource=self.resource_url,
            ),
            params.state,
        )
        return f"{self.issuer_url}{self.login_path}/{login_id}"

    async def load_authorization_code(self, client: OAuthClientInformationFull, authorization_code: str):
        return self._codes.get(authorization_code)

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode,
    ) -> OAuthToken:
        if self._codes.pop(authorization_code.code, None) is None:
            raise TokenError("invalid_grant")
        return self._issue_tokens(client, authorization_code.scopes)

    async def load_refresh_token(self, client: OAuthClientInformationFull, refresh_token: str):
        return self._refresh_tokens.get(refresh_token)

    async def exchange_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: RefreshToken, scopes: list[str],
    ) -> OAuthToken:
        if self._refresh_tokens.pop(refresh_token.token, None) is None:
            raise TokenError("invalid_grant")
        return self._issue_tokens(client, scopes)

    def _issue_tokens(self, client: OAuthClientInformationFull, scopes: list[str]) -> OAuthToken:
        now = int(time.time())
        access = secrets.token_urlsafe(32)
        refresh = None
        access_lifetime = 3600
        self._access_tokens = {
            key: token for key, token in self._access_tokens.items()
            if token.expires_at is not None and token.expires_at > now
        }
        self._access_tokens[access] = AccessToken(
            token=access, client_id=client.client_id, scopes=scopes,
            expires_at=now + access_lifetime, resource=self.resource_url,
        )
        if "refresh_token" in client.grant_types:
            refresh = secrets.token_urlsafe(32)
            self._refresh_tokens = {
                key: token for key, token in self._refresh_tokens.items()
                if token.expires_at is not None and token.expires_at > now
            }
            self._refresh_tokens[refresh] = RefreshToken(
                token=refresh, client_id=client.client_id, scopes=scopes, expires_at=now + 30 * 86400,
                resource=self.resource_url,
            )
        return OAuthToken(
            access_token=access, refresh_token=refresh, expires_in=access_lifetime, scope=" ".join(scopes),
        )

    async def load_access_token(self, token: str):
        if self._matches_api_token(token):
            return AccessToken(
                token=token, client_id="sleeptery", scopes=self.scopes, resource=self.resource_url,
            )
        return self._access_tokens.get(token)

    async def login(self, request: Request) -> Response:
        headers = {
            "Cache-Control": "no-store",
            "Referrer-Policy": "same-origin",
            "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
        }
        login_id = request.path_params["login_id"]
        pending = self._pending.get(login_id)
        if pending is None or pending[0].expires_at <= time.time():
            return HTMLResponse("Срок запроса истёк. Начните вход заново.", status_code=400, headers=headers)

        code, state = pending
        message = ""
        if request.method == "POST":
            if request.headers.get("origin") != self.issuer_url:
                return Response(status_code=403, headers=headers)
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > 8192:
                    return Response(status_code=413, headers=headers)
                body.extend(chunk)
            fields = parse_qs(body.decode("ascii", errors="replace"))
            if self._matches_api_token(fields.get("token", [""])[0]):
                now = time.time()
                if self._pending.pop(login_id, None) is None or code.expires_at <= now:
                    return Response(status_code=400, headers=headers)
                code.expires_at = now + 60
                self._codes = {
                    key: entry for key, entry in self._codes.items()
                    if entry.expires_at > now
                }
                self._codes[code.code] = code
                return RedirectResponse(
                    construct_redirect_uri(
                        str(code.redirect_uri), code=code.code, state=state, iss=self.issuer_url,
                    ),
                    status_code=303, headers=headers,
                )
            message = "<p>Неверный токен.</p>"

        return HTMLResponse(
            '<!doctype html><html lang="ru"><meta charset="utf-8"><title>Sleeptery MCP</title>'
            f'<h1>Доступ к Sleeptery MCP</h1><p>Приложение: {escape(code.redirect_uri.host or "")}</p>'
            f'{message}<form method="post"><label>MCP API-токен '
            '<input type="password" name="token" required></label> '
            '<button type="submit">Разрешить доступ</button></form></html>',
            status_code=401 if message else 200,
            headers=headers,
        )


class SleepteryMCP:
    def __init__(self):
        self.oauth = OAuthProvider()
        self.server = MCPServer(
            "Sleeptery AI MCP server",
            auth_server_provider=self.oauth,
            auth=self.oauth.settings,
        )
        self.server.custom_route(
            f"{self.oauth.login_path}/{{login_id}}", methods=["GET", "POST"],
        )(self.oauth.login)
        self._register_integrations()

    def _register_integrations(self):
        StSleepMCP(self.server)
        StDiaryMCP(self.server)
        StPostgreSQLMCP(self.server)

    async def _log_registered_tools(self):
        tools = await self.server.list_tools()
        log.info(f"Зарегистрировано MCP tools: {len(tools)}")
        for tool in tools:
            log.info(f"  ✓ {tool.name}")

    def run(self):
        with SSHTunnelForwarder(
            (config.PROD_IP, 22),
            ssh_username="root",
            ssh_pkey=config.SSH_KEY_PATH,
            remote_bind_address=("127.0.0.1", 8402),
        ) as tunnel:
            db_url = make_url(config.DB_AI_URL)

            config.DB_AI_URL = db_url.set(
                host="127.0.0.1",
                port=tunnel.local_bind_port,
            ).render_as_string(hide_password=False)

            log.info(
                f"SSH-туннель запущен: "
                f"127.0.0.1:{tunnel.local_bind_port} -> "
                f"{config.PROD_IP}:8402"
            )

            asyncio.run(self._log_registered_tools())

            log.info("Запускаем MCP сервер")

            self.server.run(
                transport="streamable-http",
                host="0.0.0.0",
                port=8800,
            )


app = SleepteryMCP()
server = app.server


if __name__ == "__main__":
    app.run()
