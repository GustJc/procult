# -*- coding: utf-8 -*-

from django.contrib.auth import update_session_auth_hash
from rest_framework import serializers
from rest_localflavor.br.serializers import BRCPFField, BRCNPJField
from .models import User, Ente


# XXX: Essa validação não é a melhor solução. Precisa ser refatorado.
class EnteSerializer(serializers.ModelSerializer):
    cpf = BRCPFField(allow_blank=True)
    cnpj = BRCNPJField(allow_blank=True)
    projects_total = serializers.SerializerMethodField()

    class Meta:
        model = Ente
        fields = ('id', 'ceac', 'cpf', 'cnpj', 'projects_total',)

    def _get_ente_instance(self):
        instance = self.root.instance
        if isinstance(instance, Ente):
            return instance
        if isinstance(instance, User):
            return instance.ente

    def validate(self, data):
        if data['cpf'] in ['', None] and data['cnpj'] in ['', None]:
            raise serializers.ValidationError(
                "Número do seu documento é obrigatório")
        return data

    def validate_cpf(self, value):
        instance = self._get_ente_instance()
        is_created = Ente.objects.is_created(cpf=value)
        msg = "Esse CPF já foi usado no sistema"

        if instance:
            if instance.cpf != value and is_created:
                raise serializers.ValidationError(msg)
        else:
            if value and is_created:
                raise serializers.ValidationError(msg)
        return value

    def validate_cnpj(self, value):
        instance = self._get_ente_instance()
        is_created = Ente.objects.is_created(cnpj=value)
        msg = "Esse CNPJ já foi usado no sistema"

        if instance:
            if instance.cnpj != value and is_created:
                raise serializers.ValidationError(msg)
        else:
            if value and is_created:
                raise serializers.ValidationError(msg)
        return value

    def validate_ceac(self, value):
        instance = self._get_ente_instance()
        is_created = Ente.objects.is_created(ceac=value)
        msg = "Esse CEAC já foi usado no sistema"

        if instance:
            if instance.ceac != value and is_created:
                raise serializers.ValidationError(msg)
        else:
            if value and is_created:
                raise serializers.ValidationError(msg)
        return value

    def get_projects_total(self, obj):
        return obj.proposals.count()


class UserSerializer(serializers.ModelSerializer):
    ente = EnteSerializer(required=False)
    password1 = serializers.CharField(write_only=True, required=False)
    password2 = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'ente',
                  'password1', 'password2', 'is_admin')
        read_only_fields = ('created_at', 'updated_at', 'is_admin',)

    def validate(self, data):
        is_admin = data.get('is_admin', False)
        ente = data.get('ente')
        if not ente and not is_admin:
            raise serializers.ValidationError(
                {"ente": "Os dados dos entes são obrigatórios"}
            )
        return data

    def create(self, validated_data):
        ente = validated_data.pop('ente', None)
        password1 = validated_data.pop('password1', None)
        password2 = validated_data.pop('password2', None)

        if ente:
            serializer = EnteSerializer(data=ente)
            if serializer.is_valid():
                if password1 and password2 and password1 == password2:
                    user = User.objects.create(**validated_data)
                    user.set_password(password1)
                    user.save()
                else:
                    raise serializers.ValidationError(
                        {
                            "password2":
                            "As senhas não se batem. Digite novamente"
                        }
                    )
                serializer.save(user=user)

        return user

    def update(self, instance, validated_data):
        ente = validated_data.pop('ente', None)

        instance.name = validated_data.get('name', instance.name)
        instance.email = validated_data.get('email', instance.email)
        password = validated_data.pop('password1', None)
        confirm_password = validated_data.pop('password2', None)
        is_admin = validated_data.pop('is_admin', False)

        if ente and not is_admin:
            ente_serializer = EnteSerializer(instance.ente, data=ente)
            if ente_serializer.is_valid():
                ente_serializer.save()

        if password and confirm_password and password == confirm_password:
            instance.set_password(password)

        instance.save()
        update_session_auth_hash(self.context.get('request'), instance)

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True, required=True)
    old_password = serializers.CharField(write_only=True, required=True)
    password1 = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        fields = ('email', 'old_password', 'password1', 'password2',)

    def update(self, instance, validated_data):
        email = validated_data.pop('email', None)
        old_password = validated_data.pop('old_password', None)
        password1 = validated_data.pop('password1', None)
        password2 = validated_data.pop('password2', None)

        if email in [None, '']:
            raise serializers.ValidationError("E-mail é obrigatório.")

        if old_password in [None, '']:
            raise serializers.ValidationError("Digite sua antiga senha.")

        user_checked = instance.check_password(old_password)

        if user_checked:
            if password1 and password2 and password1 == password2:
                instance.set_password(password1)
                instance.save()
            else:
                raise serializers.ValidationError(
                    "As senhas não se batem. Digite novamente"
                )
        else:
            raise serializers.ValidationError(
                {
                    'old_password': "A senha antiga é inválida. Tente novamente"
                }
            )

        return instance


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
