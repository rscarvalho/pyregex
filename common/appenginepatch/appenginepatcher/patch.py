# -*- coding: utf-8 -*-
# Unfortunately, we have to fix a few App Engine bugs here because otherwise
# not all of our features will work. Still, we should keep the number of bug
# fixes to a minimum and report everything to Google, please:
# http://code.google.com/p/googleappengine/issues/list

from google.appengine.ext import db
from google.appengine.ext.db import polymodel
import logging, os, re, sys

base_path = os.path.abspath(os.path.dirname(__file__))

get_verbose_name = lambda class_name: re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', ' \\1', class_name).lower().strip()

DEFAULT_NAMES = ('verbose_name', 'ordering', 'permissions', 'app_label',
                 'abstract', 'db_table', 'db_tablespace')

# Add checkpoints to patching procedure, so we don't apply certain patches
# multiple times. This can happen if an exeception gets raised on the first
# request of an instance. In that case, main.py gets reloaded and patch_all()
# gets executed yet another time.
done_patch_all = False

def patch_all():
    global done_patch_all
    if done_patch_all:
        return
    patch_python()
    patch_app_engine()
    
    # Add signals: post_save_committed, post_delete_committed
    from appenginepatcher import transactions
    
    setup_logging()
    done_patch_all = True

def patch_python():
    # Remove modules that we want to override. Don't remove modules that we've
    # already overridden.
    for module in ('memcache',):
        if module in sys.modules and \
                not sys.modules[module].__file__.startswith(base_path):
            del sys.modules[module]

    # For some reason the imp module can't be replaced via sys.path
    from appenginepatcher import have_appserver
    if have_appserver:
        from appenginepatcher import imp
        sys.modules['imp'] = imp

    if have_appserver:
        def unlink(_):
            raise NotImplementedError('App Engine does not support FS writes!')
        os.unlink = unlink

