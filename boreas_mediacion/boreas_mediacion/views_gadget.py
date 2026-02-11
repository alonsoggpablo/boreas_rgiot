from django.views.generic import ListView
from boreas_mediacion.models import Gadget

class GadgetListView(ListView):
    model = Gadget
    template_name = 'boreas_mediacion/gadget_list.html'
    context_object_name = 'gadgets'
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset()
        # Optionally add filtering/sorting here
        return qs.order_by('device_id')
