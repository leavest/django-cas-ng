from __future__ import absolute_import

import sys

import pytest
from django.test import RequestFactory

from django_cas_ng import backends


@pytest.mark.django_db
def test_backend_authentication_creating_a_user(monkeypatch, django_user_model):
    """
    Test the case where CAS authentication is creating a new user.
    """
    factory = RequestFactory()
    request = factory.get('/login/')
    request.session = {}

    def mock_verify(ticket, service):
        return 'test@example.com', {'ticket': ticket, 'service': service}, None

    # we mock out the verify method so that we can bypass the external http
    # calls needed for real authentication since we are testing the logic
    # around authentication.
    monkeypatch.setattr('django_cas_ng.backends._verify', mock_verify)

    # sanity check
    assert not django_user_model.objects.filter(
        username='test@example.com',
    ).exists()

    backend = backends.CASBackend()
    user = backend.authenticate(
        ticket='fake-ticket', service='fake-service', request=request,
    )

    assert user is not None
    assert user.username == 'test@example.com'
    assert django_user_model.objects.filter(
        username='test@example.com',
    ).exists()


@pytest.mark.django_db
def test_backend_for_existing_user(monkeypatch, django_user_model):
    """
    Test the case where CAS authenticates an existing user.
    """
    factory = RequestFactory()
    request = factory.get('/login/')
    request.session = {}

    def mock_verify(ticket, service):
        return 'test@example.com', {'ticket': ticket, 'service': service}, None

    # we mock out the verify method so that we can bypass the external http
    # calls needed for real authentication since we are testing the logic
    # around authentication.
    monkeypatch.setattr('django_cas_ng.backends._verify', mock_verify)

    existing_user = django_user_model.objects.create_user('test@example.com', '')

    backend = backends.CASBackend()
    user = backend.authenticate(
        ticket='fake-ticket', service='fake-service', request=request,
    )

    assert user is not None
    assert user.username == 'test@example.com'
    assert user == existing_user


@pytest.mark.django_db
def test_backend_for_failed_auth(monkeypatch, django_user_model):
    """
    Test CAS authentication failure.
    """
    factory = RequestFactory()
    request = factory.get('/login/')
    request.session = {}

    def mock_verify(ticket, service):
        return None, {}, None

    # we mock out the verify method so that we can bypass the external http
    # calls needed for real authentication since we are testing the logic
    # around authentication.
    monkeypatch.setattr('django_cas_ng.backends._verify', mock_verify)

    assert not django_user_model.objects.filter(
        username='test@example.com',
    ).exists()

    backend = backends.CASBackend()
    user = backend.authenticate(
        ticket='fake-ticket', service='fake-service', request=request,
    )

    assert user is None
    assert not django_user_model.objects.filter(
        username='test@example.com',
    ).exists()


def test_can_saml_assertion_is_encoded():
    ticket = 'test-ticket'

    saml = backends.get_saml_assertion(ticket)

    if sys.version_info > (3, 0):
        assert type(saml) is bytes
        assert ticket.encode('utf-8') in saml
    else:
        assert ticket in saml
