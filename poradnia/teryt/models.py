from django.urls import reverse
from teryt_tree.models import JednostkaAdministracyjna


class JST(JednostkaAdministracyjna):
    def get_absolute_url(self):
        return reverse("teryt:details", kwargs={"slug": self.slug})

    def get_full_name(self):
        name = f"{self.name} ({self.id}, {self.category})"
        if self.parent:
            name = f"{self.parent} / {name}"
            if self.parent.parent:
                name = f"{self.parent.parent} / {name}"
        return name

    @property
    def tree_name(self):
        return self.get_full_name()

    class Meta:
        proxy = True

    def __str__(self):
        return self.tree_name
