from django.contrib import admin


from .models import Contact
from .models import UserProfile
admin.site.register(Contact)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        "full_name",
        "contact_number",
    )

    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "contact_number",
    )

    def full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    full_name.short_description = "Full Name"