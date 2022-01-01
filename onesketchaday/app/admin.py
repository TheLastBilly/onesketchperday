from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.contrib import admin
from django import forms
from .models import *

class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ('username', 'telegram_username', 'mastodon_handle', 'twitter_handle', 'discord_username', 'is_staff', 'is_a_participant')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(UserCreationForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    class Meta:
        model = User
        fields = ('username', 'telegram_username', 'mastodon_handle', 'twitter_handle', 'discord_username', 'is_staff', 'is_a_participant')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if len(password1) < 1 and len(password2) < 1:
            return ""
        else:
            return UserCreationForm.clean_password2(self)

    def save(self, commit=True):
        password = self.cleaned_data["password1"]
        user = super(UserCreationForm, self).save(commit=False)

        if len(password) > 0:
            user.set_password(password)
        
        if commit:
            user.save()
        return user


class UserAdmin(BaseUserAdmin):
    default_fields = ('username', 'telegram_username', 'mastodon_handle', 'twitter_handle', 'discord_username', 'password1', 'password2')

    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('username', 'is_superuser', 'is_staff', 'is_a_participant', 'is_competing')
    list_filter = ('is_a_participant', 'is_competing', 'is_superuser')
    fieldsets = (
        (None, {'fields': default_fields}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser')}),
        ('Status', {'fields': ('is_a_participant',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': default_fields},
        ),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_a_participant')}),
    )
    search_fields = ('username',)
    ordering = ('username',)
    filter_horizontal = ()

admin.site.register(User, UserAdmin)
admin.site.unregister(Group)

class PostAdmin(admin.ModelAdmin):
    readonly_fields = ['timestamp', 'id', 'likes', 'date']

admin.site.register(Post, PostAdmin)
admin.site.register(Variable)
admin.site.register(MardownPost)