# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets, status, views
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.generics import (
    CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
)
from procult.authentication.models import User
from procult.authentication.serializers import (
    UserSerializer, LoginSerializer, ChangePasswordSerializer
)
from procult.core.models import Proposal, AttachmentProposal, ProposalDate
from procult.core.resources import ProposalResource
from procult.core.serializers import (
    ProposalSerializer, ProposalUploadSerializer,
    ProposalLastSendedSerializer, ProposalLastAnalyzedSerializer,
    ProposalDateSerializer
)


class ProposalDateViewSet(viewsets.ModelViewSet):
    lookup_field = 'id'
    queryset = ProposalDate.objects.all()
    serializer_class = ProposalDateSerializer


class UserViewSet(viewsets.ModelViewSet):
    lookup_field = 'id'
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ProposalViewSet(ListAPIView, RetrieveAPIView, UpdateAPIView,
                      DestroyAPIView):
    lookup_field = 'number'
    queryset = Proposal.objects.all()
    serializer_class = ProposalSerializer
    parser_classes = (MultiPartParser, FormParser,)

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return (permissions.AllowAny(),)

        # FIXME: Implementar uma melhor verificacao de autenticacao, e
        # depois substituir por isso.
        # return (permissions.IsAuthenticated(), IsOwner(),)

        return (permissions.AllowAny(),)


class ProposalDashboardView(views.APIView):
    def get(self, request):
        last_sended = ProposalLastSendedSerializer(
            Proposal.objects.last_sended(),
            many=True
        )
        last_analyzed = ProposalLastAnalyzedSerializer(
            Proposal.objects.last_analyzed(),
            many=True
        )
        data = {
            'drafted': Proposal.objects.drafted().count(),
            'sended': Proposal.objects.sended().count(),
            'approved': Proposal.objects.approved().count(),
            'reproved': Proposal.objects.reproved().count(),
            'canceled': Proposal.objects.canceled().count(),
            'last_sended': last_sended.data,
            'last_analyzed': last_analyzed.data
        }
        return Response(data)


class ProposalView(ListAPIView, CreateAPIView):
    queryset = Proposal.objects.exclude(status=Proposal.STATUS_CHOICES.draft)
    serializer_class = ProposalSerializer

    def post(self, request):
        serializer = ProposalSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProposalUploadFilesView(views.APIView):
    parser_classes = (MultiPartParser, FormParser,)

    def post(self, request, number):
        proposal = Proposal.objects.get(number=number)
        serializer = ProposalUploadSerializer(data=request.data,
                                              context={'request': request})

        if serializer.is_valid():
            serializer.save(proposal=proposal, file=request.data.get('file'))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProposalUploadFilesDetailView(views.APIView):
    parser_classes = (MultiPartParser, FormParser,)

    def get(self, request, uid):
        proposal = AttachmentProposal.objects.get(uid=uid)
        serializer = ProposalUploadSerializer(proposal,
                                              context={'request': request})
        return Response(serializer.data)

    def delete(self, request, uid):
        proposal = AttachmentProposal.objects.get(uid=uid)
        proposal.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProposalDetailView(RetrieveAPIView, UpdateAPIView, DestroyAPIView):
    lookup_field = 'number'
    queryset = Proposal.objects.all()
    serializer_class = ProposalSerializer


class ProposalAnalisysDetailView(views.APIView):
    def put(self, request, number, status):
        proposal = Proposal.objects.get(number=number)
        proposal.status = status
        proposal.save()
        return Response(status=status.HTTP_200_OK)


class CompressProposalFilesView(views.APIView):
    def get(self, request, number):
        proposal = get_object_or_404(Proposal, number=number)
        path = proposal.compress_files(self.request)
        return Response(data={'url': path})


class ExportProposalsView(views.APIView):
    def get(self, request):
        dataset = ProposalResource().export()
        response = HttpResponse(dataset.csv, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=propostas.csv'
        return response


class ProposalOwnListView(views.APIView):
    def get(self, request, user_pk):
        user = User.objects.get(pk=user_pk)
        proposals = Proposal.objects.filter(ente=user.ente)
        serializer = ProposalSerializer(proposals,
                                        context={'request': request},
                                        many=True)
        return Response(serializer.data)


class ChangePasswordView(views.APIView):
    def post(self, request, user_pk, format=None):
        user = User.objects.get(pk=user_pk)
        serializer = ChangePasswordSerializer(user, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)


class LoginView(views.APIView):
    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():

            email = serializer.validated_data.get('email')
            password = serializer.validated_data.get('password')
            user = authenticate(email=email, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)

                    serialized = UserSerializer(user)

                    return Response(serialized.data)
                else:
                    return Response({
                        'message': 'Essa conta não está autorizada.'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({
                    'message': 'Usuário ou senha estão inválidos.'
                }, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
