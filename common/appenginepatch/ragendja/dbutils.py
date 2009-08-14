# -*- coding: utf-8 -*-
from django.db.models import signals
from django.http import Http404
from django.utils import simplejson
from google.appengine.ext import db
from ragendja.pyutils import getattr_by_path
from random import choice
from string import ascii_letters, digits

def get_filters(*filters):
    """Helper method for get_filtered."""
    if len(filters) % 2 == 1:
        raise ValueError('You must supply an even number of arguments!')
    return zip(filters[::2], filters[1::2])

def get_filtered(data, *filters):
    """Helper method for get_xxx_or_404."""
    for filter in get_filters(*filters):
        data.filter(*filter)
    return data

def get_object(model, *filters_or_key, **kwargs):
    if kwargs.get('key_name'):
        item = model.get_by_key_name(kwargs.get('key_name'),
            parent=kwargs.get('parent'))
    elif kwargs.get('id'):
        item = model.get_by_id(kwargs.get('id'),
            parent=kwargs.get('parent'))
    elif len(filters_or_key) > 1:
        item = get_filtered(model.all(), *filters_or_key).get()
    else:
        error = None
        if isinstance(filters_or_key[0], (tuple, list)):
            error = [None for index in range(len(filters_or_key[0]))]
        try:
            item = model.get(filters_or_key[0])
        except (db.BadKeyError, db.KindError):
            return error
    return item

def get_object_or_404(model, *filters_or_key, **kwargs):
    item = get_object(model, *filters_or_key, **kwargs)
    if not item:
        raise Http404('Object does not exist!')
    return item

def get_object_list(model, *filters):
    return get_filtered(model.all(), *filters)

def get_list_or_404(model, *filters):
    data = get_object_list(model, *filters)
    if not data.count(1):
        raise Http404('No objects found!')
    return data

KEY_NAME_PREFIX = 'k'
def generate_key_name(*values):
    """
    Escapes a string such that it can be used safely as a key_name.
    
    You can pass multiple values in order to build a path.
    """
    return KEY_NAME_PREFIX + '/'.join(
        [value.replace('%', '%1').replace('/', '%2') for value in values])

def transaction(func):
    """Decorator that always runs the given function in a transaction."""
    def _transaction(*args, **kwargs):
        return db.run_in_transaction(func, *args, **kwargs)
    # In case you need to run it without a transaction you can call
    # <func>.non_transactional(...)
    _transaction.non_transactional = func
    return _transaction

@transaction
def db_add(model, key_name, parent=None, **kwargs):
    """
    This function creates an object transactionally if it does not exist in
    the datastore. Otherwise it returns None.
    """
    existing = model.get_by_key_name(key_name, parent=parent)
    if not existing:
        new_entity = model(parent=parent, key_name=key_name, **kwargs)
        new_entity.put()
        return new_entity
    return None

def db_create(model, parent=None, key_name_format=u'%s',
        non_transactional=False, **kwargs):
    """
    Creates a new model instance with a random key_name and puts it into the
    datastore.
    """
    func = non_transactional and db_add.non_transactional or db_add
    charset = ascii_letters + digits
    while True:
        # The key_name is 16 chars long. Make sure that the first char doesn't
        # begin with a digit.
        key_name = key_name_format % (choice(ascii_letters) +
            ''.join([choice(charset) for i in range(15)]))
        result = func(model, key_name, parent=parent, **kwargs)
        if result:
            return result