def patch_app_engine():
    # This allows for using Paginator on a Query object. We limit the number
    # of results to 301, so there won't be any timeouts (301, so you can say
    # "more than 300 results").
    def __len__(self):
        return self.count()
    db.Query.__len__ = __len__
    
    old_count = db.Query.count
    def count(self, limit=301):
        return old_count(self, limit)
    db.Query.count = count
    
    # Add "model" property to Query (needed by generic views)
    class ModelProperty(object):
        def __get__(self, query, unused):
            try:
                return query._Query__model_class
            except:
                return query._model_class
    db.Query.model = ModelProperty()
    db.GqlQuery.model = ModelProperty()

    # Add a few Model methods that are needed for serialization and ModelForm
    def _get_pk_val(self):
        if self.has_key():
            return unicode(self.key())
        else:
            return None
    db.Model._get_pk_val = _get_pk_val
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self._get_pk_val() == other._get_pk_val()
    db.Model.__eq__ = __eq__
    def __ne__(self, other):
        return not self.__eq__(other)
    db.Model.__ne__ = __ne__
    def pk(self):
        return self._get_pk_val()
    db.Model.id = db.Model.pk = property(pk)
    def serializable_value(self, field_name):
        """
        Returns the value of the field name for this instance. If the field is
        a foreign key, returns the id value, instead of the object. If there's
        no Field object with this name on the model, the model attribute's
        value is returned directly.

        Used to serialize a field's value (in the serializer, or form output,
        for example). Normally, you would just access the attribute directly
        and not use this method.
        """
        from django.db.models.fields import FieldDoesNotExist
        try:
            field = self._meta.get_field(field_name)
        except FieldDoesNotExist:
            return getattr(self, field_name)
        return getattr(self, field.attname)
    db.Model.serializable_value = serializable_value

    # Make Property more Django-like (needed for serialization and ModelForm)
    db.Property.serialize = True
    db.Property.editable = True
    db.Property.help_text = ''
    def blank(self):
        return not self.required
    db.Property.blank = property(blank)
    def _get_verbose_name(self):
        if not getattr(self, '_verbose_name', None):
            self._verbose_name = self.name.replace('_', ' ')
        return self._verbose_name
    def _set_verbose_name(self, verbose_name):
        self._verbose_name = verbose_name
    db.Property.verbose_name = property(_get_verbose_name, _set_verbose_name)

    def attname(self):
        return self.name
    db.Property.attname = property(attname)

    class EmptyObject(object):
        pass

    class Rel(object):
        def __init__(self, property):
            self.field_name = 'key'
            self.field = EmptyObject()
            self.field.name = self.field_name
            self.property = property
            self.to = property.reference_class
            self.multiple = True
            self.parent_link = False
            self.related_name = getattr(property, 'collection_name', None)
            self.through = None

        def get_related_field(self):
            """
            Returns the Field in the 'to' object to which this relationship is
            tied.
            """
            data = self.to._meta.get_field_by_name(self.field_name)
            if not data[2]:
                raise FieldDoesNotExist("No related field named '%s'" %
                        self.field_name)
            return data[0]

    class RelProperty(object):
        def __get__(self, property, cls):
            if property is None:
                return self
            if not hasattr(property, 'reference_class'):
                return None
            if not hasattr(property, '_rel_cache'):
                property._rel_cache = Rel(property)
            return property._rel_cache
    db.Property.rel = RelProperty()

    def formfield(self, **kwargs):
        return self.get_form_field(**kwargs)
    db.Property.formfield = formfield

    def _get_flatchoices(self):
        """Flattened version of choices tuple."""
        if not self.choices:
            return []
        if not isinstance(self.choices[0], (list, tuple)):
            return [(choice, choice) for choice in self.choices]
        flat = []
        for choice, value in self.choices:
            if type(value) in (list, tuple):
                flat.extend(value)
            else:
                flat.append((choice,value))
        return flat
    db.Property.flatchoices = property(_get_flatchoices)
    
    # Add repr to make debugging a little bit easier
    def __repr__(self):
        data = []
        if self.has_key():
            if self.key().name():
                data.append('key_name='+repr(self.key().name()))
            else:
                data.append('key_id='+repr(self.key().id()))
        for field in self._meta.fields:
            if isinstance(field, db.ReferenceProperty):
                data.append(field.name+'='+repr(field.get_value_for_datastore(self)))
                continue
            try:
                data.append(field.name+'='+repr(getattr(self, field.name)))
            except:
                data.append(field.name+'='+repr(field.get_value_for_datastore(self)))
        return u'%s(%s)' % (self.__class__.__name__, ', '.join(data))
    db.Model.__repr__ = __repr__

    # Add default __str__ and __unicode__ methods
    def __str__(self):
        return unicode(self).encode('utf-8')
    db.Model.__str__ = __str__
    def __unicode__(self):
        return unicode(repr(self))
    db.Model.__unicode__ = __unicode__

    # Replace save() method with one that calls put(), so a monkey-patched
    # put() will also work if someone uses save()
    def save(self):
        self.put()
    db.Model.save = save

    # Add _meta to Model, so porting code becomes easier (generic views,
    # xheaders, and serialization depend on it).
    from django.conf import settings
    from django.utils.encoding import force_unicode, smart_str
    from django.utils.translation import string_concat, get_language, \
        activate, deactivate_all
    class _meta(object):
        many_to_many = ()
        class pk:
            name = 'key'
            attname = 'pk'

            @classmethod
            def get_db_prep_lookup(cls, lookup_type, pk_value):
                if isinstance(pk_value, db.Key):
                    return pk_value
                return db.Key(pk_value)

        def __init__(self, model, bases):
            try:
                self.app_label = model.__module__.split('.')[-2]
            except IndexError:
                raise ValueError('Django expects models (here: %s.%s) to be defined in their own apps!' % (model.__module__, model.__name__))
            self.parents = [b for b in bases if issubclass(b, db.Model)]
            self.object_name = model.__name__
            self.module_name = self.object_name.lower()
            self.verbose_name = get_verbose_name(self.object_name)
            self.ordering = ()
            self.abstract = model is db.Model
            self.model = model
            self.unique_together = ()
            self.proxy = False
            self.has_auto_field = True
            self.installed = model.__module__.rsplit('.', 1)[0] in \
                             settings.INSTALLED_APPS
            self.permissions = []

            meta = model.__dict__.get('Meta')
            if meta:
                meta_attrs = meta.__dict__.copy()
                for name in meta.__dict__:
                    # Ignore any private attributes that Django doesn't care about.
                    # NOTE: We can't modify a dictionary's contents while looping
                    # over it, so we loop over the *original* dictionary instead.
                    if name.startswith('_'):
                        del meta_attrs[name]
                for attr_name in DEFAULT_NAMES:
                    if attr_name in meta_attrs:
                        setattr(self, attr_name, meta_attrs.pop(attr_name))
                    elif hasattr(meta, attr_name):
                        setattr(self, attr_name, getattr(meta, attr_name))

                # verbose_name_plural is a special case because it uses a 's'
                # by default.
                setattr(self, 'verbose_name_plural', meta_attrs.pop('verbose_name_plural', string_concat(self.verbose_name, 's')))

                # Any leftover attributes must be invalid.
                if meta_attrs != {}:
                    raise TypeError, "'class Meta' got invalid attribute(s): %s" % ','.join(meta_attrs.keys())
            else:
                self.verbose_name_plural = self.verbose_name + 's'

            if not isinstance(self.permissions, list):
                self.permissions = list(self.permissions)

            if not self.abstract:
                self.permissions.extend([
                    ('add_%s' % self.object_name.lower(),
                        string_concat('Can add ', self.verbose_name)),
                    ('change_%s' % self.object_name.lower(),
                        string_concat('Can change ', self.verbose_name)),
                    ('delete_%s' % self.object_name.lower(),
                        string_concat('Can delete ', self.verbose_name)),
                ])

        def __repr__(self):
            return '<Options for %s>' % self.object_name

        def __str__(self):
            return "%s.%s" % (smart_str(self.app_label), smart_str(self.module_name))

        def _set_db_table(self, db_table):
            self._db_table = db_table
        
        def _get_db_table(self):
            if getattr(settings, 'DJANGO_STYLE_MODEL_KIND', True):
                if hasattr(self, '_db_table'):
                    return self._db_table
                return '%s_%s' % (self.app_label, self.module_name)
            return self.object_name

        db_table = property(_get_db_table, _set_db_table)

        def _set_db_tablespace(self, db_tablespace):
            self._db_tablespace = db_tablespace
        
        def _get_db_tablespace(self):
            if hasattr(self, '_db_tablespace'):
                return self._db_tablespace
            return settings.DEFAULT_TABLESPACE

        db_tablespace = property(_get_db_tablespace, _set_db_tablespace)

        @property
        def verbose_name_raw(self):
            """
            There are a few places where the untranslated verbose name is needed
            (so that we get the same value regardless of currently active
            locale).
            """
            lang = get_language()
            deactivate_all()
            raw = force_unicode(self.verbose_name)
            activate(lang)
            return raw

        @property
        def local_fields(self):
            return tuple(sorted([p for p in self.model.properties().values()
                                 if not isinstance(p, db.ListProperty)],
                                key=lambda prop: prop.creation_counter))

        @property
        def local_many_to_many(self):
            return tuple(sorted([p for p in self.model.properties().values()
                                 if isinstance(p, db.ListProperty) and
                                     not (issubclass(self.model,
                                                     polymodel.PolyModel)
                                          and p.name == 'class')],
                                key=lambda prop: prop.creation_counter))

        @property
        def fields(self):
            return self.local_fields + self.local_many_to_many

        def init_name_map(self):
            """
            Initialises the field name -> field object mapping.
            """
            from django.db.models.loading import app_cache_ready
            cache = {}
            # We intentionally handle related m2m objects first so that symmetrical
            # m2m accessor names can be overridden, if necessary.
            for f, model in self.get_all_related_m2m_objects_with_model():
                try:
                    cache[f.field.collection_name] = (f, model, False, True)
                except:
                    pass
            for f, model in self.get_all_related_objects_with_model():
                try:
                    cache[f.field.collection_name] = (f, model, False, False)
                except:
                    pass
            if app_cache_ready():
                self._name_map = cache
            return cache

        def get_field(self, name, many_to_many=True):
            """
            Returns the requested field by name. Raises FieldDoesNotExist on error.
            """
            for f in self.fields:
                if f.name == name:
                    return f
            from django.db.models.fields import FieldDoesNotExist
            raise FieldDoesNotExist, '%s has no field named %r' % (self.object_name, name)

        def get_field_by_name(self, name):
            """
            Returns the (field_object, model, direct, m2m), where field_object is
            the Field instance for the given name, model is the model containing
            this field (None for local fields), direct is True if the field exists
            on this model, and m2m is True for many-to-many relations. When
            'direct' is False, 'field_object' is the corresponding RelatedObject
            for this field (since the field doesn't have an instance associated
            with it).

            Uses a cache internally, so after the first access, this is very fast.
            """
            try:
                try:
                    return self._name_map[name]
                except AttributeError:
                    cache = self.init_name_map()
                    return cache[name]
            except KeyError:
                from django.db.models.fields import FieldDoesNotExist
                raise FieldDoesNotExist('%s has no field named %r'
                        % (self.object_name, name))

        def get_all_related_objects(self, local_only=False):
            try:
                self._related_objects_cache
            except AttributeError:
                self._fill_related_objects_cache()
            if local_only:
                return [k for k, v in self._related_objects_cache.items() if not v]
            return self._related_objects_cache.keys()

        def get_all_related_objects_with_model(self):
            """
            Returns a list of (related-object, model) pairs. Similar to
            get_fields_with_model().
            """
            try:
                self._related_objects_cache
            except AttributeError:
                self._fill_related_objects_cache()
            return self._related_objects_cache.items()

        def _fill_related_objects_cache(self):
            from django.db.models.loading import get_models
            from django.db.models.related import RelatedObject
            from django.utils.datastructures import SortedDict
            cache = SortedDict()
            parent_list = self.get_parent_list()
            for parent in self.parents:
                for obj, model in parent._meta.get_all_related_objects_with_model():
                    if (obj.field.creation_counter < 0 or obj.field.rel.parent_link) and obj.model not in parent_list:
                        continue
                    if not model:
                        cache[obj] = parent
                    else:
                        cache[obj] = model
            for klass in get_models():
                for f in klass._meta.local_fields:
                    if f.rel and not isinstance(f.rel.to, str) and self == f.rel.to._meta:
                        cache[RelatedObject(f.rel.to, klass, f)] = None
            self._related_objects_cache = cache

        def get_all_related_many_to_many_objects(self, local_only=False):
            try:
                cache = self._related_many_to_many_cache
            except AttributeError:
                cache = self._fill_related_many_to_many_cache()
            if local_only:
                return [k for k, v in cache.items() if not v]
            return cache.keys()

        def get_all_related_m2m_objects_with_model(self):
            """
            Returns a list of (related-m2m-object, model) pairs. Similar to
            get_fields_with_model().
            """
            try:
                cache = self._related_many_to_many_cache
            except AttributeError:
                cache = self._fill_related_many_to_many_cache()
            return cache.items()

        def _fill_related_many_to_many_cache(self):
            from django.db.models.loading import get_models, app_cache_ready
            from django.db.models.related import RelatedObject
            from django.utils.datastructures import SortedDict
            cache = SortedDict()
            parent_list = self.get_parent_list()
            for parent in self.parents:
                for obj, model in parent._meta.get_all_related_m2m_objects_with_model():
                    if obj.field.creation_counter < 0 and obj.model not in parent_list:
                        continue
                    if not model:
                        cache[obj] = parent
                    else:
                        cache[obj] = model
            for klass in get_models():
                for f in klass._meta.local_many_to_many:
                    if f.rel and not isinstance(f.rel.to, str) and self == f.rel.to._meta:
                        cache[RelatedObject(f.rel.to, klass, f)] = None
            if app_cache_ready():
                self._related_many_to_many_cache = cache
            return cache

        def get_add_permission(self):
            return 'add_%s' % self.object_name.lower()

        def get_change_permission(self):
            return 'change_%s' % self.object_name.lower()

        def get_delete_permission(self):
            return 'delete_%s' % self.object_name.lower()

        def get_ordered_objects(self):
            return []

        def get_parent_list(self):
            """
            Returns a list of all the ancestor of this model as a list. Useful for
            determining if something is an ancestor, regardless of lineage.
            """
            result = set()
            for parent in self.parents:
                result.add(parent)
                result.update(parent._meta.get_parent_list())
            return result

    # Required to support reference properties to db.Model
    db.Model._meta = _meta(db.Model, ())
    
    def _initialize_model(cls, bases):
        cls._meta = _meta(cls, bases)
        cls._default_manager = cls
        if not cls._meta.abstract:
            from django.db.models.loading import register_models
            register_models(cls._meta.app_label, cls)

    # Register models with Django
    from django.db.models import signals
    if not hasattr(db.PropertiedClass.__init__, 'patched'):
        old_propertied_class_init = db.PropertiedClass.__init__
        def __init__(cls, name, bases, attrs, map_kind=True):
            """Creates a combined appengine and Django model.

            The resulting model will be known to both the appengine libraries
            and Django.
            """
            _initialize_model(cls, bases)
            old_propertied_class_init(cls, name, bases, attrs,
                not cls._meta.abstract)
            signals.class_prepared.send(sender=cls)
        __init__.patched = True
        db.PropertiedClass.__init__ = __init__

    if not hasattr(polymodel.PolymorphicClass.__init__, 'patched'):
        old_poly_init = polymodel.PolymorphicClass.__init__
        def __init__(cls, name, bases, attrs):
            if polymodel.PolyModel not in bases:
                _initialize_model(cls, bases)
            old_poly_init(cls, name, bases, attrs)
            if polymodel.PolyModel not in bases:
                signals.class_prepared.send(sender=cls)
        __init__.patched = True
        polymodel.PolymorphicClass.__init__ = __init__

    @classmethod
    def kind(cls):
        return cls._meta.db_table
    db.Model.kind = kind

    # Add model signals
    if not hasattr(db.Model.__init__, 'patched'):
        old_model_init = db.Model.__init__
        def __init__(self, *args, **kwargs):
            signals.pre_init.send(sender=self.__class__, args=args,
                                  kwargs=kwargs)
            old_model_init(self, *args, **kwargs)
            signals.post_init.send(sender=self.__class__, instance=self)
        __init__.patched = True
        db.Model.__init__ = __init__

    if not hasattr(db.Model.put, 'patched'):
        old_put = db.Model.put
        def put(self, *args, **kwargs):
            signals.pre_save.send(sender=self.__class__, instance=self,
                                  raw=False)
            created = not self.is_saved()
            result = old_put(self, *args, **kwargs)
            signals.post_save.send(sender=self.__class__, instance=self,
                created=created, raw=False)
            return result
        put.patched = True
        db.Model.put = put

    if not hasattr(db.put, 'patched'):
        old_db_put = db.put
        def put(models, *args, **kwargs):
            if not isinstance(models, (list, tuple)):
                items = (models,)
            else:
                items = models
            items_created = []
            for item in items:
                if not isinstance(item, db.Model):
                    continue
                signals.pre_save.send(sender=item.__class__, instance=item,
                                      raw=False)
                items_created.append(not item.is_saved())
            result = old_db_put(models, *args, **kwargs)
            for item, created in zip(items, items_created):
                if not isinstance(item, db.Model):
                    continue
                signals.post_save.send(sender=item.__class__, instance=item,
                    created=created, raw=False)
            return result
        put.patched = True
        db.put = put

    if not hasattr(db.Model.delete, 'patched'):
        old_delete = db.Model.delete
        def delete(self, *args, **kwargs):
            signals.pre_delete.send(sender=self.__class__, instance=self)
            result = old_delete(self, *args, **kwargs)
            signals.post_delete.send(sender=self.__class__, instance=self)
            return result
        delete.patched = True
        db.Model.delete = delete

    if not hasattr(db.delete, 'patched'):
        old_db_delete = db.delete
        def delete(models, *args, **kwargs):
            if not isinstance(models, (list, tuple)):
                items = (models,)
            else:
                items = models
            for item in items:
                if not isinstance(item, db.Model):
                    continue
                signals.pre_delete.send(sender=item.__class__, instance=item)
            result = old_db_delete(models, *args, **kwargs)
            for item in items:
                if not isinstance(item, db.Model):
                    continue
                signals.post_delete.send(sender=item.__class__, instance=item)
            return result
        delete.patched = True
        db.delete = delete

    # This has to come last because we load Django here
    from django.db.models.fields import BLANK_CHOICE_DASH
    def get_choices(self, include_blank=True, blank_choice=BLANK_CHOICE_DASH):
        first_choice = include_blank and blank_choice or []
        if self.choices:
            return first_choice + list(self.choices)
        if self.rel:
            return first_choice + [(obj.pk, unicode(obj))
                                   for obj in self.rel.to.all().fetch(301)]
        return first_choice
    db.Property.get_choices = get_choices

    fix_app_engine_bugs()

