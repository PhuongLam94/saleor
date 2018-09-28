import graphene
from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify

from ....product import models
from ...core.mutations import ModelDeleteMutation, ModelMutation
from ..types import AttributeValue


class AttributeCreateValueInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description='Name displayed in the interface.')
    value = graphene.String(
        required=True, description='Real value eg. HEX color.')


class AttributeCreateInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description='Name displayed in the interface.')
    values = graphene.List(
        AttributeCreateValueInput,
        description='Attribute values to be created for this attribute.')


class AttributeCreate(ModelMutation):
    ATTRIBUTE_VALUES_FIELD = 'values'

    class Arguments:
        input = AttributeCreateInput(
            required=True,
            description='Fields required to create an attribute.')

    class Meta:
        description = 'Creates an attribute.'
        model = models.Attribute

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')

    @classmethod
    def clean_attribute_value_uniqueness(cls, values, errors, error_msg):
        if len(set(values)) != len(values):
            cls.add_error(
                errors,
                cls.ATTRIBUTE_VALUES_FIELD,
                error_msg)
        return errors

    @classmethod
    def clean_attribute_values(cls, values, errors):
        for value_data in values:
            value_data['slug'] = slugify(value_data['name'])
            attribute_value = models.AttributeValue(**value_data)
            try:
                attribute_value.full_clean()
            except ValidationError as validation_errors:
                for field in validation_errors.message_dict:
                    if field == 'attribute':
                        continue
                    for message in validation_errors.message_dict[field]:
                        error_field = '%(values_field)s:%(field)s' % {
                            'values_field': cls.ATTRIBUTE_VALUES_FIELD,
                            'field': field}
                        cls.add_error(errors, error_field, message)
        return errors

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        cleaned_input['slug'] = slugify(cleaned_input['name'])
        values = cleaned_input.get(cls.ATTRIBUTE_VALUES_FIELD, [])
        if not values:
            return cleaned_input

        cls.clean_attribute_value_uniqueness(
            [v['name'] for v in values], errors,
            'Duplicated attribute value names provided.')

        slugs = []
        for value in values:
            value['slug'] = slugify(value['name'])
            slugs.append(value['slug'])
        cls.clean_attribute_value_uniqueness(
            slugs, errors, 'Provided attribute value names are not unique.')

        cls.clean_attribute_values(values, errors)
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        values = cleaned_data.get(cls.ATTRIBUTE_VALUES_FIELD, [])
        for value in values:
            instance.values.create(**value)


class AttributeUpdateInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description='Name displayed in the interface.')
    remove_values = graphene.List(
        graphene.ID, name='removeValues', required=True,
        description='List of attributes to be removed from this attribute.')
    add_values = graphene.List(
        AttributeCreateValueInput, name='addValues', required=True,
        description='Attribute values to be created for this attribute.')


class AttributeUpdate(AttributeCreate):
    ATTRIBUTE_VALUES_FIELD = 'add_values'

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an attribute to update.')
        input = AttributeUpdateInput(
            required=True,
            description='Fields required to update an attribute.')

    class Meta:
        description = 'Updates attribute.'
        model = models.Attribute

    @classmethod
    def clean_remove_values(cls, cleaned_input, instance, errors):
        attribute_values = cls.get_nodes_or_error(
            ids=cleaned_input.get('remove_values', []), errors=errors,
            only_type=AttributeValue, field=cls.ATTRIBUTE_VALUES_FIELD)
        if attribute_values:
            for value in attribute_values:
                if value.attribute != instance:
                    continue  # TODO
                    cls.add_error(
                        errors, 'remove_values:%s' % value,
                        'AttributeValue does not belong to this Attribute.')
        return attribute_values

    @classmethod
    def clean_add_values(cls, cleaned_input, instance, errors):
        existing_attribute_values = instance.values.flat_list('slug', 'name')
        existing_slugs, existing_names = zip(*existing_attribute_values)
        for value in cleaned_input.get('add_values', []):
            if value.name in existing_names:
                cls.add_error(
                    errors, 'add_values:%s' % value.name,
                    'AttributeValue with given name already exists.')
            if value.slug in existing_slugs:
                cls.add_error(
                    errors, 'add_values:%s' % value.slug,
                    'AttributeValue name is not unique.')
        return errors

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        cleaned_input['remove_values'] = cls.clean_remove_values(
            cleaned_input, instance, errors)
        cls.clean_add_values(cleaned_input, instance, errors)
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        for attribute_value in cleaned_data.get('removeValues', []):
            continue  # TODO
            attribute_value.delete()


class AttributeDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an attribute to delete.')

    class Meta:
        description = 'Deletes an attribute.'
        model = models.Attribute

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')


class AttributeValueCreateInput(graphene.InputObjectType):
    attribute = graphene.ID(
        required=True,
        description='Attribute to which value will be assigned.',
        name='attribute')
    name = graphene.String(
        required=True, description='Name displayed in the interface.')
    value = graphene.String(
        required=True, description='Real value eg. HEX color.')


class AttributeValueCreate(ModelMutation):
    class Arguments:
        input = AttributeValueCreateInput(
            required=True,
            description='Fields required to create an attribute choice value.')

    class Meta:
        description = 'Creates an attribute choice value.'
        model = models.AttributeValue

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)
        cleaned_input['slug'] = slugify(cleaned_input['name'])
        return cleaned_input


class AttributeValueUpdate(AttributeValueCreate):
    class Arguments:
        id = graphene.ID(
            required=True,
            description='ID of an attribute choice value to update.')
        input = AttributeValueCreateInput(
            required=True,
            description='Fields required to update an attribute choice value.')

    class Meta:
        description = 'Updates an attribute choice value.'
        model = models.AttributeValue


class AttributeValueDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description='ID of an attribute choice value to delete.')

    class Meta:
        description = 'Deletes an attribute choice value.'
        model = models.AttributeValue

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')