def prefetch_references(object_list, references, cache=None):
    """
    Dereferences the given (Key)ReferenceProperty fields of a list of objects
    in as few get() calls as possible.
    """
    if object_list and references:
        if not isinstance(references, (list, tuple)):
            references = (references,)
        model = object_list[0].__class__
        targets = {}
        # Collect models and keys of all reference properties.
        # Storage format of targets: models -> keys -> instance, property
        for name in set(references):
            property = getattr(model, name)
            is_key_reference = isinstance(property, KeyReferenceProperty)
            if is_key_reference:
                target_model = property.target_model
            else:
                target_model = property.reference_class
            prefetch = targets.setdefault(target_model.kind(),
                                          (target_model, {}))[1]
            for item in object_list:
                if is_key_reference:
                    # Check if we already dereferenced the property
                    if hasattr(item, '_ref_cache_for_' + property.target_name):
                        continue
                    key = getattr(item, property.target_name)
                    if property.use_key_name and key:
                        key = db.Key.from_path(target_model.kind(), key)
                else:
                    if ReferenceProperty.is_resolved(property, item):
                        continue
                    key = property.get_value_for_datastore(item)
                if key:
                    # Check if we already have a matching item in cache
                    if cache:
                        found_cached = None
                        for cached_item in cache:
                            if cached_item.key() == key:
                                found_cached = cached_item
                        if found_cached:
                            setattr(item, name, found_cached)
                            continue
                    # No item found in cache. Retrieve it.
                    key = str(key)
                    prefetch[key] = prefetch.get(key, ()) + ((item, name),)
        for target_model, prefetch in targets.values():
            prefetched_items = target_model.get(prefetch.keys())
            for prefetched, group in zip(prefetched_items, prefetch.values()):
                for item, reference in group:
                    # If prefetched is None we only update the cache
                    if not prefetched:
                        property = getattr(model, reference)
                        if isinstance(property, KeyReferenceProperty):
                            setattr(item,
                                '_ref_cache_for_' + property.target_name, None)
                        else:
                            continue
                    setattr(item, reference, prefetched)
    return object_list

# Deprecated due to uglyness! :)
class KeyReferenceProperty(object):
    """
    Creates a cached accessor for a model referenced by a string property
    that stores a str(key) or key_name. This is useful if you need to work with
    the key of a referenced object, but mustn't get() it from the datastore.

    You can also integrate properties of the referenced model into the
    referencing model, so you don't need to dereference the model within a
    transaction. Note that if the referenced model's properties change you
    won't be notified, automatically.
    """
    def __init__(self, property, model, use_key_name=True, integrate={}):
        if isinstance(property, basestring):
            self.target_name = property
        else:
            # Monkey-patch the target property, so we can monkey-patch the
            # model class, so we can detect when the user wants to set our
            # KeyReferenceProperty via the model constructor.
            # What an ugly hack; but this is the simplest implementation. :(
            # One alternative would be to implement a proxy model that
            # provides direct access to the key, but this won't work with
            # isinstance(). Maybe that's an option for Python 3000.
            # Yet another alternative would be to force the user to choose
            # either .key_name or .reference manually. That's rather ugly, too.
            self.target_name = None
            myself = self
            old_config = property.__property_config__
            def __property_config__(model_class, property_name):
                myself.target_name = property_name
                my_name = None
                for key, value in model_class.__dict__.items():
                    if value is myself:
                        my_name = key
                        break
                old_init = model_class.__init__
                def __init__(self, *args, **kwargs):
                    if my_name in kwargs:
                        setattr(self, my_name, kwargs[my_name])
                        kwargs[property_name] = getattr(self, property_name)
                        for destination, source in myself.integrate.items():
                            integrate_value = None
                            if kwargs[my_name]:
                                try:
                                    property = getattr(self.__class__, source)
                                except:
                                    property = None
                                if property and isinstance(property, db.ReferenceProperty):
                                    integrate_value = property.get_value_for_datastore(self)
                                else:
                                    integrate_value = getattr_by_path(
                                        kwargs[my_name], source)
                            kwargs[destination] = integrate_value
                    old_init(self, *args, **kwargs)
                model_class.__init__ = __init__
                old_config(model_class, property_name)
            property.__property_config__ = __property_config__
        self.target_model = model
        self.use_key_name = use_key_name
        self.integrate = integrate

    def __get__(self, instance, unused):
        if instance is None:
            return self
        attr = getattr(instance, self.target_name)
        cache = getattr(instance, '_ref_cache_for_' + self.target_name, None)
        if not cache:
            cache_key = cache
        elif self.use_key_name:
            cache_key = cache.key().name()
        else:
            cache_key = str(cache.key())
        if attr != cache_key:
            if self.use_key_name:
                cache = self.target_model.get_by_key_name(attr)
            else:
                cache = self.target_model.get(attr)
            setattr(instance, '_ref_cache_for_' + self.target_name, cache)
        return cache

    def __set__(self, instance, value):
        if value and not isinstance(value, db.Model):
            raise ValueError('You must supply a Model instance.')
        if not value:
            key = None
        elif self.use_key_name:
            key = value.key().name()
        else:
            key = str(value.key())
        setattr(instance, '_ref_cache_for_' + self.target_name, value)
        setattr(instance, self.target_name, key)

        for destination, source in self.integrate.items():
            integrate_value = None
            if value:
                try:
                    property = getattr(value.__class__, source)
                except:
                    property = None
                if property and isinstance(property, db.ReferenceProperty):
                    integrate_value = property.get_value_for_datastore(value)
                else:
                    integrate_value = getattr_by_path(value, source)
            setattr(instance, destination, integrate_value)

