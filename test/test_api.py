#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

import pytest
import json

from celly import *
from ponytest import *
from uuid import uuid4


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
    with pytest.raises(PathError):
        celly.host[uuid].desired


def test_non_existent_host_nics():
    uuid = '88888888-8888-8888-8888-888888888888'
    with pytest.raises(PathError):
        nics = celly.host[uuid].nic.uri
        celly.request(nics)


def test_post_nonsense_host():
    with pytest.raises(DataError) as ex:
        celly.host.post(u'"Wrong" data, that should break it.\n' \
                        u'Příliš žluťoučký kůň úpěl ďábelské ódy.')


def test_post_nonsense_dict_host():
    with pytest.raises(DataError) as ex:
        celly.host.post({
            '0': 'Wrong data, that should break it.',
            '1': u'Příliš žluťoučký kůň úpěl ďábelské ódy.'
        })


def test_post_host():
    uuid = str(uuid4())
    data = {
        'desired': {
            'uuid': uuid,
            'info': 'Testing Host',
            'state': 'present',
            'fencing': {},
        }
    }

    assert celly.host.post(data)

    cleanup.append(lambda: celly.host[uuid].delete())

    assert superset(celly.host[uuid].desired, data['desired'])


def test_post_host_with_nics():
    host_uuid = str(uuid4())
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

    assert celly.host.post(data)

    cleanup.append(lambda: celly.host[host_uuid].delete())

    assert superset(celly.host[host_uuid].desired, data['desired'])
    assert superset(celly.host[host_uuid].nic[nic_hwaddr].desired,
                    data['children']['nic'][nic_hwaddr]['desired'])


def test_post_host_to_entity():
    existing_uuid = 'f4f69922-5409-410d-b9b0-198c9389650f'
    uuid = str(uuid4())

    data = {
        'desired': {
            'uuid': uuid,
            'state': 'present',
            'info': 'Entity that should not be posted',
            'fencing': {},
        }
    }

    uri = celly.host[existing_uuid].uri

    with pytest.raises(MethodError):
        celly.request(uri, 'POST', json.dumps(data))


def test_delete_host():
    uuid = '6a01061e-82b0-4e21-bd61-753462d47ccd'

    if uuid not in celly.host:
        pytest.skip('host %r does not exist, cannot delete' % (uuid,))

    assert celly.request(celly.host[uuid].uri, 'DELETE') == {'uuids': {}}


def simple_negative_test(uri, expected_error, method):
    with pytest.raises(expected_error):
        celly.request(uri, method)


def test_delete_host_nic_collection():
    uri = celly.host['f4f69922-5409-410d-b9b0-198c9389650f'].nic.uri
    simple_negative_test(uri, MethodError, 'DELETE')


def test_delete_non_existant_host():
    uri = celly.host['88888888-8888-9999-0000-888888888888'].uri
    simple_negative_test(uri, PathError, 'DELETE')


def test_delete_root():
    simple_negative_test(celly.uri + '/', MethodError, 'DELETE')


def test_delete_host_attribute():
    uri = celly.host['f4f69922-5409-410d-b9b0-198c9389650f'].uri + '/state'
    simple_negative_test(uri, PathError, 'DELETE')


