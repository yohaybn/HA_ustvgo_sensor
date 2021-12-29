"""Support for ustvgo."""
import asyncio
import datetime
from datetime import datetime, timedelta
import logging
import socket
import urllib
import sys
from xml.parsers.expat import ExpatError
import difflib

import aiohttp
import async_timeout
import voluptuous as vol
import xmltodict

from homeassistant.components.sensor import ENTITY_ID_FORMAT, PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME,
    CONF_RESOURCE,
    CONF_RESOURCE_TEMPLATE,
    CONF_SCAN_INTERVAL,

)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

DEFAULT_METHOD = "GET"
DEFAULT_NAME = "ustvgo"
DEFAULT_VERIFY_SSL = True
DEFAULT_FORCE_UPDATE = False
DEFAULT_TIMEOUT = 10
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)


CONF_ATTR = "attribute"
CONF_SELECT = "select"
CONF_INDEX = "index"


METHODS = ["POST", "GET", "PUT"]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period
    }
)

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SELECT): cv.template,
        vol.Optional(CONF_ATTR): cv.string,
        vol.Optional(CONF_INDEX, default=0): cv.positive_int,
        vol.Required(CONF_NAME): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Multiscrape sensor."""
    name = config.get(CONF_NAME)
    scan_interval = config.get(CONF_SCAN_INTERVAL)
    session = async_get_clientsession(hass)
    values = {}
    async def async_update_data():
        """Fetch data from API endpoint.
        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """       
        counter=0
        try:
            async with async_timeout.timeout(1000):
                with open('/config/custom_components/ustvgo/ustvgo_channel_info.txt') as file:
                    for line in file:
                        line = line.strip()
                        if not line or line.startswith('~~'):
                            continue
                        line = line.split('|')
                        name = line[0].strip()
                        code = line[1].strip()
                        logo = line[2].strip()
                        _ent={}
                        data = {'stream': code}
                    
                        async with session.post('https://ustvgo.tv/data.php', data=data) as response:
                            m3u = await response.text()
                            _ent["m3u"] = m3u
                            _ent["tvg-id"] = code
                            _ent["tvg-logo"] = logo
                            _ent["name"] = f"ustvgo_{name}"
                            values[name]= _ent
                            _LOGGER.info("collecting sensor: %s",name)
            return values
        except Exception:
            raise UpdateFailed
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=config.get(CONF_NAME),
        update_method=async_update_data,
        update_interval=scan_interval,
    )
    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()
    entities = []
    for sensor in values:
        entities.append(UstvgoSensor(
                            hass,
                            coordinator,
                            sensor,
                            sensor,
                            True,)
        )
    async_add_entities(entities, True)
class UpdateFailed(Exception):
    """Raised when an update has failed."""


class UstvgoSensor(Entity):
    """Implementation of the Multiscrape sensor."""

    def __init__(
            self,
            hass,
            coordinator,
            key,
            name,
            force_update
    ):
        """Initialize the sensor."""
        self._hass = hass
        self._coordinator = coordinator
        self._key = key
        self._name = name
        self._state = None
        self._force_update = force_update
        self._attributes = {}
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, key, hass=hass
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def available(self):
        """Return if entity is available."""
        return self._coordinator.last_update_success

    @property
    def state(self):
        """Return the state of the device."""
       # _LOGGER.error("state -info: %s",self._coordinator.data)
       # _LOGGER.error("state -_key: %s",self._key)
        if self._coordinator.data[self._key] is None:
            return "Unavilable"
        return self._coordinator.data[self._key]['name']

    @property
    def force_update(self):
        """Force update."""
        return self._force_update

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self._coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )

    async def async_update(self):
        """Update the entity. Only used by the generic entity update service."""
        await self._coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._coordinator.data[self._key] 
