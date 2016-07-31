from django import forms
from django.core.exceptions import ValidationError

from .serializers import ProposalSerializer
from .models import Proposal


class ProposalForm(forms.ModelForm):


    def clean(self):
        data = self.cleaned_data.copy()
        data['ente'] = data.get('ente').id if data.get('ente', False) else 1
        data['status'] = 'none'
        proposal_serializer = ProposalSerializer(data=data)

        if proposal_serializer.is_valid() is False:
            print proposal_serializer.errors
            if proposal_serializer.errors.get('availability', None):
                raise ValidationError(proposal_serializer.errors['availability'])
        super(ProposalForm, self).clean()
        


    class Meta:
        model = Proposal
        fields = ['ente', 'title', 'sended_at']

