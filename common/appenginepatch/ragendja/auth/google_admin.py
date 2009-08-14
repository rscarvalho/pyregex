from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

class UserAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('Personal info'), {'fields': ('user',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions')}),
        (_('Important dates'), {'fields': ('date_joined',)}),
        (_('Groups'), {'fields': ('groups',)}),
    )
    list_display = ('email', 'username', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('user',)
    filter_horizontal = ('user_permissions',)
