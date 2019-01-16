import en_core_web_sm

NLP = en_core_web_sm.load()


def label_by_ner(words):
    if not isinstance(words, str):
        try:
            words = words.decode('utf-8')
        except UnicodeDecodeError:
            words = words.decode('gb18030')

    nlp_token = NLP(words)
    label = nlp_token.ents[0].label_ if nlp_token.ents else u'Unrecognized'
    return label


def is_person(name):
    return label_by_ner(name) == u'PERSON'


def is_org(name):
    return 3 <= len(name) <= 100 and label_by_ner(name) == u'ORG'
