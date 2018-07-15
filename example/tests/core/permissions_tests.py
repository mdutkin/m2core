__author__ = 'Maxim Dutkin (max@dutkin.ru)'


import unittest
from m2core import M2Core
from m2core.common import Permission, And, Or, Not, PermissionsEnum
from m2core.data_schemes.db_system_scheme import M2PermissionCheckMixin


class User(M2PermissionCheckMixin):
    def __init__(self, permissions: set):
        self.permissions = permissions


class PermissionsTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

        m2core = M2Core()
        m2core.run_for_test()

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
        
        self.pp1 = PlatformPerms
        self.pp2 = AnotherPlatformPerms

        self.sample_set = [
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
        perm = self.pp1.Perm1 & self.pp1.Perm2 & self.pp1.Perm3 & self.pp1.Perm4
        user = User({self.pp1.Perm1, self.pp1.Perm2, self.pp1.Perm3, self.pp1.Perm4})
        self.assertEqual(type(perm.rule_chain), And)
        self.assertEqual(len(perm.rule_chain), 4)
        self.assertTrue(user.can(perm))

    def test_or(self):
        perm = self.pp1.Perm1 | self.pp1.Perm2 | self.pp1.Perm3 | self.pp1.Perm4
        user = User({self.pp1.Perm10, self.pp1.Perm12, self.pp1.Perm13, self.pp1.Perm4})
        self.assertEqual(type(perm.rule_chain), Or)
        self.assertEqual(len(perm.rule_chain), 4)
        self.assertTrue(user.can(perm))

    def test_not(self):
        perm = ~(self.pp1.Perm1 & self.pp1.Perm2 & self.pp1.Perm3 & self.pp1.Perm4)
        user = User({self.pp1.Perm11, self.pp1.Perm12, self.pp1.Perm13, self.pp1.Perm14})
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
        result = self.pp1.ALL
        expected_result = {
            self.pp1.AUTHORIZED,
            self.pp1.Perm1,
            self.pp1.Perm2,
            self.pp1.Perm3,
            self.pp1.Perm4,
            self.pp1.Perm5,
            self.pp1.Perm6,
            self.pp1.Perm7,
            self.pp1.Perm8,
            self.pp1.Perm9,
            self.pp1.Perm10,
            self.pp1.Perm11,
            self.pp1.Perm12,
            self.pp1.Perm13,
            self.pp1.Perm14,
            self.pp1.Perm15,
            self.pp1.Perm16,
            self.pp1.Perm17,
        }
        self.assertEqual(expected_result, result)

    def test_all_across_instances(self):
        result = self.pp1.all_platform_permissions
        expected_result = {
            self.pp1.AUTHORIZED,
            self.pp1.Perm1,
            self.pp1.Perm2,
            self.pp1.Perm3,
            self.pp1.Perm4,
            self.pp1.Perm5,
            self.pp1.Perm6,
            self.pp1.Perm7,
            self.pp1.Perm8,
            self.pp1.Perm9,
            self.pp1.Perm10,
            self.pp1.Perm11,
            self.pp1.Perm12,
            self.pp1.Perm13,
            self.pp1.Perm14,
            self.pp1.Perm15,
            self.pp1.Perm16,
            self.pp1.Perm17,
            self.pp2.Perm18,
            self.pp2.Perm19,
            self.pp2.Perm20,
            self.pp2.Perm21,
            self.pp2.Perm22,
        }
        self.assertEqual(expected_result, result)

