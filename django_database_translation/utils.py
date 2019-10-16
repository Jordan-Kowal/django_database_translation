# coding: utf-8
"""
Description:
    Contains helper functions to assist you when working with database translations
Functions:
    all_instances_as_translated_dict: Applies 'instance_as_translated_dict' to the iterable of instances
    get_language_from_session: Returns the Language instance used by our user, or "False" if none is found
    instance_as_translated_dict: Returns a model instance into a dict containing all of its fields
    update_user_language: Updates the user current language following Django guildelines
"""


# --------------------------------------------------------------------------------
# > Imports
# --------------------------------------------------------------------------------
# Built-in

# Django
from django.db import models
from django.db.models.fields.files import ImageFieldFile, FieldFile
from django.utils.translation import activate, LANGUAGE_SESSION_KEY

# Third-party

# Local
from .models import Item, Language, Translation


# --------------------------------------------------------------------------------
# > Functions
# --------------------------------------------------------------------------------
def all_instances_as_translated_dict(instances, depth=True, language=None, request=None):
    """
    Description:
        Applies 'instance_as_translated_dict' to the iterable of instances
        Returns a list of dicts which contains the fields of all your instances
        Check the 'instance_as_translated_dict' for more info
    Args:
        instances (iterable): An iterable of your model instances
        depth (bool, optional): Determines if FK will also be transformed into dicts. Defaults to True.
        language (Language, optional): A Language instance from this app. Defaults to None.
        request (HttpRequest, option): HttpRequest from Django. Defaults to None.
    Returns:
        list: A list of dicts, where each dict contains the fields/values of the initial instances
    """
    # Checking arguments
    if language is None and request is None:
        raise TypeError("You must provide either 'language' or 'request'")
    # Get the language from the session
    if language is None:
        language = get_language_from_session(request)
    # Loop over instances
    results = []
    for instance in instances:
        result = instance_as_translated_dict(instance, depth=depth, language=language)
        results.append(result)
    return results


def get_language_from_session(request):
    """
    Description:
        Returns the Language instance used by our user, or "False" if none is found
    Args:
        request (HttpRequest): HttpRequest from Django
    Returns:
        Language: The currently used language from our app's Language model
    """
    language_name = request.session.get(LANGUAGE_SESSION_KEY, False)
    if language_name:
        try:
            language = Language.objects.get(django_language_name=language_name)
            return language
        except Language.DoesNotExist:
            return False
    return False


def instance_as_translated_dict(instance, depth=True, language=None, request=None):
    """
    Description:
        Returns a model instance into a dict containing all of its fields
        Language can be given as an argument, or guess through the user of "request"
        With "depth" set to True, ForeignKey will also be transformed into sub-dict
        Files and images are replaced by a subdict with 'path', 'url', and 'name' keys
        Meaning you will be able to manipulate the dict in an HTML template much like an instance
    Args:
        instance (Model): An instance from any of your models
        depth (bool, optional): Determines if FK will also be transformed into dicts. Defaults to True.
        language (Language, optional): A Language instance from this app. Defaults to None.
        request (HttpRequest, option): HttpRequest from Django. Defaults to None.
    Returns:
        dict: A dict with all of the instance's fields and values
    """
    # Checking arguments
    if language is None and request is None:
        raise TypeError("You must provide either 'language' or 'request'")
    # Get the language from the session
    if language is None:
        language = get_language_from_session(request)
    # Loop over fields
    translated_dict = {}
    fields = instance._meta.get_fields()
    for field in fields:
        value = getattr(instance, field.name, None)
        if value is not None:
            value_type = type(value)
            # Case 1: Get the translation
            if value_type == Item:
                new_value = Translation.objects.get(item=value, language=language).text
            # Case 2: Go to the linked model and repeat the process (unless depth=False)
            elif issubclass(value_type, models.Model):
                if depth:
                    new_value = instance_as_translated_dict(value, depth=True, language=language)
                else:
                    new_value = value
            # Case 3:
            elif value_type in {ImageFieldFile, FieldFile}:
                if value:
                    new_value = {
                        "name": getattr(value, "name", ""),
                        "url": getattr(value, "url", ""),
                        "path": getattr(value, "path", ""),
                    }
                else:
                    new_value = ""
            # Case 4: Keep the value as it is
            else:
                new_value = value
            translated_dict[field.name] = new_value
    return translated_dict


def update_user_language(request, language=None, language_id=None):
    """
    Description:
        Updates the user current language following Django guildelines
        This will allow for both "Django" frontend translations and "our app" database translation
        The new language must be passed either through a Language instance or an ID
    Args:
        request (HttpRequest): Request object from Django, used to get to the session
        language (Language, optional): A Language instance from this app. Defaults to None.
        language_id (id, optional): ID of the language in our database. Defaults to None.
    """
    # Checking arguments
    if language is None and language_id is None:
        raise TypeError("You must provide either 'language' or 'language_id'")
    # Get the language from the session
    if language is None:
        language = Language.objects.get(id=language_id)
    # Update the user's language
    activate(language.django_language_name)
    request.session[LANGUAGE_SESSION_KEY] = language.django_language_name
