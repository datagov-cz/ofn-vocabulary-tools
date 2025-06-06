from typing import List
from ofnBindings import DEFAULT_LANGUAGE
from ofnClasses import Term, Vocabulary


def checkVocabulary(vocabulary: Vocabulary):
    checkCycles(vocabulary)


def checkCycles(vocabulary: Vocabulary):
    visited: List[str] = []
    stack: List[str] = []
    rStack: List[str] = []
    for term in vocabulary.terms:
        if term.getIRI(vocabulary, DEFAULT_LANGUAGE) in visited:
            continue
        stack.append(term.getIRI(vocabulary, DEFAULT_LANGUAGE))
        while len(stack) > 0:
            iterID: str = stack[-1]
            if iterID in visited:
                if iterID in rStack:
                    rStack.remove(iterID)
                stack.pop()
                continue
            visited.append(iterID)
            rStack.append(iterID)
            iterTerm = next(
                x for x in vocabulary.terms if x._iri == iterID)
            for sco in iterTerm.subClassOf:
                if sco not in visited:
                    stack.append(sco)
                elif sco in rStack:
                    raise Exception(
                        "Byl nalezen cyklus nadřazených pojmů mezi následujícími pojmy: {}".format([next(x.name[DEFAULT_LANGUAGE] for x in vocabulary.terms if x._iri == y) for y in set(rStack)]))
