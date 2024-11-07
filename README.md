# Nástroje pro OFN slovníky
Python skripty pro převod různých formátů do slovníků kompatibilních s [OFN slovníky](https://ofn.gov.cz/slovníky/draft/) v RDF formátu.

## Použití
* Skripty nechávejte ve stejné složce.
* Pro všechny skripty jsou potřeba balíčky z `requirements.txt` (instalovatelné přes `pip install -r requirements.txt`).
* [formát]ToOFN.py jsou určeny pro uživatele, ostatní skripty jsou podpůrné.
* Použití na příkazové řádce: `python [formát]ToOFN.py (vstup) (výstup)`.
* Příklad: `python archiToOFN.py archi-export.xml slovník.ttl`.
* (výstup) může mít následující koncovky: `ttl` `xml` `json-ld` `nt` `n3` `trig` `trix` `nquads`
