from users.tasks import (
    generate_and_send_new_password,
    send_activation_email,
    send_password_reset_email,
    send_welcome_password_email,
)


def send_mail_activation(user):
    task = send_activation_email.delay(
        user_id=user.id,
        email=user.email,
        first_name=user.first_name or "",
        last_name=user.last_name or "",
    )

    return task.id


def send_mail_reset_password(user):
    task = send_password_reset_email.delay(
        user_id=user.id,
        email=user.email,
        first_name=user.first_name or "",
        last_name=user.last_name or "",
    )

    return task.id


def send_password_email(user, password, is_new_account=False):
    task = send_welcome_password_email.delay(
        user_id=user.id, email=user.email, password=password, is_new_account=is_new_account
    )

    return task.id


def generate_new_password_and_send(user, is_new_account=False):
    task = generate_and_send_new_password.delay(user_id=user.id, is_new_account=is_new_account)

    return task.id
