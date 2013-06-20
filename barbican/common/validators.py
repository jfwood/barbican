"""
API JSON validators.
"""

import abc
import jsonschema as schema
from oslo.config import cfg
from barbican.common import exception
from barbican.openstack.common import timeutils
from barbican.common import utils


LOG = utils.getLogger(__name__)
DEFAULT_MAX_SECRET_BYTES = 10000
common_opts = [
    cfg.IntOpt('max_allowed_secret_in_bytes',
               default=DEFAULT_MAX_SECRET_BYTES),
]

CONF = cfg.CONF
CONF.register_opts(common_opts)


def secret_too_big(data):
    return len(data.encode('utf-8')) > CONF.max_allowed_secret_in_bytes


class ValidatorBase(object):
    """Base class for validators."""

    __metaclass__ = abc.ABCMeta
    name = ''

    @abc.abstractmethod
    def validate(self, json_data, parent_schema=None):
        """Validate the input JSON.

        :param json_data: JSON to validate against this class' internal schema.
        :param parent_schema: Name of the parent schema to this schema.
        :returns: dict -- JSON content, post-validation and
        :                 normalization/defaulting.
        :raises: schema.ValidationError on schema violations.

        """

    def _full_name(self, parent_schema=None):
        """
        Returns the full schema name for this validator,
        including parent name.
        """
        schema_name = self.name
        if parent_schema:
            schema_name = _("{0}' within '{1}").format(self.name,
                                                       parent_schema)
        return schema_name


class NewSecretValidator(ValidatorBase):
    """Validate a new secret."""

    def __init__(self):
        self.name = 'Secret'

        # TODO: Get the list of mime_types from the crypto plugins?
        self.schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "algorithm": {"type": "string"},
                "cypher_type": {"type": "string"},
                "bit_length": {"type": "integer", "minimum": 0},
                "expiration": {"type": "string"},
                "plain_text": {"type": "string"},
                "mime_type": {
                    "type": "string",
                    'enum': [
                        'text/plain',
                        'application/octet-stream'
                    ]
                },
            },
            "required": ["mime_type"]
        }

    def validate(self, json_data, parent_schema=None):
        schema_name = self._full_name(parent_schema)

        try:
            schema.validate(json_data, self.schema)
        except schema.ValidationError as e:
            raise exception.InvalidObject(schema=schema_name, reason=str(e))

        # Validate/normalize 'name'.
        name = json_data.get('name', '').strip()
        if not name:
            name = None
        json_data['name'] = name

        # Validate/convert 'expiration' if provided.
        expiration = self._extract_expiration(json_data, schema_name)
        if expiration:
            # Verify not already expired.
            utcnow = timeutils.utcnow()
            if expiration <= utcnow:
                raise exception.InvalidObject(schema=schema_name,
                                              reason=_("'expiration' is "
                                                       "before current time"))
        json_data['expiration'] = expiration

        # Validate/convert 'plain_text' if provided.
        if 'plain_text' in json_data:

            plain_text = json_data['plain_text']
            if secret_too_big(plain_text):
                raise exception.LimitExceeded()

            plain_text = plain_text.strip()
            if not plain_text:
                raise exception.InvalidObject(schema=schema_name,
                                              reason=_("If 'plain_text' "
                                                       "specified, must be "
                                                       "non empty"))
            json_data['plain_text'] = plain_text

        # TODO: Add validation of 'mime_type' based on loaded plugins.

        return json_data

    def _extract_expiration(self, json_data, schema_name):
        """Extracts and returns the expiration date from the JSON data."""
        expiration = None
        expiration_raw = json_data.get('expiration', None)
        if expiration_raw and expiration_raw.strip():
            try:
                expiration_tz = timeutils.parse_isotime(expiration_raw)
                expiration = timeutils.normalize_time(expiration_tz)
            except ValueError:
                LOG.exception("Problem parsing expiration date")
                raise exception.InvalidObject(schema=schema_name,
                                              reason=_("Invalid date "
                                                       "for 'expiration'"))

        return expiration


class NewOrderValidator(ValidatorBase):
    """Validate a new order."""

    def __init__(self):
        self.name = 'Order'
        self.schema = {
            "type": "object",
            "properties": {
            },
        }
        self.secret_validator = NewSecretValidator()

    def validate(self, json_data, parent_schema=None):
        schema_name = self._full_name(parent_schema)

        try:
            schema.validate(json_data, self.schema)
        except schema.ValidationError as e:
            raise exception.InvalidObject(schema=schema_name, reason=str(e))

        # If secret group is provided, validate it now.
        if 'secret' in json_data:
            secret = json_data['secret']
            self.secret_validator.validate(secret, parent_schema=self.name)
            if 'plain_text' in secret:
                raise exception.InvalidObject(schema=schema_name,
                                              reason=_("'plain_text' not "
                                                       "allowed for secret "
                                                       "generation"))
        else:
            raise exception.InvalidObject(schema=schema_name,
                                          reason=_("'secret' attributes "
                                                   "are required"))

        # Validation secret generation related fields.
        # TODO: Invoke the crypto plugin for this purpose
        if secret.get('algorithm') != 'aes':
            raise exception.NotSupported(schema=schema_name,
                                         reason=_("The only 'algorithm' "
                                                   "selection supported now "
                                                   "is 'aes'"))
        if secret.get('cypher_type') != 'cbc':
            raise exception.NotSupported(schema=schema_name,
                                         reason=_("The only 'cypher_type' "
                                                   "selection supported now "
                                                   "is 'cbc'"))
        bit_length = int(secret.get('bit_length', 0))
        if not bit_length in (128, 192, 256):
            raise exception.NotSupported(schema=schema_name,
                                         reason=_("The only 'bit_length' "
                                                   "selections supported now "
                                                   "are one of 128, 192, "
                                                   "or 256"))

        return json_data
