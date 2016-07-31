# -*- coding: utf-8 -*-

import re
import uuid
import os
import shutil
import hashlib
from random import randint

from django.dispatch.dispatcher import receiver
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from model_utils import Choices
from .utils import normalize_text, compress_files
from .signals import remove_proposal_file, remove_proposal_folder
from .managers import ProposalManager

def _generate_proposalnumber():
    return randint(1, 99999)

def _attachment_filepath(instance, filename):
  cpf = re.sub(r'\W', '_', instance.proposal.ente.cpf)
  proposal = instance.proposal.number
  filename = normalize_text(filename)
  path = "propostas/{cpf}/{proposal}/{filename}".format(
      cpf=cpf,
      proposal=proposal,
      filename=filename
  )
  return path


class Proposal(models.Model):
    STATUS_CHOICES = Choices(
        ('draft', "Rascunho"),
        ('sended', "Enviado"),
        ('canceled', "Cancelado"),
        ('analysis', "Em Análise"),
        ('approved', "Aprovado"),
        ('reproved', "Reprovado"),
    )

    ente = models.ForeignKey(
        'authentication.Ente',
        related_name='proposals'
    )
    title = models.CharField(
        max_length=60
    )
    number = models.PositiveIntegerField(
        default=_generate_proposalnumber,
        editable=False
    )
    status = models.CharField(
        max_length=10,
        editable=False,
        default=STATUS_CHOICES.draft
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sended_at = models.DateTimeField(blank=True, null=True)

    objects = ProposalManager()

    class Meta:
        ordering = ['-created_at', '-updated_at']

    @property
    def status_display(self):
        return Proposal.STATUS_CHOICES[self.status]

    def delete(self, *args, **kwargs):
        remove_proposal_folder.send(sender=self.__class__,
                                    instance=self,
                                    ente=self.ente)
        super(Proposal, self).delete(*args, **kwargs)

    # XXX: Melhorar esse método
    def compress_files(self, request):
        fullpath = os.path.dirname(self.attachments.first().file.path)
        path = self.attachments.first().file.url
        path = "/".join(path.split(os.sep)[:-2])
        filename = "{filename}.zip".format(filename=self.number)
        compress_files(fullpath, self.number)

        is_secure = request.is_secure()
        zipped_file = "{path}/{file}".format(path=path, file=filename)
        host = request.get_host()
        if is_secure:
            return "https://{url}{path}".format(url=host, path=zipped_file)
        else:
            return "http://{url}{path}".format(url=host, path=zipped_file)


    def __unicode__(self):
        return self.title


class AttachmentProposal(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    proposal = models.ForeignKey('Proposal', on_delete=models.CASCADE,
                                 related_name='attachments')
    file = models.FileField(upload_to=_attachment_filepath)
    checksum = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        remove_proposal_file.send(sender=self.__class__, instance=self)
        super(AttachmentProposal, self).delete(*args, **kwargs)


class ProposalDate(models.Model):
    is_available = models.BooleanField(default=False)

    def __unicode__(self):
        return "Settings"


# Signals
@receiver(pre_save, sender=AttachmentProposal)
def generate_checksum(sender, instance, **kwargs):
    instance.checksum = hashlib.md5(instance.file.read()).hexdigest()


@receiver(remove_proposal_file)
def delete_proposal_file(sender, instance, **kwargs):
    file_path = os.path.join(settings.MEDIA_ROOT, instance.file.name)
    if os.path.exists(file_path):
        os.remove(os.path.join(settings.MEDIA_ROOT, instance.file.name))


@receiver(remove_proposal_folder)
def delete_proposal_folder(sender, instance, ente, **kwargs):
    number = str(instance.number)
    cpf = re.sub(r'\W', '_', ente.cpf)
    path = "propostas/{0}/{1}".format(cpf, number)
    shutil.rmtree(os.path.join(settings.MEDIA_ROOT, path))
