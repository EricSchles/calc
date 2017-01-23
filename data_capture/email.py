import re

from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.template.defaultfilters import pluralize
from django.conf import settings

from .models import SubmittedPriceList


class EmailResult():
    '''
    Simple class to hold result data from email sending functions
    '''
    def __init__(self, was_successful, context=None):
        self.was_successful = was_successful
        self.context = context or {}


def collapse_and_strip_tags(text):
    '''
    Strips HTML tags and collapases newlines in the given string.

    Example:

    >>> collapse_and_strip_tags('\\n\\n<p>hi james</p>\\n\\n\\n')
    '\\nhi james\\n'
    '''
    return re.sub(r'\n+', '\n', strip_tags(text))


def send_mail(subject, to, html_message, reply_to=None):
    '''
    Django's convinience send_mail function does not allow
    specification of the reply-to header, so we instead use
    the underlying EmailMultiAlternatives class to send CALC emails.

    Returns an integer representing the number of emails sent (just like
    Django's send_mail does).
    '''
    connection = get_connection()

    plaintext_message = collapse_and_strip_tags(html_message)

    msg = EmailMultiAlternatives(
        connection=connection,
        subject=subject,
        body=plaintext_message,
        to=to,
        reply_to=reply_to)

    msg.attach_alternative(html_message, 'text/html')

    return msg.send()


def price_list_approved(price_list, site_base_url='https://calc.gsa.gov'):
    details_link = site_base_url + reverse('data_capture:price_list_details',
                                           kwargs={'id': price_list.pk})

    ctx = {
        'price_list': price_list,
        'details_link': details_link,
    }

    if price_list.status is not SubmittedPriceList.STATUS_APPROVED:
        raise AssertionError('price_list.status must be STATUS_APPROVED')

    rendered_email = render_to_string(
        'data_capture/email/price_list_approved.html',
        ctx)

    result = send_mail(
        subject='CALC Price List Approved',
        html_message=rendered_email,
        reply_to=[settings.HELP_EMAIL],
        to=[price_list.submitter.email],
    )
    return EmailResult(
        was_successful=result is 1,
        context=ctx
    )


def price_list_retired(price_list, site_base_url='https://calc.gsa.gov'):
    details_link = site_base_url + reverse('data_capture:price_list_details',
                                           kwargs={'id': price_list.pk})

    ctx = {
        'price_list': price_list,
        'details_link': details_link,
    }

    if price_list.status is not SubmittedPriceList.STATUS_RETIRED:
        raise AssertionError('price_list.status must be STATUS_RETIRED')

    rendered_email = render_to_string(
        'data_capture/email/price_list_retired.html',
        ctx)

    result = send_mail(
        subject='CALC Price List Retired',
        html_message=rendered_email,
        reply_to=[settings.HELP_EMAIL],
        to=[price_list.submitter.email],
    )
    return EmailResult(
        was_successful=result is 1,
        context=ctx
    )


def price_list_rejected(price_list, site_base_url='https://calc.gsa.gov'):
    details_link = site_base_url + reverse('data_capture:price_list_details',
                                           kwargs={'id': price_list.pk})

    ctx = {
        'price_list': price_list,
        'details_link': details_link,
    }

    rendered_email = render_to_string(
        'data_capture/email/price_list_rejected.html',
        ctx)

    result = send_mail(
        subject='CALC Price List Rejected',
        html_message=rendered_email,
        reply_to=[settings.HELP_EMAIL],
        to=[price_list.submitter.email]
    )
    if price_list.status is not SubmittedPriceList.STATUS_REJECTED:
        raise AssertionError('price_list.status must be STATUS_REJECTED')
    return EmailResult(
        was_successful=result is 1,
        context=ctx
    )


def bulk_upload_succeeded(upload_source, num_contracts, num_bad_rows):
    ctx = {
        'upload_source': upload_source,
        'num_contracts': num_contracts,
        'num_bad_rows': num_bad_rows,
    }

    rendered_email = render_to_string(
        'data_capture/email/bulk_upload_succeeded.html',
        ctx)

    result = send_mail(
        subject='CALC Region 10 bulk data results - upload #{}'.format(
            upload_source.id),
        html_message=rendered_email,
        reply_to=[settings.HELP_EMAIL],
        to=[upload_source.submitter.email],
    )
    return EmailResult(
        was_successful=result is 1,
        context=ctx
    )


def bulk_upload_failed(upload_source, traceback,
                       site_base_url='https://calc.gsa.gov'):
    r10_upload_link = site_base_url + reverse(
        'data_capture:bulk_region_10_step_1')

    ctx = {
        'upload_source': upload_source,
        'traceback': traceback,
        'r10_upload_link': r10_upload_link
    }

    rendered_email = render_to_string(
        'data_capture/email/bulk_upload_failed.html',
        ctx)

    result = send_mail(
        subject='CALC Region 10 bulk data results - upload #{}'.format(
            upload_source.id
        ),
        html_message=rendered_email,
        reply_to=[settings.HELP_EMAIL],
        to=[upload_source.submitter.email],
    )
    return EmailResult(
        was_successful=result is 1,
        context=ctx
    )


def approval_reminder(count_unreviewed, site_base_url='https://calc.gsa.gov'):
    unreviewed_url = site_base_url + reverse(
        'admin:data_capture_unreviewedpricelist_changelist')

    ctx = {
        'count_unreviewed': count_unreviewed,
        'unreviewed_url': unreviewed_url,
    }

    rendered_email = render_to_string(
        'data_capture/email/approval_reminder.html',
        ctx
    )

    superusers = User.objects.filter(is_superuser=True)
    recipients = [s.email for s in superusers if s.email]

    result = send_mail(
        subject='CALC Reminder - {} price list{} not reviewed'.format(
            count_unreviewed, pluralize(count_unreviewed)),
        html_message=rendered_email,
        reply_to=[settings.HELP_EMAIL],
        to=recipients,
    )
    return EmailResult(
        was_successful=result is 1,  # or count of superusers
        context=ctx
    )
