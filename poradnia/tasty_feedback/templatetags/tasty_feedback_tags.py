from django import template

from ..utils import get_form

register = template.Library()


@register.inclusion_tag("tasty_feedback/widget.html", takes_context=True)
def tasty_feedback_widget(context):
    request = context["request"]
    return {
        "feedback_form": get_form()(
            user=None, initial={"url": request.build_absolute_uri()}
        ),
        "request": request,  # For nice django-crispy-forms experience
    }
