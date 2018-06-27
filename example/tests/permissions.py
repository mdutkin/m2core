__author__ = 'Maxim Dutkin (max@dutkin.ru)'


import unittest
import os
from m2core import M2Core
from m2core.common import Permission, And, Or, Not, PermissionsEnum
from m2core.data_schemes.db_system_scheme import M2PermissionCheckMixin
from tornado.options import options


options.config_name = os.getenv('TEST_CONFIG', '../config_local.py')

m2core = M2Core()
app = m2core.run_for_test()


class PlatformPerms(PermissionsEnum):
    Perm1 = Permission('perm 1')
    Perm2 = Permission('perm 2')
    Perm3 = Permission('perm 3')
    Perm4 = Permission('perm 4')
    Perm5 = Permission('perm 5')
    Perm6 = Permission('perm 6')
    Perm7 = Permission('perm 7')
    Perm8 = Permission('perm 8')
    Perm9 = Permission('perm 9')
    Perm10 = Permission('perm 10')
    Perm11 = Permission('perm 11')
    Perm12 = Permission('perm 12')
    Perm13 = Permission('perm 13')
    Perm14 = Permission('perm 14')
    Perm15 = Permission('perm 15')
    Perm16 = Permission('perm 16')
    Perm17 = Permission('perm 17')


class AnotherPlatformPerms(PermissionsEnum):
    Perm18 = Permission('perm 18')
    Perm19 = Permission('perm 19')
    Perm20 = Permission('perm 20')
    Perm21 = Permission('perm 21')
    Perm22 = Permission('perm 22')


class User(M2PermissionCheckMixin):
    def __init__(self, permissions: set):
        self.permissions = permissions


