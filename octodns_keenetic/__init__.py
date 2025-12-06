import hashlib
import pprint
from http import HTTPStatus
from logging import getLogger

import requests

from octodns.provider import ProviderException
from octodns.provider.base import BaseProvider
from octodns.record import Record

__version__ = __VERSION__ = "0.1.0"


def split_domain(domain):
    if "." in domain:
        return domain.split(".", maxsplit=1)
    return "", domain


class KeeneticProvider(BaseProvider):
    SUPPORTS_GEO = False
    SUPPORTS_DYNAMIC = False

    SUPPORTS = set(("A"))

    def __init__(
        self,
        id,
        host,
        login,
        password,
        ttl=300,
        replace=False,
        *args,
        **kwargs,
    ):
        self.log = getLogger(f"KeeneticProvider[{id}]")
        self.log.debug(
            "__init__: id=%s, host=%s, login=%s, ttl=%s, replace=%s",
            id,
            host,
            login,
            ttl,
            replace,
        )

        super().__init__(id, *args, **kwargs)

        self.ttl = ttl
        self.replace = replace

        self.api = KeeneticAPI(host, login, password)

        self._zones = None

    @property
    def zones(self):
        if self._zones:
            return self._zones

        hosts = self.api.get("ip/host")

        all_zones = {}

        for host in hosts:
            _, zone = split_domain(host["domain"])
            all_zones[zone] = True

        zones = {}

        for host in hosts:
            if host["domain"] in all_zones:
                name, zone = "", host["domain"]
            else:
                name, zone = split_domain(host["domain"])

            dns_zone = zone + "."

            zones[dns_zone] = zones.get(dns_zone, {})
            zones[dns_zone][name] = zones[dns_zone].get(name, [])

            zones[dns_zone][name].append(host["address"])

        self._zones = zones

        self.log.debug("zones: result=...\n%s", pprint.pformat(zones))
        return zones

    def list_zones(self):
        zones = sorted(self.zones.keys())

        self.log.debug("list_zones: result=%s", zones)
        return zones

    def populate(self, zone, target=False, lenient=False):
        self.log.debug(
            "populate: zone=%s, target=%s, lenient=%s",
            zone.name,
            target,
            lenient,
        )

        exist = False
        before = len(zone.records)

        if zone.name in self.zones:
            exist = True
            for name in self.zones[zone.name]:
                rec = Record.new(
                    zone,
                    name,
                    {
                        "type": "A",
                        "values": self.zones[zone.name][name],
                        "ttl": self.ttl,
                    },
                    source=self,
                    lenient=lenient,
                )
                zone.add_record(
                    rec,
                    lenient=lenient,
                    replace=self.replace,
                )

        self.log.debug(
            "populare: result=%s, records=%s", exist, len(zone.records) - before
        )

        return exist

    def _apply(self, plan):
        zone, changes = plan.desired, plan.changes

        self.log.debug("_apply: zone=%s, changes=%s", zone.name, len(changes))

        for change in changes:
            self.log.debug(
                "_apply: change=...\n%s", pprint.pformat(change.data)
            )

            if change.data["name"] == "*":
                continue

            if change.data["type"] in ["delete", "update"]:
                self.api.delete(
                    "ip/host",
                    {
                        "domain": change.data["name"]
                        + "."
                        + zone.name.removesuffix(".")
                    },
                )

            if change.data["type"] in ["create", "update"]:
                values = (
                    change.data["new"]["values"]
                    if "values" in change.data["new"]
                    else [change.data["new"]["value"]]
                )

                for value in values:
                    self.api.post(
                        "ip/host",
                        {
                            "domain": change.data["name"]
                            + "."
                            + zone.name.removesuffix("."),
                            "address": value,
                        },
                    )


class KeeneticAPI:
    def __init__(self, host, login, password):
        self.sess = requests.session()

        self.host = host

        self.login = login
        self.password = password

    def _encrypt_password(self):
        arg_hash = hashlib.md5(
            f"{self.login}:{self.realm}:{self.password}".encode("utf-8")
        ).hexdigest()

        return hashlib.sha256(
            (self.token + arg_hash).encode("utf8")
        ).hexdigest()

    def _check_need_auth(self):
        res = self.sess.get(f"http://{self.host}/auth")

        if res.status_code == HTTPStatus.OK:
            return False

        if HTTPStatus.UNAUTHORIZED:
            self.realm = res.headers.get("X-NDM-Realm")
            self.token = res.headers.get("X-NDM-Challenge")

            return True

        raise ProviderException(f"Unexpected status code: {res.status_code}")

    def auth(self):
        if not self._check_need_auth():
            return False

        res = self.sess.post(
            f"http://{self.host}/auth",
            json={"login": self.login, "password": self._encrypt_password()},
        )

        if res.status_code == HTTPStatus.OK:
            return True

        raise ProviderException(f"Unexpected status code: {res.status_code}")

    def get(self, method, params={}):
        res = self.sess.get(f"http://{self.host}/rci/{method}", params=params)

        if res.status_code == HTTPStatus.UNAUTHORIZED:
            self.auth()
            res = self.sess.get(
                f"http://{self.host}/rci/{method}", params=params
            )

        if res.status_code == HTTPStatus.OK:
            return res.json()

        raise ProviderException(f"Unexpected status code: {res.status_code}")

    def post(self, method, json={}):
        res = self.sess.post(f"http://{self.host}/rci/{method}", json=json)

        if res.status_code == HTTPStatus.UNAUTHORIZED:
            self.auth()
            res = self.sess.post(f"http://{self.host}/rci/{method}", json=json)

        if res.status_code == HTTPStatus.OK:
            return res.json()

        raise ProviderException(f"Unexpected status code: {res.status_code}")

    def delete(self, method, params={}):
        res = self.sess.delete(
            f"http://{self.host}/rci/{method}", params=params
        )

        if res.status_code == HTTPStatus.UNAUTHORIZED:
            self.auth()
            res = self.sess.delete(
                f"http://{self.host}/rci/{method}", params=params
            )

        if res.status_code == HTTPStatus.OK:
            return res.json()

        raise ProviderException(f"Unexpected status code: {res.status_code}")
