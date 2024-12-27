import pytest
from users.models import User
from event.models import Category, Event, Ticket, Partner, Payement
from django.utils import timezone
from datetime import timedelta
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.fixture
def user():
    return User.objects.create_user(
        email = 'usertest@gmail.com',
        first_name = 'user test',
        last_name = 'test',
        contact = '628923883',
        adresse = 'Conakry'
    )

@pytest.fixture
def category():
    return Category.objects.create(
        name='Category 1'
    )

@pytest.fixture
def partner():
    return Partner.objects.create(
        name = 'name partner test',
        description = 'description test'
    )

@pytest.fixture
def event(user, category):
    return Event.objects.create(
        user=user,
        category=category,
        title="Test Event",
        description="This is a test event.",
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(hours=7),
        location="Test Location",
        normal_capacity=100,
        vip_capacity=50,
        vvip_capacity=20,
    )


@pytest.fixture
def ticket(event):
    return Ticket.objects.create(
        name='name ticket test',
        email_reception = 'emailtest@gmail.com',
        telephone_payement = '437348787',
        event=event,
        prix_normal=15000,
        prix_vip=45000,
        prix_vvip=100000,
    )


@pytest.fixture
def image_large():
    img = Image.new("RGB", (20000, 20000), color="red")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile("large_image.jpg", buffer.getvalue(), content_type="image/jpeg")



