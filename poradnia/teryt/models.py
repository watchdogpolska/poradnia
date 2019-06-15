from django.urls import reverse
from teryt_tree.models import JednostkaAdministracyjna


class JST(JednostkaAdministracyjna):

    def get_absolute_url(self):
        return reverse('teryt:details', kwargs={'slug': self.slug})

    def case_qs(self):
        Case = self.case_set.model
        return Case.objects.filter(jst=self)

    def advice_qs(self):
        Advice = self.case_set.field.model.advice.related.field.model
        return Advice.objects.filter(case__jst=self)

    class Meta:
        proxy = True
