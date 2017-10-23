from importlib import import_module

def default_feature_finder(x):
    # rely only on the set of characters.
    return set


def import_finder(lang):
    if lang.isalpha():
        try:
            m = import_module('features.%s' % lang)
            return m.find_features
        except ImportError as e:
            print >> sys.stderr, "lang %s is not known" % lang
            return default_feature_finder
        except AttributeError as e:
            print >> sys.stderr, "'%s' has no find_features method" % lang
            return default_feature_finder
