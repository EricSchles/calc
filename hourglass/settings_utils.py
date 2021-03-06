import os
import sys
import json
from typing import List, Optional

Environ = os._Environ


def load_cups_from_vcap_services(name: str='calc-env',
                                 env: Environ=os.environ) -> None:
    '''
    Detects if VCAP_SERVICES exists in the environment; if so, parses
    it and imports all the credentials from the given custom
    user-provided service (CUPS) as strings into the environment.

    For more details on CUPS, see:

    https://docs.cloudfoundry.org/devguide/services/user-provided.html
    '''

    if 'VCAP_SERVICES' not in env:
        return

    vcap = json.loads(env['VCAP_SERVICES'])

    for entry in vcap.get('user-provided', []):
        if entry['name'] == name:
            for key, value in entry['credentials'].items():
                env[key] = value


def get_whitelisted_ips(env: Environ=os.environ) -> Optional[List[str]]:
    '''
    Detects if WHITELISTED_IPS is in the environment; if not,
    returns None. if so, parses WHITELISTED_IPS as a comma-separated
    string and returns a list of values.
    '''
    if 'WHITELISTED_IPS' not in env:
        return None

    return [s.strip() for s in env['WHITELISTED_IPS'].split(',')]


def load_redis_url_from_vcap_services(name: str,
                                      env: Environ=os.environ) -> None:
    '''
    Detects if a redis28 service instance with the given name
    is present in VCAP_SERVICES.
    If it is, then it creates a URL for the instance and sets env['REDIS_URL']
    to that URL. If not, it just returns and does nothing.
    '''

    if 'VCAP_SERVICES' not in env:
        return

    vcap = json.loads(env['VCAP_SERVICES'])

    for entry in vcap.get('redis28', []):
        if entry['name'] == name:
            creds = entry['credentials']
            url = 'redis://:{password}@{hostname}:{port}'.format(
                password=creds['password'],
                hostname=creds['hostname'],
                port=creds['port']
            )
            env['REDIS_URL'] = url
            return


def is_running_tests(argv: List[str]=sys.argv) -> bool:
    '''
    Returns whether or not we're running tests.
    '''

    basename = os.path.basename(argv[0])
    first_arg = argv[1] if len(argv) > 1 else None

    if basename == 'manage.py' and first_arg == 'test':
        return True
    if basename == 'py.test':
        return True

    return False
