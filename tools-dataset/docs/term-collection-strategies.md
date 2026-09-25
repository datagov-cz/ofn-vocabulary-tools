# Term collection strategies

This document records how the dataset property `metoda sbírání pojmů` is
understood and implemented. It controls construction of `týká_se_pojmu`; the
property itself is not written to JSON-LD.

## Common starting point

Both `standard` and `agresivně` start with elements whose `typ` contains
`typ objektu` or `typ subjektu` and which are connected directly to the dataset
by an `Association`. The dataset association can point in either direction and
does not have to be directed.

Only elements whose `typ` contains `typ objektu`, `typ subjektu`, or
`typ vlastnosti` can become collected terms.

## Allowed traversal edges

The implementation recognizes only these edges while expanding terms:

1. A directed, named `Association` between two `typ objektu`/`typ subjektu`
   elements. Traversal is bidirectional; `source` and `target` do not restrict
   the traversal direction.
2. `Specialization` or `Generalization` between two class elements
   (`typ objektu`/`typ subjektu`), or between two `typ vlastnosti` elements.
   These hierarchy connections are traversed in either direction. A hierarchy
   connection between a class and a property is not traversed.
3. `Composition` between a class element and a `typ vlastnosti` element.
   Composition is traversed in either direction.

Other relationships, including `Aggregation` and undirected associations, are
not traversal edges.

## Relationship terms

An association relationship itself is included in `týká_se_pojmu` only when:

- it is an `Association` between two class elements;
- `isDirected` is `true`;
- it has at least one non-empty name; and
- it falls within the terms selected by the current strategy.

An unnamed or undirected association is neither a traversal edge nor an emitted
relationship term.

## `standard`

`standard` keeps only the class elements directly associated with the dataset.
It does not add another class merely because that class is connected through an
association, generalization, or specialization.

It additionally includes:

- `typ vlastnosti` elements connected directly to one of the selected classes
  by `Composition`; and
- named directed associations whose source and target are both among the
  directly selected classes.

## `agresivně`

`agresivně` recursively expands from the directly selected classes through
the allowed traversal edges above. Every reachable class or property term is
included. Every named directed class-to-class association whose endpoints are
in the resulting reachable set is also included.

Cycles are handled by remembering visited element identifiers.

## `podrobně`

`podrobně` retains manual selection: recognized element terms must be directly
associated with the dataset. An association relationship term must also be
directly associated with the dataset and satisfy the relationship-term rules
above.

If `metoda sbírání pojmů` is missing or empty, the implementation uses
`podrobně`. An invalid non-empty value produces a warning and also falls back
to `podrobně`.
