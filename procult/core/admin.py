from django.contrib import admin
from .models import Proposal, ProposalDate, AttachmentProposal
from .forms import ProposalForm

class AttachmentAdmin(admin.ModelAdmin):
    pass


class AttachmentInline(admin.TabularInline):
    readonly_fields=('checksum',)
    model = AttachmentProposal


class ProposalAdmin(admin.ModelAdmin):
    inlines = [AttachmentInline,]
    form = ProposalForm


class ProposalDateAdmin(admin.ModelAdmin):
    pass

admin.site.register(Proposal, ProposalAdmin)
admin.site.register(ProposalDate, ProposalDateAdmin)
admin.site.register(AttachmentProposal, AttachmentAdmin)
