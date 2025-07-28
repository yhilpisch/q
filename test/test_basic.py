#!/usr/bin/env python
# vim: set ts=4 sw=4 et sts=4 ai:
#
# Test some basic functionality.
#

import os
import re
import sys
import unittest

qpath = os.path.abspath(os.path.join(os.path.split(__file__)[0], '..'))
sys.path.insert(0, qpath)
import q
Q_PATH = q.OUTPUT_PATH


class TestQBasic(unittest.TestCase):

    def setUp(self):
        if os.path.exists(Q_PATH):
            os.remove(Q_PATH)

    def tearDown(self):
        self.setUp()

    def assertInQLog(self, string):
        # Check the log file exists.
        self.assertTrue(os.path.exists(Q_PATH))

        # Read in the data.
        f = open(Q_PATH, 'r')
        logdata = f.read()
        f.close()

        # Check the string is found in the log file.
        # We can't use self.assertRegexpMatches as we need re.DOTALL
        expected_regexp = re.compile('.*%s.*' % string, re.DOTALL)
        if not expected_regexp.search(logdata):
            msg = '%s: %r not found in\n%s\n%s\n%s' % (
                "Regexp didn't match",
                expected_regexp.pattern,
                "-"*75,
                logdata,
                "-"*75,
                )
            raise self.failureException(msg)

    def test_q_log_message(self):
        import q
        q.q('Test message')
        self.assertInQLog('Test message')

    def test_q_function_call(self):
        import q

        @q.t
        def test(arg):
            return 'RetVal'

        self.assertEqual('RetVal', test('ArgVal'))

        self.assertInQLog('ArgVal')
        self.assertInQLog('RetVal')

    def test_q_argument_order_arguments(self):
        import q
        q.writer.color = False

        class A:
            def __init__(self, two, three, four):
                q(two, three, four)

        A("ArgVal1", "ArgVal2", "ArgVal3")
        self.assertInQLog(".*".join([
            "__init__:",
            "two='ArgVal1'",
            "three='ArgVal2'",
            "four='ArgVal3'",
            ]))

    def test_q_argument_order_attributes1(self):
        import q
        q.writer.color = False

        class A:
            def __init__(self, two, three, four):
                self.attrib1 = 'Attrib1'
                self.attrib2 = 'Attrib2'
                q(self.attrib1, self.attrib2)

        A("ArgVal1", "ArgVal2", "ArgVal3")
        self.assertInQLog(".*".join([
            "__init__:",
            "self.attrib1='Attrib1',",
            "self.attrib2='Attrib2'",
            ]))

    def test_q_argument_order_attributes2(self):
        import q
        q.writer.color = False

        class A:
            def __init__(s, two, three, four):
                s.attrib1 = 'Attrib1'
                s.attrib2 = 'Attrib2'
                q(s.attrib1, s.attrib2)

        A("ArgVal1", "ArgVal2", "ArgVal3")
        self.assertInQLog(".*".join([
            "__init__:",
            "s.attrib1='Attrib1',",
            "s.attrib2='Attrib2'",
            ]))

    @unittest.skipIf(sys.version_info < (3, 8), "requires Python 3.8+")
    def test_q_multiple_calls_on_line(self):
        import q
        q.writer.color = False

        class A:
            def __init__(self, two, three, four):
                self.attrib1 = 'Attrib1'
                self.attrib2 = 'Attrib2'
                q(q(two, self.attrib1) + q(three, self.attrib2), four)

        A("ArgVal1", "ArgVal2", "ArgVal3")
        self.assertInQLog(".*".join([
            "__init__:",
            "two='ArgVal1',",
            "self.attrib1='Attrib1'",
            "__init__:",
            "three='ArgVal2',",
            "self.attrib2='Attrib2'",
            "__init__:",
            # `q(two, self.attrib1) + q(three, self.attrib2)='ArgVal1ArgVal2',`
            # does not work despite that text being in the log, so just test
            # for `'ArgVal1ArgVal2',`
            "'ArgVal1ArgVal2',",
            "four='ArgVal3'",
            ]))

    def test_q_argument_order_attributes_and_arguments(self):
        import q
        q.writer.color = False

        class A:
            def __init__(self, two, three, four):
                self.attrib1 = 'Attrib1'
                self.attrib2 = 'Attrib2'
                q(two, three, self.attrib1, four, self.attrib2)

        A("ArgVal1", "ArgVal2", "ArgVal3")
        self.assertInQLog(".*".join([
            "__init__:",
            "two='ArgVal1'",
            "three='ArgVal2'",
            "self.attrib1='Attrib1'",
            "four='ArgVal3'",
            "self.attrib2='Attrib2'",
        ]))

    def test_q_trace(self):
        import q
        q.writer.color = False

        @q
        def log1(msg='default'):
            return msg

        @q.t
        def log2(msg='default'):
            return msg

        log1('log1 message')
        log2('log2 message')

        self.assertInQLog("log1\\('log1 message'\\)")
        self.assertInQLog("log2\\('log2 message'\\)")

    def test_q_nested_bad_wrapper(self):
        # See http://micheles.googlecode.com/hg/decorator/documentation.html#statement-of-the-problem # noqa
        import q
        q.writer.color = False

        def wrapper(func):
            def do_nothing(*args, **kwargs):
                return func(*args, **kwargs)
            return do_nothing

        @wrapper
        @q
        @wrapper
        def decorated_log_bad(msg='default'):
            return msg

        decorated_log_bad('decorated bad message')
        self.assertInQLog(r"do_nothing\((?:\n\s*)?'"
                          r"decorated bad message'\)")
        self.assertInQLog("-> 'decorated bad message'")

    def test_q_nested_good_wrappers(self):
        import q
        q.writer.color = False

        import functools

        def wrapper(func):
            def do_nothing(*args, **kwargs):
                return func(*args, **kwargs)
            return functools.update_wrapper(do_nothing, func)

        @wrapper
        @q
        @wrapper
        def decorated_log_good(msg='default'):
            return msg

        decorated_log_good('decorated good message')
        self.assertInQLog(r"decorated_log_good\((?:\n\s*)?'"
                          r"decorated good message'\)")
        self.assertInQLog("-> 'decorated good message'")

    @unittest.skipIf(sys.version_info < (3, 3), "requires Python 3.3+")
    def test_q_trace_method(self):
        import q
        q.writer.color = False

        class A(object):
            @q
            def run1(self, arg):
                return arg

            @staticmethod
            @q
            def run2(arg):
                return arg

            @classmethod
            @q
            def run3(cls, arg):
                return arg

        a = A()
        a.run1('first message')
        A.run2('second message')
        A.run3('third message')

        self.assertInQLog(".*".join([
            "\\bA.run1\\(",
            "'first message'\\)",
        ]))
        self.assertInQLog("-> 'first message'")

        self.assertInQLog(".*".join([
            "\\bA.run2\\(",
            "'second message'\\)",
        ]))
        self.assertInQLog("-> 'second message'")

        self.assertInQLog(".*".join([
            "\\bA.run3\\(",
            "'third message'\\)",
        ]))
        self.assertInQLog("-> 'third message'")


unittest.main()
