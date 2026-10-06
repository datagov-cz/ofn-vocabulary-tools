from __future__ import annotations

from typing import TYPE_CHECKING

from .ofn_distribution_bindings import (
    CONTEXT,
    CS,
    DISTRIBUCE,
    E_MAIL,
    FORMAT,
    IRI,
    JE_ZAHRNUTA_V_ISVS,
    JMENO,
    KLICOVE_SLOVO,
    KONTAKTNI_BOD,
    NAZEV,
    PODMINKY_UZITI,
    POPIS,
    PRAVNI_PREDPIS,
    PRISTUPOVA_SLUZBA,
    PRISTUPOVE_URL,
    PRISTUPOVY_BOD,
    TYP,
    TYP_MEDIA,
    TYKA_SE_POJMU,
)

if TYPE_CHECKING:
    from .jsonld_builders import DistributionDocument


DATASET_REQUIRED_FIELDS = (
    CONTEXT,
    IRI,
    TYP,
    NAZEV,
    POPIS,
    KLICOVE_SLOVO,
    TYKA_SE_POJMU,
    JE_ZAHRNUTA_V_ISVS,
    PRAVNI_PREDPIS,
)
DOWNLOAD_DISTRIBUTION_REQUIRED_FIELDS = (
    IRI,
    TYP,
    PRISTUPOVE_URL,
    PRAVNI_PREDPIS,
    PODMINKY_UZITI,
    FORMAT,
    TYP_MEDIA,
)
SERVICE_DISTRIBUTION_REQUIRED_FIELDS = (
    IRI,
    TYP,
    PRISTUPOVE_URL,
    PRAVNI_PREDPIS,
    PODMINKY_UZITI,
    PRISTUPOVA_SLUZBA,
)
ACCESS_SERVICE_REQUIRED_FIELDS = (
    IRI,
    TYP,
    NAZEV,
    PRISTUPOVY_BOD,
    PRAVNI_PREDPIS,
)
CONTACT_POINT_REQUIRED_FIELDS = (TYP, JMENO, E_MAIL)


def missingRequiredFields(
    document: dict,
    required_fields,
    prefix: str = "",
) -> list[str]:
    return [
        "{}.{}".format(prefix, field) if prefix else field
        for field in required_fields
        if field not in document
    ]


def find_missing_required_fields(
    document: dict,
    distributions: list[DistributionDocument],
) -> list[str]:
    missing_fields = missingRequiredFields(document, DATASET_REQUIRED_FIELDS)

    if KONTAKTNI_BOD in document:
        contact_point = document[KONTAKTNI_BOD]
        missing_fields.extend(missingRequiredFields(
            contact_point,
            CONTACT_POINT_REQUIRED_FIELDS,
            KONTAKTNI_BOD,
        ))
        if JMENO in contact_point:
            missing_fields.extend(missingRequiredFields(
                contact_point[JMENO],
                (CS,),
                "{}.{}".format(KONTAKTNI_BOD, JMENO),
            ))

    for index, distribution in enumerate(distributions):
        distribution_path = "{}[{}]".format(DISTRIBUCE, index)
        required_fields = (
            DOWNLOAD_DISTRIBUTION_REQUIRED_FIELDS
            if distribution.kind == "download"
            else SERVICE_DISTRIBUTION_REQUIRED_FIELDS
        )
        missing_fields.extend(missingRequiredFields(
            distribution.document,
            required_fields,
            distribution_path,
        ))

        if (
            distribution.kind == "service"
            and PRISTUPOVA_SLUZBA in distribution.document
        ):
            missing_fields.extend(missingRequiredFields(
                distribution.document[PRISTUPOVA_SLUZBA],
                ACCESS_SERVICE_REQUIRED_FIELDS,
                "{}.{}".format(distribution_path, PRISTUPOVA_SLUZBA),
            ))

    return missing_fields


def find_missing_required_entries(document: dict) -> list[tuple[str, dict]]:
    """Return every missing field together with the JSON entry it belongs to.

    Unlike ``find_missing_required_fields``, this representation retains the
    entry itself so reports can include its name and IRI.
    """
    missing = [
        (field, document)
        for field in DATASET_REQUIRED_FIELDS
        if field not in document
    ]

    contact_point = document.get(KONTAKTNI_BOD)
    if isinstance(contact_point, dict):
        missing.extend(
            (field, document)
            for field in CONTACT_POINT_REQUIRED_FIELDS
            if field not in contact_point
        )
        contact_name = contact_point.get(JMENO)
        if isinstance(contact_name, dict) and CS not in contact_name:
            missing.append(("{}.{}.{}".format(KONTAKTNI_BOD, JMENO, CS), document))

    for distribution in document.get(DISTRIBUCE, []):
        if not isinstance(distribution, dict):
            continue
        access_service = distribution.get(PRISTUPOVA_SLUZBA)
        required_fields = (
            SERVICE_DISTRIBUTION_REQUIRED_FIELDS
            if isinstance(access_service, dict)
            else DOWNLOAD_DISTRIBUTION_REQUIRED_FIELDS
        )
        missing.extend(
            (field, distribution)
            for field in required_fields
            if field not in distribution
        )

        if isinstance(access_service, dict):
            missing.extend(
                (field, access_service)
                for field in ACCESS_SERVICE_REQUIRED_FIELDS
                if field not in access_service
            )

    return missing