# Don't use this, yet. It's not part of the official API!
class ReferenceProperty(db.ReferenceProperty):
    def __init__(self, reference_class, integrate={}, **kwargs):
        self.integrate = integrate
        super(ReferenceProperty, self).__init__(reference_class, **kwargs)

    @classmethod
    def is_resolved(cls, property, instance):
        try:
            if not hasattr(instance, property.__id_attr_name()) or \
                    not getattr(instance, property.__id_attr_name()):
                return True
            return bool(getattr(instance, property.__resolved_attr_name()))
        except:
            import logging
            logging.exception('ReferenceProperty implementation changed! '
                              'Update ragendja.dbutils.ReferenceProperty.'
                              'is_resolved! Exception was:')
        return False

    def __set__(self, instance, value):
        super(ReferenceProperty, self).__set__(instance, value)

        for destination, source in self.integrate.items():
            integrate_value = None
            if value:
                try:
                    property = getattr(value.__class__, source)
                except:
                    property = None
                if property and isinstance(property, db.ReferenceProperty):
                    integrate_value = property.get_value_for_datastore(value)
                else:
                    integrate_value = getattr_by_path(value, source)
            setattr(instance, destination, integrate_value)

def to_json_data(model_instance, property_list):
    """
    Converts a models into dicts for use with JSONResponse.

    You can either pass a single model instance and get a single dict
    or a list of models and get a list of dicts.

    For security reasons only the properties in the property_list will get
    added. If the value of the property has a json_data function its result
    will be added, instead.
    """
    if hasattr(model_instance, '__iter__'):
        return [to_json_data(item, property_list) for item in model_instance]
    json_data = {}
    for property in property_list:
        property_instance = None
        try:
            property_instance = getattr(model_instance.__class__,
                property.split('.', 1)[0])
        except:
            pass
        key_access = property[len(property.split('.', 1)[0]):]
        if isinstance(property_instance, db.ReferenceProperty) and \
                key_access in ('.key', '.key.name'):
            key = property_instance.get_value_for_datastore(model_instance)
            if key_access == '.key':
                json_data[property] = str(key)
            else:
                json_data[property] = key.name()
            continue
        value = getattr_by_path(model_instance, property, None)
        value = getattr_by_path(value, 'json_data', value)
        json_data[property] = value
    return json_data

def _get_included_cleanup_entities(entities, rels_seen, to_delete, to_put):
    # Models can define a CLEANUP_REFERENCES attribute if they have
    # reference properties that must get geleted with the model.
    include_references = getattr(entities[0], 'CLEANUP_REFERENCES', None)
    if include_references:
        if not isinstance(include_references, (list, tuple)):
            include_references = (include_references,)
        prefetch_references(entities, include_references)
        for entity in entities:
            for name in include_references:
                subentity = getattr(entity, name)
                to_delete.append(subentity)
                get_cleanup_entities(subentity, rels_seen=rels_seen,
                        to_delete=to_delete, to_put=to_put)

