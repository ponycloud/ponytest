#!/usr/bin/python -tt

__all__ = ['superset']


def superset(value, muster):
    """
    Determine whether given value is a (dict-wise) superset of the muster.
    Lists are treated as sets in that they must contain the items, but in
    no specific order.
    """

    if isinstance(muster, dict):
        if not isinstance(value, dict):
            return False

        for k in muster:
            if k not in value:
                return False

            if not superset(value[k], muster[k]):
                return False

        return True

    if isinstance(muster, set) or isinstance(muster, list):
        if not isinstance(value, set) and not isinstance(value, list):
            return False

        for mv in muster:
            matched = False
            for vv in value:
                if superset(vv, mv):
                    matched = True
                    break

            if not matched:
                return False

        return True

    return muster == value


# vim:set sw=4 ts=4 et:
# -*- coding: utf-8 -*-