def test_post_bond():
    existing_host = 'f4f69922-5409-410d-b9b0-198c9389650f'
    bond_uuid = 'new_bond'
    bond_data = {
            'desired': {
                'uuid': bond_uuid,
                'mode': 'active-backup'
            },
            'children': {
                'nic': {
                    '11:22:22:22:22:22': {
                        'desired': {
                            'hwaddr': '11:22:22:22:22:22',
                            'host': existing_host
                        }
                    },
                    '44:22:22:22:22:22': {
                        'desired': {
                            'hwaddr': '44:22:22:22:22:22',
                            'host': existing_host
                        }
                    }
                }
            }
        }

    # Post the data and take placeholder for verification
    posted = celly.host[existing_host].bond.post(bond_data)
    bond_uuid = posted['uuids'][bond_uuid]

    # Verify bond we just inserted.
    new_bond = celly.host[existing_host].bond[bond_uuid]
    bond_data['desired']['uuid'] = bond_uuid
    assert superset(new_bond.desired, bond_data['desired'])

    # Verify its nics as well.
    nic_muster = [x['desired'] for x in bond_data['children']['nic'].values()]
    new_nics = [item.desired for item in new_bond.nic.list]
    assert superset(new_nics, nic_muster)

    # Cleanup the mess.
    to_delete = [
        lambda: celly.host[existing_host].nic['44:22:22:22:22:22'].delete(),
        lambda: celly.host[existing_host].nic['11:22:22:22:22:22'].delete(),
        lambda: celly.host[existing_host].bond[bond_uuid].delete()
    ]

    for item in to_delete:
        cleanup.append(item)


@pytest.mark.xfail(reason='We do not support non-immediate parents yet')
def test_negative_post_bond():
    existing_host = 'f4f69922-5409-410d-b9b0-198c9389650f'
    bond_uuid = 'new_bond'
    bond_data = {
            'desired': {
                'uuid': bond_uuid,
                'mode': 'active-backup'
            },
            'children': {
                'nic': {
                    '11:22:22:22:22:22': {
                        'desired': {
                            'hwaddr': '11:22:22:22:22:22',
                        }
                    },
                    '44:22:22:22:22:22': {
                        'desired': {
                            'hwaddr': '44:22:22:22:22:22',
                        }
                    }
                }
            }
        }
    assert celly.host[existing_host].bond.post(bond_data)

def test_patch_host():
    existing_host = 'f4f69922-5409-410d-b9b0-198c9389650f'

    patch = [{'op': 'add',
              'path': '/children/bond/%autoid0',
              'value': {'children': {'roles': {'%autoid1': {'desired': {'address': None,
                                                                        'role': 'storage',
                                                                        'uuid': '%autoid1'}}}},
                        'desired': {'mode': 'active-backup', 'uuid': '%autoid0'}}},
             {'op': 'add',
              'path': '/children/bond/%autoid0/children/role/%autoid1',
              'value': {'desired': {'address': None,
                                    'role': 'storage',
                                    'uuid': '%autoid1'}}},
             {'op': 'merge',
              'path': '/children/bond/3b1c5852-d1fe-438c-a3fc-16c9b5b92d75',
              'value': {'children': {'nics': {'1a:2b:3c:4d:5e:6f': {'desired': {'hwaddr': '1a:2b:3c:4d:5e:6f'}}},
                                     'roles': {'%autoid2': {'desired': {'address': None,
                                                                        'role': 'management',
                                                                        'uuid': '%autoid2'}},
                                               '6518215b-d7b8-4c91-84b2-512a8fb82ad2': {'desired': {'bond': '3b1c5852-d1fe-438c-a3fc-16c9b5b92d75',
                                                                                                    'role': 'core',
                                                                                                    'uuid': '6518215b-d7b8-4c91-84b2-512a8fb82ad2',
                                                                                                    'vlan_id': 1}}}},
                        'desired': {'mode': '802.3ad', 'xmit_hash_policy':'layer2+3'}}},
             {'op': 'add',
              'path': '/children/bond/3b1c5852-d1fe-438c-a3fc-16c9b5b92d75/children/role/%autoid2',
              'value': {'desired': {'address': None,
                                    'role': 'management',
                                    'uuid': '%autoid2'}}},
             {'op': 'merge',
              'path': '/children/nic/1a:2b:3c:4d:5e:6f/desired',
              'value': {'bond': '3b1c5852-d1fe-438c-a3fc-16c9b5b92d75'}}]


    assert celly.host[existing_host].patch(patch)





def test_cleanup():
    for job in cleanup:
        job()


# vim:set sw=4 ts=4 et:
