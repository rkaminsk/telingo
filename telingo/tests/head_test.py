import unittest
import sys
import clingo
import telingo
from telingo.transformers import head as th

class TestCase(unittest.TestCase):
    def assertRaisesRegex(self, *args, **kwargs):
        return (self.assertRaisesRegexp(*args, **kwargs)
            if sys.version_info[0] < 3
            else unittest.TestCase.assertRaisesRegex(self, *args, **kwargs))

def parse_formula(s):
    ret = []
    prg = clingo.Control(message_limit=0)
    clingo.parse_program("&tel{{{}}}.".format(s), ret.append)
    return ret[-1].head

def parse_atom(s):
    return parse_formula(s).elements[0].tuple[0]

def theory_term_to_tel_atom(s, positive=True):
    return str(th.theory_term_to_tel_atom(parse_atom(s), positive))

def tel_atom_to_theory_term(s, positive=True):
    return str(th.tel_atom_to_theory_term(th.theory_term_to_tel_atom(parse_atom(s)), positive))

def theory_atom_to_formula(s):
    return str(th.theory_atom_to_formula(parse_formula(s)))

def formula_to_theory_term(s):
    return str(th.formula_to_theory_term(th.theory_atom_to_formula(parse_formula(s))))

def formula_to_theory_atom(s):
    return str(th.theory_term_to_theory_atom(th.formula_to_theory_term(th.theory_atom_to_formula(parse_formula(s)))))

def shift_formula(s):
    f = th.theory_atom_to_formula(parse_formula(s))
    aux = th.TelAtom(f.location, True, "aux", [])
    f, r = th.shift_tel_formula(f, aux)
    return str(f), list(map(str, r))

class TestHead(TestCase):
    def test_atom(self):
        self.assertEqual(theory_term_to_tel_atom("a"), "a")
        self.assertEqual(theory_term_to_tel_atom("-a"), "-a")
        self.assertEqual(theory_term_to_tel_atom("- -a"), "a")
        self.assertEqual(theory_term_to_tel_atom("a", False), "-a")
        self.assertEqual(theory_term_to_tel_atom("-a", False), "a")
        self.assertEqual(theory_term_to_tel_atom("a(X)"), "a(X)")
        self.assertEqual(theory_term_to_tel_atom("a(X,x)"), "a(X,x)")
        self.assertEqual(theory_term_to_tel_atom("a(X,-x)"), "a(X,-x)")

        self.assertEqual(tel_atom_to_theory_term("a"), "a")
        self.assertEqual(tel_atom_to_theory_term("-a"), "-(a)")
        self.assertEqual(tel_atom_to_theory_term("- -a"), "a")
        self.assertEqual(tel_atom_to_theory_term("a", False), "-(a)")
        self.assertEqual(tel_atom_to_theory_term("-a", False), "a")
        self.assertEqual(tel_atom_to_theory_term("a(X)"), "a(X)")
        self.assertEqual(tel_atom_to_theory_term("a(X,x)"), "a(X,x)")
        self.assertEqual(tel_atom_to_theory_term("a(X,-x)"), "a(X,-(x))")

    def test_formula(self):
        self.assertEqual(theory_atom_to_formula(">a"), "(>a)")
        self.assertEqual(theory_atom_to_formula(">:a"), "(>:a)")
        self.assertEqual(theory_atom_to_formula("2>a"), "(2>a)")
        self.assertEqual(theory_atom_to_formula("(-2)>a"), "(-2>a)")
        self.assertEqual(theory_atom_to_formula("-2>a"), "(-2>a)")
        self.assertEqual(theory_atom_to_formula("a>?b"), "(a>?b)")
        self.assertEqual(theory_atom_to_formula("a>*b"), "(a>*b)")
        self.assertEqual(theory_atom_to_formula("~a"), "(~a)")
        self.assertEqual(theory_atom_to_formula("~ ~a"), "(~(~a))")
        self.assertEqual(theory_atom_to_formula("a & b"), "(a&b)")
        self.assertEqual(theory_atom_to_formula("a | b"), "(a|b)")
        self.assertEqual(theory_atom_to_formula("a ;> b"), "(a&(>b))")
        self.assertEqual(theory_atom_to_formula("a ;>: b"), "(a&(>:b))")
        self.assertEqual(theory_atom_to_formula("&true"), "&true")
        self.assertEqual(theory_atom_to_formula("&false"), "&false")
        self.assertEqual(theory_atom_to_formula("&final"), "__final")
        self.assertEqual(theory_atom_to_formula(">>a"), "(>*(__final|a))")

        self.assertEqual(formula_to_theory_term(">a"), ">(a)")
        self.assertEqual(formula_to_theory_term(">:a"), ">:(a)")
        self.assertEqual(formula_to_theory_term("2>a"), ">(2,a)")
        self.assertEqual(formula_to_theory_term("(-2)>a"), ">(-(2),a)")
        self.assertEqual(formula_to_theory_term("-2>a"), ">(-(2),a)")
        self.assertEqual(formula_to_theory_term("a>?b"), ">?(a,b)")
        self.assertEqual(formula_to_theory_term("a>*b"), ">*(a,b)")
        self.assertEqual(formula_to_theory_term("~a"), "~(a)")
        self.assertEqual(formula_to_theory_term("~ ~a"), "~(~(a))")
        self.assertEqual(formula_to_theory_term("a & b"), "&(a,b)")
        self.assertEqual(formula_to_theory_term("a | b"), "|(a,b)")
        self.assertEqual(formula_to_theory_term("a ;> b"), "&(a,>(b))")
        self.assertEqual(formula_to_theory_term("a ;>: b"), "&(a,>:(b))")
        self.assertEqual(formula_to_theory_term("&true"), "&(true)")
        self.assertEqual(formula_to_theory_term("&false"), "&(false)")
        self.assertEqual(formula_to_theory_term("&final"), "__final")
        self.assertEqual(formula_to_theory_term(">>a"), ">*(|(__final,a))")

        self.assertEqual(formula_to_theory_atom(">a"), "&tel { >(a) :  }")

    def test_variables(self):
        self.assertEqual(str(th.get_variables(parse_atom("p(X,Y) | a(X,Z)"))), "[X, Y, Z]")

    def test_shift(self):
        self.assertEqual(shift_formula("a"), ("a", []))
        l = '((1-__t)+__S)'
        self.assertEqual(shift_formula(">a"), ('(({l}>=0)&(a|({l}!=0))&({l}<=0))'.format(l=l), []))
        # TODO: test shifting of next and until