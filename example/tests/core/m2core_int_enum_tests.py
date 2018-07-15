__author__ = 'Maxim Dutkin (max@dutkin.ru)'


import unittest
from m2core.common.int_enum import M2CoreIntEnum


class M2CoreIntEnumTest(unittest.TestCase):
    def setUp(self):
        class SampleEnum(M2CoreIntEnum):
            ONE = 1
            TWO = 2
            THREE = 3
            FOUR = 4
            FIVE = 5
            SIX = 6
            SEVEN = 7
            EIGHT = 8
            NINE = 9
            TEN = 10
        
        self.sample_enum = SampleEnum
    
    def test_get_by_int(self):
        self.assertEqual(self.sample_enum.ONE, self.sample_enum.get(1))
        self.assertEqual(self.sample_enum.TWO, self.sample_enum.get(2))
        self.assertEqual(self.sample_enum.THREE, self.sample_enum.get(3))
        self.assertEqual(self.sample_enum.FOUR, self.sample_enum.get(4))
        self.assertEqual(self.sample_enum.FIVE, self.sample_enum.get(5))
        self.assertEqual(self.sample_enum.SIX, self.sample_enum.get(6))
        self.assertEqual(self.sample_enum.SEVEN, self.sample_enum.get(7))
        self.assertEqual(self.sample_enum.EIGHT, self.sample_enum.get(8))
        self.assertEqual(self.sample_enum.NINE, self.sample_enum.get(9))
        self.assertEqual(self.sample_enum.TEN, self.sample_enum.get(10))
        self.assertTrue(self.sample_enum.get(11) is None)
        self.assertTrue(self.sample_enum.get(-1) is None)

    def test_get_raises(self):
        with self.assertRaises(Exception):
            self.sample_enum.get(1.0)
        with self.assertRaises(Exception):
            self.sample_enum.get(1.1)
        with self.assertRaises(Exception):
            self.sample_enum.get(True)
        with self.assertRaises(Exception):
            self.sample_enum.get(object)

    def test_get_by_str(self):
        self.assertEqual(self.sample_enum.ONE, self.sample_enum.get('ONE'))
        self.assertEqual(self.sample_enum.TWO, self.sample_enum.get('TWO'))
        self.assertEqual(self.sample_enum.THREE, self.sample_enum.get('THREE'))
        self.assertEqual(self.sample_enum.FOUR, self.sample_enum.get('FOUR'))
        self.assertEqual(self.sample_enum.FIVE, self.sample_enum.get('FIVE'))
        self.assertEqual(self.sample_enum.SIX, self.sample_enum.get('SIX'))
        self.assertEqual(self.sample_enum.SEVEN, self.sample_enum.get('SEVEN'))
        self.assertEqual(self.sample_enum.EIGHT, self.sample_enum.get('EIGHT'))
        self.assertEqual(self.sample_enum.NINE, self.sample_enum.get('NINE'))
        self.assertEqual(self.sample_enum.TEN, self.sample_enum.get('TEN'))
        self.assertTrue(self.sample_enum.get('ELEVEN') is None)
        self.assertTrue(self.sample_enum.get('NON_EXISTENT_MEMBER') is None)

    def test_all(self):
        self.assertEqual([
            self.sample_enum.ONE,
            self.sample_enum.TWO,
            self.sample_enum.THREE,
            self.sample_enum.FOUR,
            self.sample_enum.FIVE,
            self.sample_enum.SIX,
            self.sample_enum.SEVEN,
            self.sample_enum.EIGHT,
            self.sample_enum.NINE,
            self.sample_enum.TEN,
        ], self.sample_enum.all())
