# Prolegomenous Setup

This is the initial setup client for building a *root* structure in a Google
Cloud organization. To get started, please see the
[docs folder](docs/README.md).

This client is in an early development stage.

## Testing

Test this code with **pylint**.

```bash
pylint src/psetup
```

## Packaging

Build this package in a **virtualenv** using pip.
For more information about virtualenv, please look for the [virtualenv website](https://virtualenv.pypa.io/en/latest/).

```bash
virtualenv env-name
source env-name/bin/activate
env-name/bin/python -m build
```

## Installation

Install the client using pip.

```bash
env-name/bin/pip install dist/psetup-0.2.0-py3-none-any.whl
```

## Third Party Libraries and Dependencies

The following libraries will be installed when you install the client library:

* [google-api-python-client](https://github.com/googleapis/google-api-python-client/)
* [google-cloud-resource-manager](https://github.com/googleapis/google-cloud-python/tree/main/packages/google-cloud-resource-manager)
* [google-cloud-billing](https://github.com/googleapis/google-cloud-python/tree/main/packages/google-cloud-billing)
* [google-cloud-service-usage](https://github.com/googleapis/google-cloud-python/tree/main/packages/google-cloud-service-usage)
* [grpc-google-iam-v1](https://github.com/googleapis/python-grpc-google-iam-v1)
* [PyYAML](https://github.com/yaml/pyyaml)
* [terrasnek](https://github.com/dahlke/terrasnek)
