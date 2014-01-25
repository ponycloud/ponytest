#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

import pytest
import json

from time import sleep

from ponycloud.celly import Celly
from ponycloud.common.schema import schema
from ponycloud.celly import *

from ponytest import *


celly = Celly(headers={
    'Authorization': 'Basic bHVuYUBwb25pZXMuY29tOmNva29saXZ=',
})

cleanup = []


def test_host():
    """
    Test existence of a well-known host.
    """

    uuid = 'f4f69922-5409-410d-b9b0-198c9389650f'
    assert superset(celly.host[uuid].desired, {
        'fencing': {},
        'state': 'present',
        'uuid': uuid,
    })


def test_host_nic():
    """
    Test some well-known NICs of a well-known host.
    """

    uuid = 'f4f69922-5409-410d-b9b0-198c9389650f'
    nics = [nic.desired for nic in celly.host[uuid].nic]

    assert superset(nics, [
        {
            'host': 'f4f69922-5409-410d-b9b0-198c9389650f',
            'hwaddr': '1a:2b:3c:4d:5e:6f',
        },
        {
            'host': 'f4f69922-5409-410d-b9b0-198c9389650f',
            'hwaddr': 'aa:bb:cc:dd:ee:ff',
        },
        {
            'host': 'f4f69922-5409-410d-b9b0-198c9389650f',
            'hwaddr': '66:55:44:33:22:11',
        },
        {
            'host': 'f4f69922-5409-410d-b9b0-198c9389650f',
            'hwaddr': '11:22:33:44:55:66',
        },
    ])


def test_non_existent_host():
    uuid = '88888888-8888-8888-8888-888888888888'
    with pytest.raises(RequestError) as ex:
        celly.host[uuid].desired
    assert isinstance(ex.value, NotFoundError)


def test_non_existent_host_nics():
    uuid = '88888888-8888-8888-8888-888888888888'
    with pytest.raises(RequestError) as ex:
        nics = celly.host[uuid].nic.uri
        celly.request(nics)
    assert isinstance(ex.value, NotFoundError)


def test_post_nonsense_host():
    with pytest.raises(RequestError) as ex:
        celly.host.post(u'"Wrong" data, that should break it.\n' \
                        u'Příliš žluťoučký kůň úpěl ďábelské ódy.')
    assert isinstance(ex.value, BadRequestError)


def test_post_nonsense_dict_host():
    with pytest.raises(RequestError) as ex:
        celly.host.post({
            '0': 'Wrong data, that should break it.',
            '1': u'Příliš žluťoučký kůň úpěl ďábelské ódy.'
        })
    assert isinstance(ex.value, BadRequestError)


def test_post_host():
    uuid = 'this_host_does_not_exist_yet'
    data = {
        'desired': {
            'uuid': uuid,
            'info': 'Testing Host',
            'state': 'present',
            'fencing': {},
        }
    }

    result = celly.host.post(data)
    uuid = data['desired']['uuid'] = result['uuids'][uuid]

    cleanup.append(lambda: celly.host[uuid].delete())

    sleep(1)
    assert superset(celly.host[uuid].desired, data['desired'])


def test_post_host_with_nics():
    host_uuid = 'this_host_does_not_exist_yet'
    nic_hwaddr = '22:22:22:22:22:22'

    data = {
        'desired': {
            'uuid': host_uuid,
            'info': 'Testing Host with nic',
            'state': 'present',
            'fencing': {},
        },
        'children': {
            'nic': {
                nic_hwaddr: {
                    'desired': {
                        'hwaddr': nic_hwaddr,
                        'host': host_uuid,
                    }
                }
            }
        }
    }

    result = celly.host.post(data)
    host_uuid = data['desired']['uuid'] = result['uuids'][host_uuid]
    data['children']['nic'][nic_hwaddr]['desired']['host'] = host_uuid

    cleanup.append(lambda: celly.host[host_uuid].delete())

    sleep(1)
    assert superset(celly.host[host_uuid].desired, data['desired'])
    assert superset(celly.host[host_uuid].nic[nic_hwaddr].desired,
                    data['children']['nic'][nic_hwaddr]['desired'])


def test_post_host_to_entity():
    existing_uuid = 'f4f69922-5409-410d-b9b0-198c9389650f'
    uuid = 'this_host_does_not_exist_yet'

    data = {
        'desired': {
            'uuid': uuid,
            'state': 'present',
            'info': 'Entity that should not be posted',
            'fencing': {},
        }
    }

    uri = celly.host[existing_uuid].uri

    with pytest.raises(RequestError) as ex:
        celly.request(uri, 'POST', json.dumps(data))

    assert isinstance(ex.value, MethodNotAllowedError)


def test_delete_host():
    uuid = '6a01061e-82b0-4e21-bd61-753462d47ccd'
    muster = {'uuids': {}}
    value = celly.request(celly.host[uuid].uri, 'DELETE')
    assert value == muster


def simple_negative_test(uri, expected_error, method):
    with pytest.raises(RequestError) as ex:
        celly.request(uri, method)
    assert isinstance(ex.value, expected_error)


def test_delete_host_nic_collection():
    uri = celly.host['f4f69922-5409-410d-b9b0-198c9389650f'].nic.uri
    simple_negative_test(uri, MethodNotAllowedError, 'DELETE')


def test_delete_non_existant_host():
    uri = celly.host['88888888-8888-9999-0000-888888888888'].uri
    simple_negative_test(uri, NotFoundError, 'DELETE')


def test_delete_root():
    simple_negative_test(celly.uri + '/', MethodNotAllowedError, 'DELETE')


def test_delete_host_attribute():
    uri = celly.host['f4f69922-5409-410d-b9b0-198c9389650f'].uri + '/state'
    simple_negative_test(uri, NotFoundError, 'DELETE')


def test_cleanup():
    for job in cleanup:
        job()


# vim:set sw=4 ts=4 et:
