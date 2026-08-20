from dataclasses import dataclass
import logging
import warnings

from .jsonld_properties import (
    DATE_REGEX,
    EUROVOC_REGEX,
    FORMAT_REGEX,
    FREQUENCY_REGEX,
    HTTPS_REGEX,
    ISVS_REGEX,
    MEDIA_TYPE_REGEX,
    PROVIDER_REGEX,
    THEME_REGEX,
    addCodeProperty,
    addEmailProperty,
    addNonEmptyProperty,
    addPrefixedProperty,
    addProperty,
    addPropertyHelper,
    addRegexProperty,
    containsCompare,
    getSubproperty,
    readProperty,
    splitProperty,
)
from .ofn_distribution_bindings import (
    AUTOR,
    AUTOR_DATABAZE,
    AUTORSKE_DILO,
    CASOVE_POKRYTI,
    CASOVE_POKRYTI_KONEC,
    CASOVE_POKRYTI_ZACATEK,
    CONTEXT,
    CS,
    DATABAZE_CHRANENA_ZVLASTNIMI_PRAVY,
    DATABAZE_JAKO_AUTORSKE_DILO,
    DISTRIBUCE,
    DOKUMENTACE,
    E_MAIL,
    FORMAT,
    IRI,
    JE_SOUCASTI,
    JE_ZAHRNUTA_V_ISVS,
    JMENO,
    KLICOVE_SLOVO,
    KONCEPT_EUROVOC,
    KONTAKTNI_BOD,
    KONTAKTNI_BOD_EMAIL,
    KONTAKTNI_BOD_JMENO,
    KONEC,
    NAZEV,
    OSOBNI_UDAJE,
    PERIODICITA_AKTUALIZACE,
    PODMINKY_UZITI,
    POPIS,
    POPIS_PRISTUPOVEHO_BODU,
    POSKYTOVATEL,
    PRAVNI_PREDPIS,
    PRISTUPOVA_SLUZBA,
    PRISTUPOVE_URL,
    PRISTUPOVY_BOD,
    SCHEMA,
    SOUBOR_KE_STAZENI,
    SPECIFIKACE,
    TEMA,
    TYP,
    TYP_MEDIA,
    TYP_MEDIA_BALICKU,
    TYP_MEDIA_KOMPRESE,
    TYKA_SE_POJMU,
    VSTUPNI_STRANKA,
    ZACATEK,
)
from .xml_processing import ArchimateElement


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DistributionDocument:
    kind: str
    document: dict


def _single_property(element: ArchimateElement, property_name: str):
    return addPropertyHelper(readProperty(element, property_name))


def _list_property(element: ArchimateElement, property_name: str):
    return splitProperty(readProperty(element, property_name))


def _localized_names(element: ArchimateElement) -> dict:
    return {name.language: name.value for name in element.names}


def _build_usage_terms(
    distribution: ArchimateElement,
    distribution_iri: str,
) -> dict:
    def property_name(child: str) -> str:
        return getSubproperty(PODMINKY_UZITI, child)

    return {
        IRI: distribution_iri + "/specifikace-podmínek-užití",
        TYP: ["Specifikace podmínek užití"],
        **addRegexProperty(
            AUTORSKE_DILO,
            _single_property(distribution, property_name(AUTORSKE_DILO)),
            HTTPS_REGEX,
            distribution,
            property_name(AUTORSKE_DILO),
        ),
        **addProperty(
            AUTOR,
            {CS: _single_property(distribution, property_name(AUTOR))},
            distribution,
            property_name(AUTOR),
        ),
        **addRegexProperty(
            DATABAZE_JAKO_AUTORSKE_DILO,
            _single_property(
                distribution,
                property_name(DATABAZE_JAKO_AUTORSKE_DILO),
            ),
            HTTPS_REGEX,
            distribution,
            property_name(DATABAZE_JAKO_AUTORSKE_DILO),
        ),
        **addProperty(
            AUTOR_DATABAZE,
            {CS: _single_property(
                distribution, property_name(AUTOR_DATABAZE))},
            distribution,
            property_name(AUTOR_DATABAZE),
        ),
        **addRegexProperty(
            DATABAZE_CHRANENA_ZVLASTNIMI_PRAVY,
            _single_property(
                distribution,
                property_name(DATABAZE_CHRANENA_ZVLASTNIMI_PRAVY),
            ),
            HTTPS_REGEX,
            distribution,
            property_name(DATABAZE_CHRANENA_ZVLASTNIMI_PRAVY),
        ),
        **addRegexProperty(
            OSOBNI_UDAJE,
            _single_property(distribution, property_name(OSOBNI_UDAJE)),
            HTTPS_REGEX,
            distribution,
            property_name(OSOBNI_UDAJE),
        ),
    }


def _build_common_distribution_properties(
    distribution: ArchimateElement,
    distribution_iri: str,
    usage_terms: dict,
) -> dict:
    return {
        IRI: distribution_iri,
        TYP: ["Datové rozhraní", "Distribuce"],
        NAZEV: _localized_names(distribution),
        **addRegexProperty(
            PRISTUPOVE_URL,
            _single_property(distribution, PRISTUPOVE_URL),
            HTTPS_REGEX,
            distribution,
        ),
        **addRegexProperty(
            PRAVNI_PREDPIS,
            _list_property(distribution, PRAVNI_PREDPIS),
            HTTPS_REGEX,
            distribution,
        ),
        **addPrefixedProperty(PODMINKY_UZITI, usage_terms, distribution),
    }


def _build_download_distribution(
    distribution: ArchimateElement,
    distribution_iri: str,
    usage_terms: dict,
) -> dict:
    return {
        **_build_common_distribution_properties(
            distribution,
            distribution_iri,
            usage_terms,
        ),
        **addRegexProperty(
            SOUBOR_KE_STAZENI,
            _single_property(distribution, SOUBOR_KE_STAZENI),
            HTTPS_REGEX,
            distribution,
        ),
        # File type according to the code list at https://op.europa.eu/en/web/eu-vocabularies/concept-scheme/-/resource?uri=http://publications.europa.eu/resource/authority/file-type (code is the field inputted here, for example 7Z  - should be transformed into formáty:75 for the jsonld)
        **addCodeProperty(
            FORMAT,
            _single_property(distribution, FORMAT),
            "formáty:",
            FORMAT_REGEX,
            distribution,
        ),
        # Media type according to IANA file types, for example application/zip - should be transformed into mediaTypes:application/zip for the jsonld
        **addCodeProperty(
            TYP_MEDIA,
            _single_property(distribution, TYP_MEDIA),
            "mediaTypes:",
            MEDIA_TYPE_REGEX,
            distribution,
        ),
        **addRegexProperty(
            SCHEMA,
            _single_property(distribution, SCHEMA),
            HTTPS_REGEX,
            distribution,
        ),
        # Media type according to IANA file types, for example application/zip - should be transformed into mediaTypes:application/zip for the jsonld
        **addCodeProperty(
            TYP_MEDIA_KOMPRESE,
            _single_property(distribution, TYP_MEDIA_KOMPRESE),
            "mediaTypes:",
            MEDIA_TYPE_REGEX,
            distribution,
        ),
        # Media type according to IANA file types, for example application/zip - should be transformed into mediaTypes:application/zip for the jsonld
        **addCodeProperty(
            TYP_MEDIA_BALICKU,
            _single_property(distribution, TYP_MEDIA_BALICKU),
            "mediaTypes:",
            MEDIA_TYPE_REGEX,
            distribution,
        ),
    }


def _build_access_service(
    distribution: ArchimateElement,
    distribution_iri: str,
) -> dict:
    def property_name(child: str) -> str:
        return getSubproperty(PRISTUPOVA_SLUZBA, child)

    return {
        IRI: distribution_iri + "/přístupová-služba",
        TYP: ["Datová služba"],
        NAZEV: _localized_names(distribution),
        **addRegexProperty(
            PRISTUPOVY_BOD,
            _single_property(distribution, property_name(PRISTUPOVY_BOD)),
            HTTPS_REGEX,
            distribution,
            property_name(PRISTUPOVY_BOD),
        ),
        **addRegexProperty(
            POPIS_PRISTUPOVEHO_BODU,
            _single_property(
                distribution,
                property_name(POPIS_PRISTUPOVEHO_BODU),
            ),
            HTTPS_REGEX,
            distribution,
            property_name(POPIS_PRISTUPOVEHO_BODU),
        ),
        **addRegexProperty(
            PRAVNI_PREDPIS,
            _list_property(distribution, property_name(PRAVNI_PREDPIS)),
            HTTPS_REGEX,
            distribution,
            property_name(PRAVNI_PREDPIS),
        ),
        **addRegexProperty(
            SPECIFIKACE,
            _list_property(distribution, property_name(SPECIFIKACE)),
            HTTPS_REGEX,
            distribution,
            property_name(SPECIFIKACE),
        ),
        **addRegexProperty(
            DOKUMENTACE,
            _single_property(distribution, property_name(DOKUMENTACE)),
            HTTPS_REGEX,
            distribution,
            property_name(DOKUMENTACE),
        ),
    }


def _build_service_distribution(
    distribution: ArchimateElement,
    distribution_iri: str,
    usage_terms: dict,
) -> dict:
    common_properties = _build_common_distribution_properties(
        distribution,
        distribution_iri,
        usage_terms,
    )
    access_service = _build_access_service(distribution, distribution_iri)
    return {
        **common_properties,
        **addPrefixedProperty(
            PRISTUPOVA_SLUZBA,
            access_service,
            distribution,
        ),
    }


def build_distributions(
    distributions: list[ArchimateElement],
    dataset_iri: str,
) -> list[DistributionDocument]:
    documents = []

    for index, distribution in enumerate(distributions):
        distribution_iri = "{}/distribuce/{}".format(dataset_iri, index)
        usage_terms = _build_usage_terms(distribution, distribution_iri)
        distribution_type = readProperty(distribution, TYP)

        if containsCompare(
            distribution_type,
            "distribuce - soubor ke stažení",
        ):
            logger.info(
                "Generated distribution IRI %r for element ID %r",
                distribution_iri,
                distribution.identifier,
            )
            logger.info(
                "Generated usage terms IRI %r for distribution element ID %r",
                usage_terms[IRI],
                distribution.identifier,
            )
            documents.append(DistributionDocument(
                kind="download",
                document=_build_download_distribution(
                    distribution,
                    distribution_iri,
                    usage_terms,
                ),
            ))
        elif containsCompare(
            distribution_type,
            "distribuce - datová služba",
        ):
            logger.info(
                "Generated distribution IRI %r for element ID %r",
                distribution_iri,
                distribution.identifier,
            )
            logger.info(
                "Generated usage terms IRI %r for distribution element ID %r",
                usage_terms[IRI],
                distribution.identifier,
            )
            logger.info(
                "Generated access service IRI %r for distribution element ID %r",
                distribution_iri + "/přístupová-služba",
                distribution.identifier,
            )
            documents.append(DistributionDocument(
                kind="service",
                document=_build_service_distribution(
                    distribution,
                    distribution_iri,
                    usage_terms,
                ),
            ))
        else:
            warnings.warn(
                "Skipping distribution of element ID {} because it doesn't "
                "specify the exact distribution type".format(
                    distribution.identifier,
                )
            )

    return documents


def _build_temporal_coverage(dataset: ArchimateElement) -> dict:
    return {
        TYP: ["Časový interval"],
        **addRegexProperty(
            ZACATEK,
            _single_property(dataset, CASOVE_POKRYTI_ZACATEK),
            DATE_REGEX,
            dataset,
            CASOVE_POKRYTI_ZACATEK,
        ),
        **addRegexProperty(
            KONEC,
            _single_property(dataset, CASOVE_POKRYTI_KONEC),
            DATE_REGEX,
            dataset,
            CASOVE_POKRYTI_KONEC,
        ),
    }


def _build_contact_point(dataset: ArchimateElement) -> dict:
    return {
        TYP: ["Organizace"],
        **addProperty(
            JMENO,
            {CS: _single_property(dataset, KONTAKTNI_BOD_JMENO)},
            dataset,
            KONTAKTNI_BOD_JMENO,
        ),
        **addEmailProperty(
            E_MAIL,
            _single_property(dataset, KONTAKTNI_BOD_EMAIL),
            dataset,
            KONTAKTNI_BOD_EMAIL,
        ),
    }


def build_dataset_document(
    dataset: ArchimateElement,
    dataset_iri: str,
    related_term_iris: list[str],
    distributions: list[DistributionDocument],
) -> dict:
    return {
        CONTEXT: "https://ofn.gov.cz/dcat-ap-cz-datová-rozhraní/draft/datová-sada/kontext.jsonld",
        IRI: dataset_iri,
        TYP: ["Datová sada", "Datová sada SSP"],
        NAZEV: _localized_names(dataset),
        **addProperty(
            POPIS,
            {CS: _single_property(dataset, POPIS)},
            dataset,
        ),
        **addRegexProperty(
            POSKYTOVATEL,
            _single_property(dataset, POSKYTOVATEL),
            PROVIDER_REGEX,
            dataset,
        ),
        # Themes according to the code list at https://op.europa.eu/en/web/eu-vocabularies/concept-scheme/-/resource?uri=http://publications.europa.eu/resource/authority/data-theme (code is the field inputted here, for example GOVE  - should be transformed into témata:GOVE for the jsonld)
        **addCodeProperty(
            TEMA,
            _list_property(dataset, TEMA),
            "témata:",
            THEME_REGEX,
            dataset,
        ),
        # Themes according to the code list at https://op.europa.eu/en/web/eu-vocabularies/concept-scheme/-/resource?uri=http://publications.europa.eu/resource/authority/frequency (code is the field inputted here, for example CONT - should be transformed into frekvence:CONT for the jsonld)
        **addCodeProperty(
            PERIODICITA_AKTUALIZACE,
            _single_property(dataset, PERIODICITA_AKTUALIZACE),
            "frekvence:",
            FREQUENCY_REGEX,
            dataset,
        ),
        **addProperty(
            KLICOVE_SLOVO,
            {CS: _list_property(dataset, KLICOVE_SLOVO)},
            dataset,
        ),
        **addPrefixedProperty(
            CASOVE_POKRYTI,
            _build_temporal_coverage(dataset),
            dataset,
        ),
        **addPrefixedProperty(
            KONTAKTNI_BOD,
            _build_contact_point(dataset),
            dataset,
        ),
        **addRegexProperty(
            DOKUMENTACE,
            _single_property(dataset, DOKUMENTACE),
            HTTPS_REGEX,
            dataset,
        ),
        **addRegexProperty(
            SPECIFIKACE,
            _list_property(dataset, SPECIFIKACE),
            HTTPS_REGEX,
            dataset,
        ),
        # one or more numbers, for example 1234;5678 - should be transformed into [euroVoc:1234, euroVoc:5678] for the jsonld
        **addCodeProperty(
            KONCEPT_EUROVOC,
            _list_property(dataset, KONCEPT_EUROVOC),
            "euroVoc:",
            EUROVOC_REGEX,
            dataset,
        ),
        **addNonEmptyProperty(TYKA_SE_POJMU, related_term_iris),
        # A number, for example 1234 - should be transformed into isvs:1234 for the jsonld
        **addCodeProperty(
            JE_ZAHRNUTA_V_ISVS,
            _single_property(dataset, JE_ZAHRNUTA_V_ISVS),
            "isvs:",
            ISVS_REGEX,
            dataset,
        ),
        **addRegexProperty(
            JE_SOUCASTI,
            _single_property(dataset, JE_SOUCASTI),
            HTTPS_REGEX,
            dataset,
        ),
        **addRegexProperty(
            PRAVNI_PREDPIS,
            _list_property(dataset, PRAVNI_PREDPIS),
            HTTPS_REGEX,
            dataset,
        ),
        **addNonEmptyProperty(
            DISTRIBUCE,
            [distribution.document for distribution in distributions],
        ),
        **addRegexProperty(
            VSTUPNI_STRANKA,
            _single_property(dataset, VSTUPNI_STRANKA),
            HTTPS_REGEX,
            dataset,
        ),
    }
