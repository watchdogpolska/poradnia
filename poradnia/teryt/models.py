from django.urls import reverse
from teryt_tree.models import JednostkaAdministracyjna


class JST(JednostkaAdministracyjna):

    def get_absolute_url(self):
        return reverse('teryt:details', kwargs={'slug': self.slug})

    def advice_qs(self):
        Advice = self.advice_set.model
        return Advice.objects.filter(jst=self)

    class Meta:
        proxy = True
