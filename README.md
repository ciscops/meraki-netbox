# Meraki-Netbox

A set of python scripts and an AWS Lambda function that leverages a python module that can synchronize data between Netbox and the Meraki Dashboard.

## Requirements
### Python

Python requimrents are contained in `requirements.txt`:

`pip install -r requirements.txt`

### Netbox

You Netbox deployment must be configred with the following tags and custom fields:

Tags:
  - `discovered`

Custom Fields:
  - last_used: date
  - mac: string


## Organization

This repo contains a module (`meraki-netbox`) along with scripts that leverage the functions in that module.  It also contains an AWS Lambda function that can call different functionality from the module depending on the event that the Lambda fucntion receives.

## Scripts

`discover_meraki_clients.py`

Description: 

This sctipt iterates through the specified organization's networks looking for networks with the `discover-clients` tag.  When it finds such a network, it iterates through all of the hosts in that network.  For each host, it either adds it to `IP Addresses` if it does not exist or updates it if it does exist.  In both cases, it updates the `last_used` and `mac` fields.  When it adds a host, it also adds a `discovered` tag to keep track of the hosts that were added through the discovery process.

## Makefile targets

A number of default make targets are provided.  You can run `make help` to get a short summary of each.

Useful targets:
  * `make check`: runs `yapf` and `pylint` to check formatting and code correctness.  A `.pylintrc` is  provided with some defaults to make it a little less picky.
  * `make docs` : build documentation in HTML and Markdown.  By default, it will automatically generate API documentation for everyting in `myproject`.  Output documents can be found in `docs/build`.
  * `make clean`: cleans up generated binaries, virtualenvs, and documentation
  * `make lambda-layer`: Creates a layer for the dependancied in `requirements.txt` and pushes to AWS Lambda
  * `make lambda-deploy`: Packages the function and pushed to AWS Lambda

> Note: See [Contributing](CONTRIBUTING.md) for guideline to use when contributing to this project