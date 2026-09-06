from .models import Contact

def contact_info(request):
    return {
        'contact': Contact.objects.all()
    }