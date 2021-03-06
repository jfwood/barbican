# Barbican
Barbican is a ReST API designed for the secure storage, provisioning and management of secrets. It is aimed at being useful for all environments, including large ephemeral Clouds. The project is supported by [Rackspace Hosting](http://www.rackspace.com).

Barbican is part of a set of applications that make up the CloudKeep ecosystem. The other systems are:

* [Postern](https://github.com/cloudkeep/postern) - Go based agent that provides access to secrets from the Barbican API.
* [Palisade](https://github.com/cloudkeep/palisade) - AngularJS based web ui for the Barbican API.
* [Python-barbicanclient](https://github.com/cloudkeep/python-barbicanclient) - A convenient Python-based library to interact with the Barbican API.
* [Keep](https://github.com/cloudkeep/keep) - A python-based command line client for the Barbican API.

Additional documentation can be found on the [Github Wiki](https://github.com/cloudkeep/barbican/wiki). For questions, comments or concerns, hop on the OpenStack dev mailing list at `openstack-dev@lists.openstack.org` and let us know what you think, just add `[openstack-dev][barbican]` to the subject. You can also join our Freenode IRC at `#openstack-cloudkeep`.


## Getting Started

* [Please visit our wiki home page for details](https://github.com/cloudkeep/barbican/wiki)


## Why Should You Use Barbican?
The current state of key management is atrocious. While Windows does have some decent options through the use of the Data Protection API (DPAPI) and Active Directory, Linux lacks a cohesive story around how to manage keys for applicaiton use. 

Barbican was designed to solve this problem. The system was motivated by internal Rackspace needs, requirements from [OpenStack](http://www.openstack.org/) and a realization that the current state of the art could use some help.

Barbican will handle many types of secrets, including:

* **Symmetric Keys** - Used to perform reversible encryption of data at rest, typically using the AES algorithm set. This type of key is required to enable features like [encrypted Swift containers and Cinder volumes](http://www.openstack.org/software/openstack-storage/), [encrypted Cloud Backups](http://www.rackspace.com/cloud/backup/), etc.
* **Asymmetric Keys** - Asymmetric key pairs (sometimes referred to as [public / private keys](http://en.wikipedia.org/wiki/Public-key_cryptography)) are used in many scenarios where communication between untrusted parties is desired. The most common case is with SSL/TLS certificates, but also is used in solutions like SSH keys, S/MIME (mail) encryption and digital signatures.
* **Raw Secrets** - Barbican stores secrets as a base64 encoded block of data (encrypted, naturally). Clients can use the API to store any secrets in any format they desire. The [Postern](https://github.com/cloudkeep/postern) agent is capable of presenting these secrets in various formats to ease integration.

For the symmetric and asymmetric key types, Barbican supports full lifecycle management including provisioning, expiration, reporting, etc. A plugin system allows for multiple certificate authority support (including public and private CAs).

## Design Goals

1. Provide a central secret-store capable of distributing secret / keying material to all types of deployments including ephemeral Cloud instances.
2. Support reasonable compliance regimes through reporting and auditability.
3. Application adoption costs should be minimal or non-existent.
4. Build a community and ecosystem by being open-source and extensible.
5. Improve security through sane defaults and centralized management of [policies for all secrets](https://github.com/cloudkeep/barbican/wiki/Policies).
6. Out of band communication mechanism to notify and protect sensitive assets.

