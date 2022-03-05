import logging
import pathlib
from typing import Any, Callable, Coroutine, ParamSpec
from functools import wraps
from urllib.parse import urlparse, urlencode

import yaml
import httpx
import uvicorn
from single_source import get_version
from starlette.routing import Mount, Route
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from starlette.templating import Jinja2Templates, _TemplateResponse
from starlette.staticfiles import StaticFiles
from starlette.applications import Starlette

logger = logging.getLogger(__name__)
P = ParamSpec("P")


class _Config(yaml.YAMLObject):
    def __init__(self):
        try:
            with open("config.yaml", "r") as f:
                items = yaml.safe_load(f)

            self.blocky_api_url = items["blocky_api_url"]
            self.blocky_allowed_path = pathlib.Path(items["blocky_allowed_path"])
            self.cwd = pathlib.Path(__file__).parent

            self.host = str(items.get("blocky_web_server_host", ""))

        except (KeyError, FileNotFoundError):
            raise Exception("Ensure a configuration file titled `config.yaml` is properly filled out.")


config = _Config()
templates = Jinja2Templates(directory=config.cwd.joinpath("templates"))
templates.env.globals["version"] = get_version(__name__, config.cwd.parent)


def add_status(
    func: Callable[P, Coroutine[Any, Any, _TemplateResponse]]
) -> Callable[P, Coroutine[Any, Any, _TemplateResponse]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> _TemplateResponse:
        r = await func(*args, **kwargs)
        if isinstance(r, _TemplateResponse):
            r.context["enabled"] = httpx.get(f"{config.blocky_api_url}blocking/status").json().get("enabled")
            r.body = r.render(r.template.render(r.context))
            r.init_headers()
        return r

    return wrapper


async def redirect(request: Request) -> RedirectResponse:
    if not config.host:
        try:
            host, _ = request.scope["server"]

        except KeyError:
            raise Exception("Unable to determine server settings. Please set blocky_web_server_host in config.yaml")

    else:
        host = config.host

    blocky_web_server = f"http://{host}"
    domain = urlencode({"domain": request.base_url.netloc})

    return RedirectResponse(f"{blocky_web_server}{urlparse(request.url_for('block')).path}?{domain}")


@add_status
async def block(request: Request) -> _TemplateResponse:
    return templates.TemplateResponse(
        "block.html.j2", context={"request": request, "url": request.query_params.get("domain")}
    )


@add_status
async def admin(request: Request) -> _TemplateResponse:
    return templates.TemplateResponse("base.html.j2", context={"request": request})


### "API" METHODS
async def api(request: Request) -> JSONResponse:
    body = await request.json()
    action = urlparse(body.get("action")).path[1:]

    match action:
        case "query":
            return JSONResponse(query(domain=body.get("domain")))

        case "toggle":
            return JSONResponse(toggle(state=body.get("state")))

        case "add":
            return JSONResponse(add(domain=body.get("domain"), redirect=body.get("redirect")))

        case _:
            return JSONResponse({"rc": False, "message": "A server error occurred"}, status_code=500)


def query(domain: str) -> dict[str, str | bool]:
    response = httpx.post(f"{config.blocky_api_url}query", json={"query": domain, "type": "A"})

    if not (response.is_success and response.json().get("returnCode") == "NOERROR"):
        return {
            "rc": False,
            "message": f"Unable to submit the query. Please try again, or check the blocky logs.",
            "type": "is-danger",
        }

    if response.json().get("responseType") == "BLOCKED":
        return {"rc": True, "message": f"Blocky is configured to BLOCK the domain: {domain}.", "type": "is-warning"}

    return {"rc": True, "message": f"Blocky is configured to NOT BLOCK the domain: {domain}.", "type": "is-primary"}


def toggle(state: str) -> dict[str, str | bool]:
    response = httpx.get(f"{config.blocky_api_url}blocking/{state}")

    state = f"{state}d".upper()

    if not response.is_success:
        return {
            "rc": False,
            "message": "Unable to toggle blocking. Please try again, or check the blocky logs.",
            "type": "is-danger",
        }

    return {"rc": True, "message": f"Successfully toggled blocking to the {state} state", "type": "is-primary"}


def add(domain: str, redirect: bool) -> dict[str, str | bool]:
    with open(config.blocky_allowed_path, "a") as f:
        f.write(f"{domain}\n")

    response = httpx.post(f"{config.blocky_api_url}lists/refresh")

    if not response.is_success:
        return {
            "rc": False,
            "message": "Unable to add the domain to the whitelist. Please try again, or check the blocky logs.",
            "type": "is-danger",
        }

    return {
        "rc": True,
        "message": "Successfully added the domain to the whitelist!",
        "type": "is-primary",
        "redirect": redirect == "true",
    }


app = Starlette(
    routes=[
        Route("/", redirect),
        Route("/block", block),
        Route("/admin", admin),
        Route("/api", api, methods=["POST"]),
        Mount("/static", app=StaticFiles(directory=config.cwd.joinpath("static")), name="static"),
    ],
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
