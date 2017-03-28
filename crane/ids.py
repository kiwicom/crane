import re
from . import utils


def _is_id(string):
    return string and re.match(r'^[0-9][a-z]{1,2}[0-9]+$', string) is not None


def _stack_name_to_id(url, env, access, secret, name):
    response = utils.rancher_api_get(f'{url}/v1/projects/{env}/environments?name={name}', access, secret)

    return next(stack['id'].replace('1e', '1st') for stack in response['data'])


def _service_name_to_id(url, env, access, secret, name, stack):
    response = utils.rancher_api_get(f'{url}/v1/projects/{env}/services?name={name}&stackId={stack}', access, secret)

    return next(service['id'] for service in response['data'])


def names_to_ids(rancher_url, env, stack, service, access, secret):
    if not _is_id(stack):
        stack = _stack_name_to_id(rancher_url, env, access, secret, stack)

    if not _is_id(service):
        service = _service_name_to_id(rancher_url, env, access, secret, service, stack)

    return stack, service