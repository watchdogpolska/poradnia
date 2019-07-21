from django.urls import reverse
from teryt_tree.models import JednostkaAdministracyjna


class JST(JednostkaAdministracyjna):

    def get_absolute_url(self):
        return reverse('teryt:details', kwargs={'slug': self.slug})

    class Meta:
        proxy = True
