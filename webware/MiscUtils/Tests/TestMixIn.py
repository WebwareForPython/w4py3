import unittest

from MiscUtils.MixIn import MixIn


class TestMixIn(unittest.TestCase):

    def setUp(self):
        class Base:
            attr0 = 'this is Base.attr0'
            attr1 = 'this is Base.attr1'

            def foo(self):
                return 'this is Base.foo'

        class PyClass(Base):
            attr1 = 'this is PyClass.attr1'
            attr2 = 'this is PyClass.attr2'
            attr3 = 'this is PyClass.attr3'

            def foo(self):
                return 'this is PyClass.foo'

            @classmethod
            def cFoo(cls):
                return 'this is PyClass.cFoo'

            @staticmethod
            def sFoo():
                return 'this is PyClass.sFoo'

        class MixIn1:
            attr3 = 'this is MixIn1.attr3'
            attr4 = 'this is MixIn1.attr4'

            def foo(self):
                return 'this is MixIn1.foo'

            @classmethod
            def cFoo(cls):
                return 'this is MixIn1.cFoo'

            @staticmethod
            def sFoo():
                return 'this is MixIn1.sFoo'

        class MixIn2Base:
            attr5 = 'this is MixIn2Base.attr5'

            def bar(self):
                return 'this is MixIn2Base.bar'

            def baz(self):
                return 'this is MixIn2Base.baz'

        class MixIn2(MixIn2Base):
            attr5 = 'this is MixIn2.attr5'
            attr6 = 'this is MixIn2.attr6'

            def bar(self):
                return 'this is MixIn2.bar'

        self.base = Base
        self.pyClass = PyClass
        self.mixIn1 = MixIn1
        self.mixIn2Base = MixIn2Base
        self.mixIn2 = MixIn2

    def testMixInSameAsClass(self):
        self.assertRaisesRegex(
            TypeError, 'mixInClass is the same as pyClass',
            MixIn, self.pyClass, self.pyClass)

    # pylint: disable=no-member

    def testMakeAncestor1(self):
        cls = MixIn(self.pyClass, self.mixIn1, makeAncestor=True)
        self.assertEqual(cls.__bases__, (self.mixIn1, self.base))
        self.assertFalse(hasattr(cls, 'mixInsForPyClass'))
        self.assertFalse(hasattr(self.mixIn1, 'mixInSuperFoo'))
        self.assertEqual(cls.attr0, 'this is Base.attr0')
        self.assertEqual(cls.attr1, 'this is PyClass.attr1')
        self.assertEqual(cls.attr2, 'this is PyClass.attr2')
        self.assertEqual(cls.attr3, 'this is PyClass.attr3')
        self.assertEqual(cls.attr4, 'this is MixIn1.attr4')
        self.assertEqual(cls.cFoo(), 'this is PyClass.cFoo')
        self.assertEqual(cls.sFoo(), 'this is PyClass.sFoo')
        obj = cls()
        self.assertEqual(obj.foo(), 'this is PyClass.foo')

    def testMakeAncestor2(self):
        cls = MixIn(self.pyClass, self.mixIn2, makeAncestor=True)
        self.assertEqual(cls.__bases__, (self.mixIn2, self.base))
        self.assertFalse(hasattr(cls, 'mixInsForPyClass'))
        self.assertFalse(hasattr(self.mixIn2, 'mixInSuperFoo'))
        self.assertEqual(cls.attr0, 'this is Base.attr0')
        self.assertEqual(cls.attr1, 'this is PyClass.attr1')
        self.assertEqual(cls.attr2, 'this is PyClass.attr2')
        self.assertEqual(cls.attr3, 'this is PyClass.attr3')
        self.assertEqual(cls.attr5, 'this is MixIn2.attr5')
        self.assertEqual(cls.attr6, 'this is MixIn2.attr6')
        self.assertEqual(cls.cFoo(), 'this is PyClass.cFoo')
        self.assertEqual(cls.sFoo(), 'this is PyClass.sFoo')
        obj = cls()
        self.assertEqual(obj.foo(), 'this is PyClass.foo')
        self.assertEqual(obj.bar(), 'this is MixIn2.bar')
        self.assertEqual(obj.baz(), 'this is MixIn2Base.baz')

    def testMixIn1(self):
        cls = self.pyClass
        MixIn(cls, self.mixIn1)
        self.assertEqual(cls.__bases__, (self.base,))
        self.assertEqual(cls.mixInsForPyClass, [self.mixIn1])
        self.assertFalse(hasattr(self.mixIn1, 'mixInSuperFoo'))
        self.assertEqual(cls.attr0, 'this is Base.attr0')
        self.assertEqual(cls.attr1, 'this is PyClass.attr1')
        self.assertEqual(cls.attr2, 'this is PyClass.attr2')
        self.assertEqual(cls.attr3, 'this is MixIn1.attr3')
        self.assertEqual(cls.attr4, 'this is MixIn1.attr4')
        self.assertEqual(cls.cFoo(), 'this is MixIn1.cFoo')
        self.assertEqual(cls.sFoo(), 'this is MixIn1.sFoo')
        obj = cls()
        self.assertEqual(obj.foo(), 'this is MixIn1.foo')

    def testMixIn2(self):
        cls = self.pyClass
        MixIn(cls, self.mixIn2)
        self.assertEqual(cls.__bases__, (self.base,))
        self.assertEqual(cls.mixInsForPyClass, [self.mixIn2Base, self.mixIn2])
        self.assertFalse(hasattr(self.mixIn2, 'mixInSuperFoo'))
        self.assertEqual(cls.attr0, 'this is Base.attr0')
        self.assertEqual(cls.attr1, 'this is PyClass.attr1')
        self.assertEqual(cls.attr2, 'this is PyClass.attr2')
        self.assertEqual(cls.attr3, 'this is PyClass.attr3')
        self.assertEqual(cls.attr5, 'this is MixIn2.attr5')
        self.assertEqual(cls.attr6, 'this is MixIn2.attr6')
        self.assertEqual(cls.cFoo(), 'this is PyClass.cFoo')
        self.assertEqual(cls.sFoo(), 'this is PyClass.sFoo')
        obj = cls()
        self.assertEqual(obj.foo(), 'this is PyClass.foo')
        self.assertEqual(obj.bar(), 'this is MixIn2.bar')
        self.assertEqual(obj.baz(), 'this is MixIn2Base.baz')

    def testMixIn1And2(self):
        cls = self.pyClass
        MixIn(cls, self.mixIn1)
        MixIn(cls, self.mixIn2)
        self.assertEqual(cls.__bases__, (self.base,))
        self.assertEqual(cls.mixInsForPyClass, [
            self.mixIn1, self.mixIn2Base, self.mixIn2])
        self.assertFalse(hasattr(self.mixIn1, 'mixInSuperFoo'))
        self.assertFalse(hasattr(self.mixIn2, 'mixInSuperFoo'))
        self.assertEqual(cls.attr0, 'this is Base.attr0')
        self.assertEqual(cls.attr1, 'this is PyClass.attr1')
        self.assertEqual(cls.attr2, 'this is PyClass.attr2')
        self.assertEqual(cls.attr3, 'this is MixIn1.attr3')
        self.assertEqual(cls.attr4, 'this is MixIn1.attr4')
        self.assertEqual(cls.attr5, 'this is MixIn2.attr5')
        self.assertEqual(cls.attr6, 'this is MixIn2.attr6')
        self.assertEqual(cls.cFoo(), 'this is MixIn1.cFoo')
        self.assertEqual(cls.sFoo(), 'this is MixIn1.sFoo')
        obj = cls()
        self.assertEqual(obj.foo(), 'this is MixIn1.foo')
        self.assertEqual(obj.bar(), 'this is MixIn2.bar')
        self.assertEqual(obj.baz(), 'this is MixIn2Base.baz')

    def testMixIn1WithSuper(self):
        cls, mixIn = self.pyClass, self.mixIn1
        MixIn(cls, mixIn, mixInSuperMethods=True)
        self.assertEqual(cls.__bases__, (self.base,))
        self.assertEqual(cls.mixInsForPyClass, [mixIn])
        self.assertTrue(hasattr(mixIn, 'mixInSuperFoo'))
        self.assertTrue(hasattr(mixIn, 'mixInSuperCFoo'))
        self.assertTrue(hasattr(mixIn, 'mixInSuperSFoo'))
        self.assertEqual(cls.attr0, 'this is Base.attr0')
        self.assertEqual(cls.attr1, 'this is PyClass.attr1')
        self.assertEqual(cls.attr2, 'this is PyClass.attr2')
        self.assertEqual(cls.attr3, 'this is MixIn1.attr3')
        self.assertEqual(cls.attr4, 'this is MixIn1.attr4')
        self.assertEqual(cls.cFoo(), 'this is MixIn1.cFoo')
        self.assertEqual(cls.sFoo(), 'this is MixIn1.sFoo')
        self.assertEqual(mixIn.mixInSuperCFoo(), 'this is PyClass.cFoo')
        self.assertEqual(mixIn.mixInSuperSFoo(), 'this is PyClass.sFoo')
        obj = cls()
        self.assertEqual(obj.foo(), 'this is MixIn1.foo')
        superFoo = mixIn.mixInSuperFoo
        self.assertEqual(superFoo(self), 'this is PyClass.foo')

    def testMixIn2WithSuper(self):
        cls, mixIn = self.pyClass, self.mixIn2
        MixIn(cls, mixIn, mixInSuperMethods=True)
        self.assertEqual(cls.__bases__, (self.base,))
        self.assertEqual(cls.mixInsForPyClass, [self.mixIn2Base, mixIn])
        self.assertFalse(hasattr(mixIn, 'mixInSuperFoo'))
        self.assertFalse(hasattr(mixIn, 'mixInSuperCFoo'))
        self.assertFalse(hasattr(mixIn, 'mixInSuperSFoo'))
        self.assertEqual(cls.attr0, 'this is Base.attr0')
        self.assertEqual(cls.attr1, 'this is PyClass.attr1')
        self.assertEqual(cls.attr2, 'this is PyClass.attr2')
        self.assertEqual(cls.attr3, 'this is PyClass.attr3')
        self.assertEqual(cls.attr5, 'this is MixIn2.attr5')
        self.assertEqual(cls.attr6, 'this is MixIn2.attr6')
        self.assertEqual(cls.cFoo(), 'this is PyClass.cFoo')
        self.assertEqual(cls.sFoo(), 'this is PyClass.sFoo')
        obj = cls()
        self.assertEqual(obj.foo(), 'this is PyClass.foo')
        self.assertEqual(obj.bar(), 'this is MixIn2.bar')
        self.assertEqual(obj.baz(), 'this is MixIn2Base.baz')