def get_cleanup_entities(instance, rels_seen=None, to_delete=None, to_put=None):
    if not instance or getattr(instance, '__handling_delete', False):
        return [], [], []

    if to_delete is None:
        to_delete = []
    if to_put is None:
        to_put = []
    if rels_seen is None:
        rels_seen = []

    # Delete many-to-one relations
    for related in instance._meta.get_all_related_objects():
        # Check if we already have fetched some of the entities
        seen = (instance.key(), related.opts, related.field.name)
        if seen in rels_seen:
            continue
        rels_seen.append(seen)

        entities = getattr(instance, related.get_accessor_name(),
            related.model.all().filter(related.field.name + ' =', instance))
        entities = entities.fetch(501)
        for entity in entities[:]:
            # Check if we might already have fetched this entity
            for item in to_delete:
                if item.key() == entity.key():
                    entities.remove(entity)
                    break
            for item in to_put:
                if item.key() == entity.key():
                    to_put.remove(item)
                    break

        to_delete.extend(entities)
        if len(to_delete) > 200:
            raise Exception("Can't delete so many entities at once!")

        if not entities:
            continue
        for entity in entities:
            get_cleanup_entities(entity, rels_seen=rels_seen,
                    to_delete=to_delete, to_put=to_put)

        _get_included_cleanup_entities(entities, rels_seen, to_delete, to_put)


    # Clean up many-to-many relations
    for related in instance._meta.get_all_related_many_to_many_objects():
        seen = (instance.key(), related.opts, related.field.name)
        if seen in rels_seen:
            continue
        rels_seen.append(seen)
        entities = getattr(instance, related.get_accessor_name(),
            related.model.all().filter(related.field.name + ' =', instance))
        entities = entities.fetch(501)
        for entity in entities[:]:
            # Check if we might already have fetched this entity
            for item in to_put + to_delete:
                if item.key() == entity.key():
                    entities.remove(entity)
                    entity = item
                    break

            # We assume that data is a list. Remove instance from the list.
            data = getattr(entity, related.field.name)
            data = [item for item in data
                    if (isinstance(item, db.Key) and
                        item != instance.key()) or
                       item.key() != instance.key()]
            setattr(entity, related.field.name, data)
        to_put.extend(entities)
        if len(to_put) > 200:
            raise Exception("Can't change so many entities at once!")

    return rels_seen, to_delete, to_put

def cleanup_relations(instance, **kwargs):
    if getattr(instance, '__handling_delete', False):
        return
    rels_seen, to_delete, to_put = get_cleanup_entities(instance)
    _get_included_cleanup_entities((instance,), rels_seen, to_delete, to_put)
    for entity in [instance] + to_delete:
        entity.__handling_delete = True
    if to_delete:
        db.delete(to_delete)
    for entity in [instance] + to_delete:
        del entity.__handling_delete
    if to_put:
        db.put(to_put)

class FakeModel(object):
    """A fake model class which is stored as a string.

    This can be useful if you need to emulate some model whose entities
    get generated by syncdb and are never modified afterwards.
    For example: ContentType and Permission.

    Use this with FakeModelProperty and FakeModelListProperty (the latter
    simulates a many-to-many relation).
    """
    # Important: If you want to change your fields at a later point you have
    # to write a converter which upgrades your datastore schema.
    fields = ('value',)

    def __init__(self, **kwargs):
        if sorted(kwargs.keys()) != sorted(self.fields):
            raise ValueError('You have to pass the following values to '
                             'the constructor: %s' % ', '.join(self.fields))

        for key, value in kwargs.items():
            setattr(self, key, value)

    class _meta(object):
        installed = True

    def get_value_for_datastore(self):
        return simplejson.dumps([getattr(self, field) for field in self.fields])

    @property
    def pk(self):
        return self.get_value_for_datastore()

    @property
    def id(self):
        return self.pk

    @classmethod
    def load(cls, value):
        return simplejson.loads(value)

    @classmethod
    def make_value_from_datastore(cls, value):
        return cls(**dict(zip(cls.fields, cls.load(value))))

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__,
                             ' | '.join([unicode(getattr(self, field))
                                         for field in self.fields]))

