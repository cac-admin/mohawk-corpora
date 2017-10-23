# Library functions for manipulating Māori text corpora.
# Copyright Douglas Bagnall <douglas@halo.gen.nz> GPLv3
import re
import unicodedata
import sys
from collections import Counter

DIPHTHONGS = {
    'ae': 'æ',
    'ai': 'ȧ',
    'ao': 'å',
    'au': 'ä',
    'oi': 'ȯ',
    'oe': 'œ',
    'ou': 'ö',
    'ei': 'ė',
    'eu': 'ë'
}


def debug(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def possible_n_grams(n, state='v'):
    """Estimate the number of possible n-grams, very roughly."""
    # let's assume there are two states, vowel and consonant.
    # vowels = 10     # a e i o u ā ē ī ō ū
    # consonants = 10 # h k m n ng p r t w wh
    if n <= 0:
        return 1

    total = 0
    if state == 'v':
        total += 10 * possible_n_grams(n - 1, 'c')
    total += 10 * possible_n_grams(n - 1, 'v')
    return total


def generate_n_grams(n, prefix, diphthongs, macrons):
    """Estimate the number of possible n-grams, very roughly."""
    # let's assume there are two states, vowel and consonant.
    if n <= 0:
        return [prefix]

    chars = 'aeiou'
    if diphthongs:
        chars += ''.join(DIPHTHONGS.values())

    if macrons:
        chars += 'āēīōū'

    if prefix == '' or prefix[-1] in chars:
        chars += 'fhkmnŋprtw'

    ngrams = []
    for c in chars:
        ngrams.extend(generate_n_grams(n - 1, prefix + c, diphthongs, macrons))
    return ngrams


has_bad_letter = re.compile('[^aeiouāēīōūfhkmnŋprtw ]').search
has_bad_cluster = re.compile(r'[fhkmnŋprtw][fhkmnŋprtw]').search
has_bad_end = re.compile(r'[^aeiouāēīōū ]\b').search


def has_english(text):
    if has_bad_letter(text) or has_bad_cluster(text) or has_bad_end(text):
        return True
    return False


def remove_english(text):
    words = text.split()
    good_words = []
    for word in words:
        if has_english(word):
            continue
        good_words.append(word)
    return ' '.join(good_words)


def normalise_text(text):
    text = unicodedata.normalize('NFC', text)
    text = text.lower()
    text = re.sub(r'[^\wāēōūī]+', ' ', text)
    text = re.sub(r'ng', 'ŋ', text)
    text = re.sub(r'wh', 'f', text)
    return text


def find_features(text, word_boundaries, trigram_mode):
    text = normalise_text(text)

    if has_english(text):
        return {}

    # count unigrams first (including diphthongs and macrons).
    features = Counter(mangle_text(text, diphthongs=True, macrons=True))

    text = mangle_text(text, diphthongs=False, macrons=False)
    words = text.split()
    is_vowel = set('aeiou').__contains__
    for word in words:
        if word_boundaries:
            word = '«%s»' % word
        if len(word) < 2:
            continue
        g2 = word[:2]
        features[g2] += 1
        for i in range(2, len(word)):
            g3 = g2 + word[i]
            g2 = g3[1:]
            features[g2] += 1

            if trigram_mode != 'none':
                if trigram_mode == 'all':
                    features[g3] += 1
                else:
                    for x, y in zip(g3, trigram_mode):
                        if y == 'v' and not is_vowel(x):
                            break
                    else:
                        features[g3] += 1

    return features


def mangle_text(text, diphthongs, macrons, no_english=True):
    if no_english:
        text = remove_english(text)
    if not macrons:
        text = demacronise(text)
    if diphthongs:
        for k, v in DIPHTHONGS.items():
            text = re.sub(k, v, text)
    return text


def denormalise_text(text):
    text = re.sub(r'ŋ', 'ng', text)
    text = re.sub(r'f', 'wh', text)
    for k, v in DIPHTHONGS.items():
        text = re.sub(v, k, text)
    return text


def demacronise(text):
    return (text
            .replace('ā', 'aa')
            .replace('ē', 'ee')
            .replace('ī', 'ii')
            .replace('ō', 'oo')
            .replace('ū', 'uu'))


def load_raw_text(filenames):
    raw = []
    for fn in filenames:
        f = open(fn)
        raw.append(f.read())
        f.close()
    return '\n\n'.join(raw)


def load_text(filenames, **kwargs):
    text = load_raw_text(filenames)
    text = normalise_text(text)
    text = mangle_text(text, **kwargs)
    return text


def partially_normalise_text(text):
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'\n\s*\n+', '. ', text)
    text = re.sub(r'\n\s*', ' ', text)
    return text