def fix_app_engine_bugs():
    # Fix handling of verbose_name. Google resolves lazy translation objects
    # immedately which of course breaks translation support.
    # http://code.google.com/p/googleappengine/issues/detail?id=583
    from django import forms
    from django.utils.text import capfirst
    # This import is needed, so the djangoforms patch can do its work, first
    from google.appengine.ext.db import djangoforms
    def get_form_field(self, form_class=forms.CharField, **kwargs):
        defaults = {'required': self.required}
        defaults['label'] = capfirst(self.verbose_name)
        if self.choices:
            choices = []
            if not self.required or (self.default is None and
                                     'initial' not in kwargs):
                choices.append(('', '---------'))
            for choice in self.choices:
                choices.append((unicode(choice), unicode(choice)))
            defaults['widget'] = forms.Select(choices=choices)
        if self.default is not None:
            defaults['initial'] = self.default
        defaults.update(kwargs)
        return form_class(**defaults)
    db.Property.get_form_field = get_form_field

    # Extend ModelForm with support for EmailProperty
    # http://code.google.com/p/googleappengine/issues/detail?id=880
    def get_form_field(self, **kwargs):
        """Return a Django form field appropriate for an email property."""
        defaults = {'form_class': forms.EmailField}
        defaults.update(kwargs)
        return super(db.EmailProperty, self).get_form_field(**defaults)
    db.EmailProperty.get_form_field = get_form_field

    # Fix DateTimeProperty, so it returns a property even for auto_now and
    # auto_now_add.
    # http://code.google.com/p/googleappengine/issues/detail?id=994
    def get_form_field(self, **kwargs):
        defaults = {'form_class': forms.DateTimeField}
        defaults.update(kwargs)
        return super(db.DateTimeProperty, self).get_form_field(**defaults)
    db.DateTimeProperty.get_form_field = get_form_field
    def get_form_field(self, **kwargs):
        defaults = {'form_class': forms.DateField}
        defaults.update(kwargs)
        return super(db.DateProperty, self).get_form_field(**defaults)
    db.DateProperty.get_form_field = get_form_field
    def get_form_field(self, **kwargs):
        defaults = {'form_class': forms.TimeField}
        defaults.update(kwargs)
        return super(db.TimeProperty, self).get_form_field(**defaults)
    db.TimeProperty.get_form_field = get_form_field

    # Improve handing of StringListProperty
    def get_form_field(self, **kwargs):
        defaults = {'widget': forms.Textarea,
                    'initial': ''}
        defaults.update(kwargs)
        defaults['required'] = False
        return super(db.StringListProperty, self).get_form_field(**defaults)
    db.StringListProperty.get_form_field = get_form_field

    # Fix file uploads via BlobProperty
    def get_form_field(self, **kwargs):
        defaults = {'form_class': forms.FileField}
        defaults.update(kwargs)
        return super(db.BlobProperty, self).get_form_field(**defaults)
    db.BlobProperty.get_form_field = get_form_field
    def get_value_for_form(self, instance):
        return getattr(instance, self.name)
    db.BlobProperty.get_value_for_form = get_value_for_form
    from django.core.files.uploadedfile import UploadedFile
    def make_value_from_form(self, value):
        if isinstance(value, UploadedFile):
            return db.Blob(value.read())
        return super(db.BlobProperty, self).make_value_from_form(value)
    db.BlobProperty.make_value_from_form = make_value_from_form

    # Optimize ReferenceProperty, so it returns the key directly
    # http://code.google.com/p/googleappengine/issues/detail?id=993
    def get_value_for_form(self, instance):
        return self.get_value_for_datastore(instance)
    db.ReferenceProperty.get_value_for_form = get_value_for_form
    # Use our ModelChoiceField instead of Google's
    def get_form_field(self, **kwargs):
        defaults = {'form_class': forms.ModelChoiceField,
                    'queryset': self.reference_class.all()}
        defaults.update(kwargs)
        return super(db.ReferenceProperty, self).get_form_field(**defaults)
    db.ReferenceProperty.get_form_field = get_form_field

def setup_logging():
    from django.conf import settings
    if settings.DEBUG:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
