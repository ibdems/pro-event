from datetime import timedelta

import pytest
from django.utils import timezone

from event.models import Event, Partner


@pytest.mark.django_db
def test_creat_partner(partner):
    assert partner.name == "name partner test"
    assert partner.description == "description test"
    assert partner.partnership_type == "collaborator"


@pytest.mark.django_db
def test_create_user(user):
    assert user.email == "usertest@gmail.com"
    assert user.first_name == "user test"
    assert user.last_name == "test"
    assert user.contact == "628923883"
    assert user.role == "membre"


@pytest.mark.django_db
def test_create_event(event, category, user):
    assert event.title == "Test Event"
    assert event.category == category
    assert event.user == user
    assert event.total_capacity() == 170
    assert event.available_capacity() == 170
    assert event.prix_normal == 23000


@pytest.mark.django_db
def test_create_ticket(ticket, event):
    assert "PE-TI" in ticket.code_ticket
    assert ticket.event == event
    assert event.available_capacity() == 169
    assert ticket.qr_code is not None
    assert ticket.qr_code.name.startswith("qr_")
    assert ticket.qr_code.path.endswith(".png")


# @pytest.mark.django_db
# def test_create_payement(ticket, event):
#     ticket2 = Ticket.objects.create(
#         email_reception="emailtest@gmail.com",
#         telephone_payement="437348787",
#         event=event,

#     )
#     payement = Payement.objects.create(amount=ticket.prix_normal + ticket.prix_vip)
#     payement.tickets.set([ticket, ticket2])

#     assert payement.tickets.count() == 2
#     assert payement.amount == 60000
#     assert "PE-PA" in payement.reference_payement


def test_large_image_size(image_large):
    assert image_large.size > 2 * 1024 * 1024


@pytest.mark.django_db
def test_methode_save(image_large, user, category):
    # Test pour Event
    event = Event(
        user=user,
        category=category,
        title="Large Image Event",
        description="This event has a large image.",
        start_date=timezone.now() + timedelta(hours=1),
        end_date=timezone.now(),
        location="Test Location",
        normal_capacity=-2,
        vip_capacity=-3,
        vvip_capacity=-8,
        prix_normal=23000,
        prix_vip=45000,
        prix_vvip=100000,
        image=image_large,
    )

    with pytest.raises(Exception) as e:
        event.full_clean()
    assert (
        "L'image ne peut pas dépasser 2MB"
        and "La date de début ne peut pas être après la date de fin."
        and "La capacité ne peut pas être négative."
    ) in str(e.value)

    # Test pour Partner
    partner = Partner(
        name="test with image large",
        logo=image_large,
        description="image larger",
    )

    with pytest.raises(Exception) as e:
        partner.full_clean()

    assert "Le logo ne peut pas dépasser 2MB." in str(e.value)
