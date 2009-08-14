# -*- coding: utf-8 -*-
from django.db.models import signals
from django.test import TestCase
from ragendja.dbutils import cleanup_relations
from ragendja.testutils import ModelTestCase
from google.appengine.ext import db
from google.appengine.ext.db.polymodel import PolyModel
from datetime import datetime

# Test class Meta

class TestA(db.Model):
    class Meta:
        abstract = True
        verbose_name = 'aaa'

class TestB(TestA):
    class Meta:
        verbose_name = 'bbb'

class TestC(TestA):
    pass

class TestModelRel(db.Model):
    modelrel = db.ReferenceProperty(db.Model)

class PolyA(PolyModel):
    class Meta:
        verbose_name = 'polyb'

class PolyB(PolyA):
    pass

class ModelMetaTest(TestCase):
    def test_class_meta(self):
        self.assertEqual(TestA._meta.verbose_name_plural, 'aaas')
        self.assertTrue(TestA._meta.abstract)

        self.assertEqual(TestB._meta.verbose_name_plural, 'bbbs')
        self.assertFalse(TestB._meta.abstract)

        self.assertEqual(TestC._meta.verbose_name_plural, 'test cs')
        self.assertFalse(TestC._meta.abstract)

        self.assertFalse(PolyA._meta.abstract)
        self.assertFalse(PolyB._meta.abstract)

# Test signals

class SignalTest(TestCase):
    def test_signals(self):
        global received_pre_delete
        global received_post_save
        received_pre_delete = False
        received_post_save = False
        def handle_pre_delete(**kwargs):
            global received_pre_delete
            received_pre_delete = True
        signals.pre_delete.connect(handle_pre_delete, sender=TestC)
        def handle_post_save(**kwargs):
            global received_post_save
            received_post_save = True
        signals.post_save.connect(handle_post_save, sender=TestC)
        a = TestC()
        a.put()
        a.delete()
        self.assertTrue(received_pre_delete)
        self.assertTrue(received_post_save)

    def test_batch_signals(self):
        global received_pre_delete
        global received_post_save
        received_pre_delete = False
        received_post_save = False
        def handle_pre_delete(**kwargs):
            global received_pre_delete
            received_pre_delete = True
        signals.pre_delete.connect(handle_pre_delete, sender=TestC)
        def handle_post_save(**kwargs):
            global received_post_save
            received_post_save = True
        signals.post_save.connect(handle_post_save, sender=TestC)
        a = TestC()
        db.put([a])
        db.delete([a])
        self.assertTrue(received_pre_delete)
        self.assertTrue(received_post_save)

# Test serialization

class SerializeModel(db.Model):
    name = db.StringProperty()
    count = db.IntegerProperty()
    created = db.DateTimeProperty()

class SerializerTest(ModelTestCase):
    model = SerializeModel

    def test_serializer(self, format='json'):
        from django.core import serializers
        created = datetime.now()
        x = SerializeModel(key_name='blue_key', name='blue', count=4)
        x.put()
        SerializeModel(name='green', count=1, created=created).put()
        data = serializers.serialize(format, SerializeModel.all())
        db.delete(SerializeModel.all().fetch(100))
        for obj in serializers.deserialize(format, data):
            obj.save()
        self.validate_state(
            ('key.name', 'name',  'count', 'created'),
            (None,       'green', 1, created),
            ('blue_key', 'blue',  4, None),
        )

    def test_xml_serializer(self):
        self.test_serializer(format='xml')

    def test_python_serializer(self):
        self.test_serializer(format='python')

    def test_yaml_serializer(self):
        self.test_serializer(format='yaml')

# Test ragendja cleanup handler
class SigChild(db.Model):
    CLEANUP_REFERENCES = 'rel'

    owner = db.ReferenceProperty(TestC)
    rel = db.ReferenceProperty(TestC, collection_name='sigchildrel_set')

class RelationsCleanupTest(TestCase):
    def test_cleanup(self):
        signals.pre_delete.connect(cleanup_relations, sender=TestC)
        c1 = TestC()
        c2 = TestC()
        db.put((c1, c2))
        TestModelRel(modelrel=c1).put()
        child = SigChild(owner=c1, rel=c2)
        child.put()
        self.assertEqual(TestC.all().count(), 2)
        self.assertEqual(SigChild.all().count(), 1)
        self.assertEqual(TestModelRel.all().count(), 1)
        c1.delete()
        signals.pre_delete.disconnect(cleanup_relations, sender=TestC)
        self.assertEqual(SigChild.all().count(), 0)
        self.assertEqual(TestC.all().count(), 0)
        self.assertEqual(TestModelRel.all().count(), 0)

from ragendja.dbutils import FakeModel, FakeModelProperty, \
    FakeModelListProperty

class FM(db.Model):
    data = FakeModelProperty(FakeModel, indexed=False)

class FML(db.Model):
    data = FakeModelListProperty(FakeModel, indexed=False)

# Test FakeModel, FakeModelProperty, FakeModelListProperty
class RelationsCleanupTest(TestCase):
    def test_fake_model_property(self):
        value = {'bla': [1, 2, {'blub': 'bla'*1000}]}
        FM(data=FakeModel(value=value)).put()
        self.assertEqual(FM.all()[0].data.value, value)

    def test_fake_model_list_property(self):
        value = {'bla': [1, 2, {'blub': 'bla'*1000}]}
        FML(data=[FakeModel(value=value)]).put()
        self.assertEqual(FML.all()[0].data[0].value, value)        
