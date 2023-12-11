from django_filters.filters import ModelMultipleChoiceFilter
from django.utils.translation import gettext as _
from django.db.models import Q
from functools import reduce
from .models import JST


class AreaMultipleFilter(ModelMultipleChoiceFilter):
    """
    Multiple choice filter for JSTs.
    The queryset should implement a `area_in` method.
    """

    def __init__(self, *args, **kwargs):
        label = kwargs.pop("label", _("Area"))
        required = kwargs.pop("required", False)
        queryset = kwargs.pop("queryset", JST.objects.all())
        method = kwargs.pop("method", lambda q, _, v: q.area_in(v))
        super(ModelMultipleChoiceFilter, self).__init__(
            *args,
            label=label,
            required=required,
            queryset=queryset,
            method=method,
            **kwargs,
        )

    @staticmethod
    def filter_area_in(queryset, value, area_field=None):
        """
        Multiselect filter by area.
        If `value` is empty, returns an empty queryset.

        `area_field` is the field which points to a field of type `JST`.

        This method is not automatically injected to the queryset.
        It merely serves as a sample implementation of an `area_in` filter.
        """

        def with_area_field(path):
            if area_field is None:
                return path
            else:
                return "{}__{}".format(area_field, path)

        if not value:
            return queryset.none()

        return queryset.filter(
            reduce(
                lambda x, y: x | y,
                [
                    Q(
                        **{
                            with_area_field("tree_id"): jst.tree_id,
                            with_area_field("lft__range"): (jst.lft, jst.rght),
                        }
                    )
                    for jst in value
                ],
            )
        )
