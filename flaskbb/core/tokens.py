# -*- coding: utf-8 -*-
"""
    flaskbb.core.auth.tokens
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides ways of interacting
    with tokens in FlaskBB

    :copyright: (c) 2014-2018 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""
from abc import abstractmethod

import attr

from .._compat import ABC
from .exceptions import BaseFlaskBBError

class TokenError(BaseFlaskBBError):
    """
    Raised when there is an issue with deserializing
    a token. Has helper classmethods to ensure
    consistent verbiage.
    """
    def __init__(self, reason):
        self.reason = reason
        super(TokenError, self).__init__(reason)

    @classmethod
    def invalid(cls):
        return cls('Token is invalid')

    @classmethod
    def expired(cls):
        return cls('Token is expired')

    # in theory this would never be raised
    # but it's provided for a generic catchall
    # when processing goes horribly wrong
    @classmethod  # pragma: no cover
    def bad(cls):
        return cls('Token cannot be processed')


# holder for token actions
# not an enum so plugins can add to it
class TokenActions:
    RESET_PASSWORD = 'reset_password'
    ACTIVATE_ACCOUNT = 'activate_account'


@attr.s(frozen=True, cmp=True, hash=True)
class Token(object):
    user_id = attr.ib()
    operation = attr.ib()


class TokenSerializer(ABC):
    """
    Interface for token serializers.

    dumps must accept a Token instance and produce
    a JWT

    loads must accept a string representation of
    a JWT and produce a token instance
    """
    @abstractmethod
    def dumps(self, token):
        pass

    @abstractmethod
    def loads(self, raw_token):
        pass


class TokenVerifier(ABC):
    """
    Used to verify the validatity of tokens post
    deserialization, such as an email matching the
    user id in the provided token.

    Should raise a flaskbb.core.exceptions.ValidationError
    if verification fails.
    """
    @abstractmethod
    def verify_token(self, token, **kwargs):
        pass

    def __call__(self, token, **kwargs):
        return self.verify_token(token, **kwargs)