class FakeModelProperty(db.Property):
    data_type = basestring

    def __init__(self, model, raw=False, *args, **kwargs):
        self.raw = raw
        self.model = model
        super(FakeModelProperty, self).__init__(*args, **kwargs)

    def validate(self, value):
        if isinstance(value, basestring):
            value = self.make_value_from_datastore(value)
        if not isinstance(value, self.model):
            raise db.BadValueError('Value must be of type %s' %
                                   self.model.__name__)
        if self.validator is not None:
            self.validator(value)
        return value

    def get_value_for_datastore(self, model_instance):
        fake_model = getattr(model_instance, self.name)
        if not fake_model:
            return None
        if not self.indexed:
            return db.Text(fake_model.get_value_for_datastore())
        return fake_model.get_value_for_datastore()

    def make_value_from_datastore(self, value):
        if not value:
            return None
        return self.model.make_value_from_datastore(unicode(value))

    def get_value_for_form(self, instance):
        return self.get_value_for_datastore(instance)

    def make_value_from_form(self, value):
        return value

    def __set__(self, model_instance, value):
        if isinstance(value, basestring):
            value = self.make_value_from_datastore(value)
        super(FakeModelProperty, self).__set__(model_instance, value)

    @classmethod
    def get_fake_defaults(self, fake_model, multiple=False, **kwargs):
        from ragendja import forms
        form = multiple and forms.FakeModelMultipleChoiceField or \
                            forms.FakeModelChoiceField
        defaults = {'form_class': form, 'fake_model': fake_model}
        defaults.update(kwargs)
        return defaults

    def get_form_field(self, **kwargs):
        if self.raw:
          from django import forms
          defaults = kwargs
          defaults['widget'] = forms.TextInput(attrs={'size': 80})
        else:
          defaults = FakeModelProperty.get_fake_defaults(self.model, **kwargs)
        return super(FakeModelProperty, self).get_form_field(**defaults)

class FakeModelListProperty(db.ListProperty):
    fake_item_type = basestring

    def __init__(self, model, *args, **kwargs):
        self.model = model
        if not kwargs.get('indexed', True):
            self.fake_item_type = db.Text
        super(FakeModelListProperty, self).__init__(
            self.__class__.fake_item_type, *args, **kwargs)

    def validate(self, value):
        new_value = []
        for item in value:
            if isinstance(item, basestring):
                item = self.make_value_from_datastore([item])[0]
            if not isinstance(item, self.model):
                raise db.BadValueError('Value must be of type %s' %
                                       self.model.__name__)
            new_value.append(item)
        if self.validator is not None:
            self.validator(new_value)
        return new_value

    def get_value_for_datastore(self, model_instance):
        fake_models = getattr(model_instance, self.name)
        if not self.indexed:
            return [db.Text(fake_model.get_value_for_datastore())
                    for fake_model in fake_models]
        return [fake_model.get_value_for_datastore()
                for fake_model in fake_models]

    def make_value_from_datastore(self, value):
        return [self.model.make_value_from_datastore(unicode(item))
                for item in value]

    def get_value_for_form(self, instance):
        return self.get_value_for_datastore(instance)

    def make_value_from_form(self, value):
        return value

    def get_form_field(self, **kwargs):
        defaults = FakeModelProperty.get_fake_defaults(self.model,
            multiple=True, **kwargs)
        defaults['required'] = False
        return super(FakeModelListProperty, self).get_form_field(**defaults)

class KeyListProperty(db.ListProperty):
    """Simulates a many-to-many relation using a list property.
    
    On the model level you interact with keys, but when used in a ModelForm
    you get a ModelMultipleChoiceField (as if it were a ManyToManyField)."""

    def __init__(self, reference_class, *args, **kwargs):
        self._reference_class = reference_class
        super(KeyListProperty, self).__init__(db.Key, *args, **kwargs)

    @property
    def reference_class(self):
        if isinstance(self._reference_class, basestring):
            from django.db import models
            self._reference_class = models.get_model(
                *self._reference_class.split('.', 1))
        return self._reference_class

    def validate(self, value):
        new_value = []
        for item in value:
            if isinstance(item, basestring):
                item = db.Key(item)
            if isinstance(item, self.reference_class):
                item = item.key()
            if not isinstance(item, db.Key):
                raise db.BadValueError('Value must be a key or of type %s' %
                                       self.reference_class.__name__)
            new_value.append(item)
        return super(KeyListProperty, self).validate(new_value)

    def get_form_field(self, **kwargs):
        from django import forms
        defaults = {'form_class': forms.ModelMultipleChoiceField,
                    'queryset': self.reference_class.all(),
                    'required': False}
        defaults.update(kwargs)
        return super(KeyListProperty, self).get_form_field(**defaults)
