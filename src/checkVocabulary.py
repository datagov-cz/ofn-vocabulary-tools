from typing import List
from ofnBindings import DEFAULT_LANGUAGE
from ofnClasses import Term, Vocabulary


def checkVocabulary(vocabulary: Vocabulary):
    checkCycles(vocabulary)


def checkCycles(vocabulary: Vocabulary):
    for term in vocabulary.terms:
        trail: List[str] = [term._iri]
        stack: List[str] = [term._iri]
        while len(stack) > 0:
            iterIRI: str = stack.pop()
            try:
                iterTerm = next(
                    x for x in vocabulary.terms if x._iri == iterIRI)
                trail += set(iterTerm.subClassOf)
                stack += set(iterTerm.subClassOf)
                if len(trail) > len(set(trail)):
                    raise Exception(
                        "Byl nalezen cyklus nadřazených pojmů mezi následujícími pojmy: {}".format([next(x.name[DEFAULT_LANGUAGE] for x in vocabulary.terms if x._iri == y) for y in set(trail)]))
            except StopIteration:
                break
