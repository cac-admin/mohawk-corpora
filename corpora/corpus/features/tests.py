# -*- coding: utf-8 -*-
# these tests don't use Django's test framework and can be run in its absence.
from __future__ import print_function
import unittest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import features

GREEN    = "\033[01;32m"
RED      = "\033[01;31m"
YELLOW   = "\033[01;33m"
C_NORMAL = "\033[00m"

def format_features(c):
    a = []
    colours = ['', RED, YELLOW, GREEN]

    for k, v in c.most_common():
        #a.append(' %s%s' % (colours[len(k)], k))
        if (v > 1):
            k = '%s*%d' % (k, v)
        a.append(k)
    return ', '.join(a).encode('utf8')


class TestFeaturesImport(unittest.TestCase):
    def test_mi_import_success(self):
        f = features.import_finder('mi')
        for s, answer in [
                ("nananananananānānanana na",
                 "na*12, n*12, a*10, ana*10, an*10, nan*8, ā*2, aa*2, "
                 "naa*2, aan*2,  "),
                ("ko wai au?", " *2, wa, ä, ȧ, ai, k, ko, o, wai, au, w"),
                ("", ""),
                ("e", "e"),
                ("E ahu pēhea ana koe?! @#@!$#@%$#^ AUE",
                 " *5, a*4, e*3, h*2, eh, ee, ah, ea, an, ē, au, ahu, ana, "
                 "aue, na, koe, ehe, hea, pe, pee, hu, œ, he, ä, k, ko, "
                 "n, p, u, eeh, ue, oe"),
                ("ko Mare tōku ingoa",
                 " *3, a*2, k*2, o*2, ŋoa, ko, ŋo, ar, are, re, to, iŋ, too, "
                 "oo, mar, oku, ma, ŋ, ō, ook, ok, oa, e, i, m, r, u, t, "
                 "ku, iŋo"),
                ("ko Iha tōku ingoa 123", ""),
                ("aeiouāēīōū hīkōmānūngīpērītēwāwhī",
                 "ii*5, ī*5, ā*3, ee*3, aa*3, ē*3, ei*2, ō*2, oo*2, ou*2, "
                 "uu*2, ae*2, io*2, ū*2, ite,  , te, ŋ, ŋi, uŋ, hii, h, eew, "
                 "eer, p, eei, t, aei, aee, oua, nuu, tee, ew, ouu, er, ŋii, "
                 "pee, ri, oma, wa, iko, ioo, om, k, w, fii, ipe, koo, waa, "
                 "pe, iit, iip, oom, oou, hi, iio, iik, aae, aaf, ma, f, aan, "
                 "ik, n, r, eii, ua, eri, eio, uŋi, af, ip, it, an, anu, rii, "
                 "uaa, afi, ė, nu, iou, m, maa, fi, a, ko, uuŋ, ö, ewa"),
        ]:
            c = f(s)
            self.assertEqual(format_features(c), answer)

    def test_mi_import_fail(self):
        f = features.import_finder('mi')
        for s in ['esdf velifont', # bad bad bad
                  'ko Mare [Murray] tōku ingoa', # bad word (Murray)
                  'ko Murray tōku ingoa', # bad word (Murray)
                  'ko Iha tōku ing', # bad word ending ("ing").
        ]:
            c = f(s)
            if c:
                cc = format_features(c)
                self.fail("incorrectly parsed %s: %s" % (s, cc))


    def test_missing_import(self):
        f = features.import_finder('missing')



if __name__ == '__main__':
    unittest.main()