class PermissionsTest(unittest.TestCase):
    sample_set = [
        (
            # 0
            PlatformPerms.Perm1 & PlatformPerms.Perm2 & PlatformPerms.Perm3 |
            PlatformPerms.Perm4 & PlatformPerms.Perm5 & PlatformPerms.Perm6 |
            PlatformPerms.Perm7 & PlatformPerms.Perm8 & PlatformPerms.Perm9 |
            PlatformPerms.Perm10 | PlatformPerms.Perm11 | PlatformPerms.Perm12,
            Or(
                And(PlatformPerms.Perm1, PlatformPerms.Perm2, PlatformPerms.Perm3),
                And(PlatformPerms.Perm4, PlatformPerms.Perm5, PlatformPerms.Perm6),
                And(PlatformPerms.Perm7, PlatformPerms.Perm8, PlatformPerms.Perm9),
                PlatformPerms.Perm10,
                PlatformPerms.Perm11,
                PlatformPerms.Perm12
            ),
            {PlatformPerms.Perm12},
            {PlatformPerms.Perm1, PlatformPerms.Perm2, PlatformPerms.Perm4,
             PlatformPerms.Perm6, PlatformPerms.Perm7, PlatformPerms.Perm8,
             PlatformPerms.Perm13}
        ),
        (
            # 1
            (~PlatformPerms.Perm1 & ~PlatformPerms.Perm2 & PlatformPerms.Perm3) |
            (~PlatformPerms.Perm4 & ~PlatformPerms.Perm5 & PlatformPerms.Perm6) |
            (~PlatformPerms.Perm7 & ~PlatformPerms.Perm8 & PlatformPerms.Perm9) |
            PlatformPerms.Perm10 | PlatformPerms.Perm11 | PlatformPerms.Perm12,
            Or(
                And(Not(PlatformPerms.Perm1), Not(PlatformPerms.Perm2), PlatformPerms.Perm3),
                And(Not(PlatformPerms.Perm4), Not(PlatformPerms.Perm5), PlatformPerms.Perm6),
                And(Not(PlatformPerms.Perm7), Not(PlatformPerms.Perm8), PlatformPerms.Perm9),
                PlatformPerms.Perm10,
                PlatformPerms.Perm11,
                PlatformPerms.Perm12
            ),
            {PlatformPerms.Perm3, PlatformPerms.Perm6},
            {PlatformPerms.Perm1, PlatformPerms.Perm2, PlatformPerms.Perm4,
             PlatformPerms.Perm6, PlatformPerms.Perm7, PlatformPerms.Perm8,
             PlatformPerms.Perm13}
        ),
        (
            # 2
            PlatformPerms.Perm1 & PlatformPerms.Perm2 & PlatformPerms.Perm3 |
            PlatformPerms.Perm4 & ~PlatformPerms.Perm5 & PlatformPerms.Perm6 |
            PlatformPerms.Perm7 & PlatformPerms.Perm8 & PlatformPerms.Perm9 |
            PlatformPerms.Perm10 | ~PlatformPerms.Perm11 | PlatformPerms.Perm12,
            Or(
                And(PlatformPerms.Perm1, PlatformPerms.Perm2, PlatformPerms.Perm3),
                And(PlatformPerms.Perm4, Not(PlatformPerms.Perm5), PlatformPerms.Perm6),
                And(PlatformPerms.Perm7, PlatformPerms.Perm8, PlatformPerms.Perm9),
                PlatformPerms.Perm10,
                Not(PlatformPerms.Perm11),
                PlatformPerms.Perm12
            ),
            {PlatformPerms.Perm4, PlatformPerms.Perm6},
            {PlatformPerms.Perm4, PlatformPerms.Perm5, PlatformPerms.Perm6, PlatformPerms.Perm11}
        ),
        (
            # 3
            ~(PlatformPerms.Perm1 & PlatformPerms.Perm2),
            Not(
                And(PlatformPerms.Perm1, PlatformPerms.Perm2)
            ),
            {PlatformPerms.Perm1},
            {PlatformPerms.Perm1, PlatformPerms.Perm2}
        ),
        (
            # 4
            ~PlatformPerms.Perm1,
            Not(PlatformPerms.Perm1),
            {PlatformPerms.Perm2, PlatformPerms.Perm3},
            {PlatformPerms.Perm1, PlatformPerms.Perm2, PlatformPerms.Perm3}
        ),
        (
            # 5
            ~((PlatformPerms.Perm1 | ~PlatformPerms.Perm2) &
              (~PlatformPerms.Perm3 | PlatformPerms.Perm4) &
              (PlatformPerms.Perm5 | ~PlatformPerms.Perm6)),
            Not(
                And(
                    Or(PlatformPerms.Perm1, Not(PlatformPerms.Perm2)),
                    Or(Not(PlatformPerms.Perm3), PlatformPerms.Perm4),
                    Or(PlatformPerms.Perm5, Not(PlatformPerms.Perm6)),
                )
            ),
            {PlatformPerms.Perm2, PlatformPerms.Perm3, PlatformPerms.Perm6},
            {PlatformPerms.Perm1, PlatformPerms.Perm2, PlatformPerms.Perm5, PlatformPerms.Perm6}
        )
    ]

    def setUp(self):
        self.maxDiff = None

    def test_constructions(self):
        for num, (sample, right_result, true_perm_set, false_perm_set) in enumerate(self.sample_set):
            self.assertEqual(
                repr(sample.rule_chain),
                repr(right_result),
                msg=f'Error in {num} sample'
            )

    def test_user_can(self):
        for num, (sample, right_result, true_perm_set, false_perm_set) in enumerate(self.sample_set):
            user = User(true_perm_set)
            self.assertTrue(
                user.can(sample),
                msg=f'Error in {num} sample'
            )

    def test_user_can_not(self):
        for num, (sample, right_result, true_perm_set, false_perm_set) in enumerate(self.sample_set):
            user = User(false_perm_set)
            self.assertFalse(
                user.can(sample),
                msg=f'Error in {num} sample'
            )

    def test_and(self):
        perm = PlatformPerms.Perm1 & PlatformPerms.Perm2 & PlatformPerms.Perm3 & PlatformPerms.Perm4
        user = User({PlatformPerms.Perm1, PlatformPerms.Perm2, PlatformPerms.Perm3, PlatformPerms.Perm4})
        self.assertEqual(type(perm.rule_chain), And)
        self.assertEqual(len(perm.rule_chain), 4)
        self.assertTrue(user.can(perm))

    def test_or(self):
        perm = PlatformPerms.Perm1 | PlatformPerms.Perm2 | PlatformPerms.Perm3 | PlatformPerms.Perm4
        user = User({PlatformPerms.Perm10, PlatformPerms.Perm12, PlatformPerms.Perm13, PlatformPerms.Perm4})
        self.assertEqual(type(perm.rule_chain), Or)
        self.assertEqual(len(perm.rule_chain), 4)
        self.assertTrue(user.can(perm))

    def test_not(self):
        perm = ~(PlatformPerms.Perm1 & PlatformPerms.Perm2 & PlatformPerms.Perm3 & PlatformPerms.Perm4)
        user = User({PlatformPerms.Perm11, PlatformPerms.Perm12, PlatformPerms.Perm13, PlatformPerms.Perm14})
        self.assertEqual(type(perm.rule_chain), Not)
        self.assertEqual(len(perm.rule_chain), 1)
        self.assertEqual(type(perm.rule_chain[0]), And)
        self.assertTrue(user.can(perm))

    def test_permission_properties(self):
        with self.assertRaises(AttributeError):
            Permission()
            Permission(None)
            Permission('')

        name = 'permission 1'
        sys_name = 'PERMISSION_1'
        custom_sys_name = 'COOL_PERMISSION_____1'
        p = Permission(name)
        self.assertEqual(p.name, name)
        p = Permission(name, None)
        self.assertEqual(p.sys_name, sys_name)
        p = Permission(name, sys_name)
        self.assertEqual(p.sys_name, sys_name)
        p = Permission(name, custom_sys_name)
        self.assertEqual(p.sys_name, custom_sys_name)

    def test_permissions_enum_all(self):
        result = PlatformPerms.ALL
        expected_result = {
            PlatformPerms.AUTHORIZED,
            PlatformPerms.Perm1,
            PlatformPerms.Perm2,
            PlatformPerms.Perm3,
            PlatformPerms.Perm4,
            PlatformPerms.Perm5,
            PlatformPerms.Perm6,
            PlatformPerms.Perm7,
            PlatformPerms.Perm8,
            PlatformPerms.Perm9,
            PlatformPerms.Perm10,
            PlatformPerms.Perm11,
            PlatformPerms.Perm12,
            PlatformPerms.Perm13,
            PlatformPerms.Perm14,
            PlatformPerms.Perm15,
            PlatformPerms.Perm16,
            PlatformPerms.Perm17,
        }
        self.assertEqual(expected_result, result)

    def test_all_across_instances(self):
        result = PlatformPerms.all_platform_instances
        expected_result = {
            PlatformPerms.AUTHORIZED,
            PlatformPerms.Perm1,
            PlatformPerms.Perm2,
            PlatformPerms.Perm3,
            PlatformPerms.Perm4,
            PlatformPerms.Perm5,
            PlatformPerms.Perm6,
            PlatformPerms.Perm7,
            PlatformPerms.Perm8,
            PlatformPerms.Perm9,
            PlatformPerms.Perm10,
            PlatformPerms.Perm11,
            PlatformPerms.Perm12,
            PlatformPerms.Perm13,
            PlatformPerms.Perm14,
            PlatformPerms.Perm15,
            PlatformPerms.Perm16,
            PlatformPerms.Perm17,
            AnotherPlatformPerms.Perm18,
            AnotherPlatformPerms.Perm19,
            AnotherPlatformPerms.Perm20,
            AnotherPlatformPerms.Perm21,
            AnotherPlatformPerms.Perm22,
        }
        self.assertEqual(expected_result, result)

