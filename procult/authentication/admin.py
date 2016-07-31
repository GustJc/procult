# -*- coding: utf-8 -*-

from django.contrib import admin
import django.contrib.auth.admin as admin_auth
from .models import User, Ente
from .forms import EnteForm
from django.utils.translation import ugettext_lazy as _


class UserAdmin(admin_auth.UserAdmin):
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'is_admin')}),
        (_('Dados pessoais'), {'fields': ('name', )}),
        (_('Datas'), {'fields': ('created_at', 'updated_at')}),
        (_('Permissoes'), {'fields': ('is_superuser',
                                      'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'email', 'password1', 'password2',
                       'is_admin', 'groups')}
         ),
    )
    list_filter = []
    list_display = ('email', 'name')
    search_fields = ('email', 'name')
    ordering = ('email',)


class EnteAdmin(admin.ModelAdmin):
    form = EnteForm
    pass


admin.site.register(User, UserAdmin)
admin.site.register(Ente, EnteAdmin)
