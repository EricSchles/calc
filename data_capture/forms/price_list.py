from django import forms

from ..models import SubmittedPriceList
from ..schedules import registry
from frontend.upload import UploadWidget
from frontend.date import SplitDateField
from frontend.radio import UswdsRadioSelect
from contracts.models import MIN_ESCALATION_RATE, MAX_ESCALATION_RATE


class Step1Form(forms.ModelForm):
    schedule = forms.ChoiceField(
        label="Which schedule is associated with this price list?",
        choices=registry.get_choices
    )

    class Meta:
        model = SubmittedPriceList
        fields = [
            'schedule',
            'contract_number',
            'vendor_name',
        ]

    def clean(self):
        cleaned_data = super().clean()
        schedule = cleaned_data.get('schedule')
        if schedule:
            cleaned_data['schedule_class'] = registry.get_class(schedule)
        return cleaned_data


class Step2Form(forms.ModelForm):
    is_small_business = forms.ChoiceField(
        label='Business size',
        choices=[
            (True, 'This is a small business.'),
            (False, 'This is not a small business.'),
        ],
        widget=UswdsRadioSelect,
    )
    contractor_site = forms.ChoiceField(
        label='Worksite',
        choices=SubmittedPriceList.CONTRACTOR_SITE_CHOICES,
        widget=UswdsRadioSelect,
    )
    contract_start = SplitDateField(
        label='Contract or current option period start'
    )
    contract_end = SplitDateField(
        label='Contract or current option period end'
    )
    escalation_rate = forms.FloatField(
        label="Escalation Rate (%)",
        help_text='This is the escalation rate (as a %) '
                  'for calculating out-year pricing. '
                  'Leave this field blank or enter 0 if this contract does '
                  'not have a fixed escalation rate.',
        min_value=MIN_ESCALATION_RATE,
        max_value=MAX_ESCALATION_RATE,
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        if 'contract_start' in cleaned_data and 'contract_end' in cleaned_data:
            start = cleaned_data['contract_start']
            end = cleaned_data['contract_end']
            if start > end:
                self.add_error('contract_start',
                               'Start date must be before end date.')

    def clean_escalation_rate(self):
        value = self.cleaned_data['escalation_rate']
        if value is None:
            value = 0
        return value

    class Meta:
        model = SubmittedPriceList
        fields = [
            'is_small_business',
            'contractor_site',
            'contract_start',
            'contract_end',
            'escalation_rate'
        ]


class Step3Form(forms.Form):
    file = forms.FileField(widget=UploadWidget())

    def __init__(self, *args, **kwargs):
        '''
        This constructor requires `schedule` to be passed in as a
        keyword argument. It should be a string referring to the
        fully-qualified class name for an entry in the schedule
        registry, e.g.
        "data_capture.schedules.fake_schedule.FakeSchedulePriceList".
        '''

        self.schedule = kwargs.pop('schedule')
        self.schedule_class = registry.get_class(self.schedule)

        super().__init__(*args, **kwargs)

        extra = self.schedule_class.upload_widget_extra_instructions
        if extra is not None:
            self.fields['file'].widget.extra_instructions = extra

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')

        if file:
            gleaned_data = registry.smart_load_from_upload(self.schedule,
                                                           file)

            if gleaned_data.is_empty():
                raise forms.ValidationError(
                    "The file you uploaded doesn't have any data we can "
                    "glean from it."
                )

            cleaned_data['gleaned_data'] = gleaned_data

        return cleaned_data
