# Copyright (c) 2013 Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Shared business logic.
"""

from barbican.model.models import (Tenant, Secret, TenantSecret,
                                   EncryptedDatum, Order, States)
from barbican.model.repositories import (TenantRepo, SecretRepo,
                                         OrderRepo, TenantSecretRepo,
                                         EncryptedDatumRepo)
from barbican.crypto.fields import encrypt, decrypt
from barbican.openstack.common import timeutils
from barbican.openstack.common.gettextutils import _
from barbican.openstack.common import jsonutils as json
from barbican.queue import get_queue_api
from barbican.common import utils

LOG = utils.getLogger(__name__)


def ensure_expiration(data):
    expiration = data.get('expiration', None)
    if not expiration:
        expiration = timeutils.utcnow()
    data['expiration'] = expiration
    return expiration


def create_secret_single_type(data, tenant_id, tenant_repo,
                              secret_repo, tenant_secret_repo,
                              datum_repo):
    # Create a Secret and a single EncryptedDatum for that Secret. Create
    #   a Tenant if one doesn't already exist.
    tenant = tenant_repo.get(tenant_id, suppress_exception=True)
    if not tenant:
        LOG.debug('Creating tenant for {0}'.format(tenant_id))
        tenant = Tenant()
        tenant.keystone_id = tenant_id
        tenant.status = States.ACTIVE
        tenant_repo.create_from(tenant)

    # TODO: What if any criteria to restrict new secrets vs existing ones?
    # Verify secret doesn't already exist.
    #
    #name = data['name']
    #LOG.debug('Secret name is {0}'.format(name))
    #secret = secret_repo.find_by_name(name=name,
    #                                       suppress_exception=True)
    #if secret:
    #    abort(falcon.HTTP_400, 'Secret with name {0} '
    #                           'already exists'.format(name))

    # Encrypt fields.
    encrypt(data)
    LOG.debug('Post-encrypted fields...{0}'.format(data))
    secret_value = data['cypher_text']
    LOG.debug('Encrypted secret is {0}'.format(secret_value))

    # Create Secret entity.
    new_secret = Secret()
    new_secret.name = data['name']
    new_secret.expiration = ensure_expiration(data)
    new_secret.status = States.ACTIVE
    secret_repo.create_from(new_secret)

    # Create Tenant/Secret entity.
    new_assoc = TenantSecret()
    new_assoc.tenant_id = tenant.id
    new_assoc.secret_id = new_secret.id
    new_assoc.role = "admin"
    new_assoc.status = States.ACTIVE
    tenant_secret_repo.create_from(new_assoc)

    # Create EncryptedDatum entity.
    new_datum = EncryptedDatum()
    new_datum.secret_id = new_secret.id
    new_datum.mime_type = data['mime_type']
    new_datum.cypher_text = secret_value
    new_datum.kek_metadata = data['kek_metadata']
    new_datum.status = States.ACTIVE
    datum_repo.create_from(new_datum)
    
    return new_secret


# Maps mime-types used to specify secret data formats to the types that can
#   be requested for secrets via GET calls.
CTYPES_PLAIN = {'default': 'text/plain'}
CTYPES_AES = {'default': 'application/aes'}
CTYPES_MAPPINGS = {'text/plain': CTYPES_PLAIN,
                   'application/aes': CTYPES_AES}


def augment_fields_with_content_types(secret):
    # Based on the data associated with the secret, generate a list of content
    #   types.
    
    fields = secret.to_dict_fields()

    if not secret.encrypted_data:
        return fields

    # TODO: How deal with merging more than one datum instance?
    for datum in secret.encrypted_data:
        if datum.mime_type in CTYPES_MAPPINGS:
            fields.update({'content_types': CTYPES_MAPPINGS[datum.mime_type]})

    print " zzzzz ",fields

    return fields