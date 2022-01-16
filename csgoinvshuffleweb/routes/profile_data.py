import datetime

import flask_praetorian
import requests
from csgoinvshuffle.inventory import InventoryIsPrivateException, get_inventory
from csgoinvshuffle.item import Item
from flask import Blueprint, abort, jsonify, request
from pydantic import BaseModel
from spectree import Response

from csgoinvshuffleweb.extensions.cache import cache
from csgoinvshuffleweb.extensions.validation import api_validator
from csgoinvshuffleweb.utils import get_profile_data

profile_data = Blueprint("profile_data", __name__)


class ProfilePicAnswer(BaseModel):
    link: str


@profile_data.get("/profile_picture")
@flask_praetorian.auth_required
@api_validator.validate(
    resp=Response(HTTP_200=ProfilePicAnswer), tags=("Profile Data",)
)
def get_pp_link():
    """Get the link to the authenticated user's steam profile picture"""
    steam_id = flask_praetorian.current_user_id()
    if (cached := cache.get(f"pp_{steam_id}")) and not request.args.get("no_cache", 0):

        return cached
    for child in get_profile_data():
        if child.tag == "avatarIcon":
            ret = child.text
    resp = (
        jsonify(link=ret),
        200,
    )
    cache.set(f"pp_{steam_id}", resp, timeout=1800)
    return resp


@profile_data.get("/inventory")
@flask_praetorian.auth_required
@api_validator.validate(tags=("Profile Data",))
def get_inv():
    """Get the CS:GO of the authenticated user"""
    steam_id = flask_praetorian.current_user_id()
    if (cached := cache.get(f"inventory_{steam_id}")) and not request.args.get(
        "no_cache", 0
    ):
        return cached
    try:
        if datetime.timedelta(minutes=10) > (
            re_timeout := (
                datetime.datetime.now()
                - (
                    cache.get(f"timeout_{steam_id}")
                    or (datetime.datetime.now() - datetime.timedelta(minutes=11))
                )
            )
        ):
            return f"{600 - re_timeout.seconds}", 429

        def filter_equippable(item: Item):
            return item.equippable

        resp = jsonify(list(filter(filter_equippable, get_inventory(steam_id))))
        cache.set(f"inventory_{steam_id}", resp, timeout=86_400)
        cache.set(f"timeout_{steam_id}", datetime.datetime.now(), timeout=1200)
        return resp
    except InventoryIsPrivateException:
        abort(403)
    except requests.HTTPError:
        cache.set(f"timeout_{steam_id}", datetime.datetime.now(), timeout=1200)
        return "600", 429
