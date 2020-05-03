import datetime as dt

from django.core.mail import send_mail


def year(request):
    """
    Добавляет переменную с текущим годом.
    """
    d = dt.datetime.today()
    year = d.year
    return {
        'year': year
    }


def send_mail(request):
    send_mail(
        'Тема письма',
        'Текст письма.',
        'from@example.com',
        ['to@example.com'],
        fail_silently=False,
    )
