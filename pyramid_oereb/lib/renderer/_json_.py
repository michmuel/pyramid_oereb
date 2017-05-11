# -*- coding: utf-8 -*-
from json import dumps

from pyramid.response import Response
from shapely.geometry import mapping

from pyramid_oereb import default_lang, srid
from pyramid_oereb.lib.renderer import Base


class Extract(Base):
    def __init__(self, info):
        """
        Creates a new JSON renderer instance for extract rendering.

        :var info: Info object.
        :vartype info: pyramid.interfaces.IRendererInfo
        """
        super(Extract, self).__init__(info)
        self.language = str(default_lang).lower()

    def __call__(self, value, system):
        """
        Returns the JSON encoded extract, according to the specification.

        :param value: A tuple containing the generated extract record and the params dictionary.
        :type value: tuple
        :param system: The available system properties.
        :type system: dict
        :return: The JSON encoded extract.
        :rtype: str
        """
        response = self.get_response(system)
        if isinstance(response, Response) and response.content_type == response.default_content_type:
            response.content_type = 'application/json'

        self._params_ = value[1]

        return self.__render__(value[0])

    def __render__(self, extract):
        """
        Serializes the extract record.

        :param extract: The extract record
        :type extract: pyramid_oereb.lib.records.extract.ExtractRecord
        :return: The JSON encoded extract.
        :rtype: str
        """

        if self._params_.get('language'):
            self.language = str(self._params_.get('language')).lower()

        extract_dict = {
            'CreationDate': self.date_time(extract.creation_date),
            'ConcernedTheme': [],
            'NotConcernedTheme': [],
            'ThemeWithoutData': [],
            'isReduced': self._params_.get('flavour') == 'reduced',
            'LogoPLRCadastre': extract.logo_plr_cadastre.encode(),
            'FederalLogo': extract.federal_logo.encode(),
            'CantonalLogo': extract.cantonal_logo.encode(),
            'MunicipalityLogo': extract.municipality_logo.encode(),
            'ExtractIdentifier': extract.extract_identifier,
            'BaseData': extract.base_data,
            'PLRCadastreAuthority': self.format_office(extract.plr_cadastre_authority),
            'RealEstate': self.format_real_estate(extract.real_estate)
        }

        if extract.electronic_signature:
            extract_dict['ElectronicSignature'] = extract.electronic_signature
        if extract.qr_code:
            extract_dict['QRCode'] = extract.qr_code
        if extract.general_information:
            extract_dict['GeneralInformation'] = extract.general_information

        if isinstance(extract.exclusions_of_liability, list) and len(extract.exclusions_of_liability) > 0:
            exclusions_of_liability = list()
            for eol in extract.exclusions_of_liability:
                exclusions_of_liability.append({
                    'Title': self.get_localized_text(eol.title),
                    'Content': self.get_localized_text(eol.content)
                })
            extract_dict['ExclusionOfLiability'] = exclusions_of_liability

        if isinstance(extract.glossaries, list) and len(extract.glossaries) > 0:
            glossaries = list()
            for gls in extract.glossaries:
                glossaries.append({
                    'Title': self.get_localized_text(gls.title),
                    'Content': self.get_localized_text(gls.content)
                })
            extract_dict['Glossary'] = glossaries

        return dumps(extract_dict)

    def format_real_estate(self, real_estate):
        """
        Formats a real estate record for rendering according to the federal specification.

        :param real_estate: The real estate record to be formatted.
        :type real_estate: pyramid_oereb.lib.records.real_estate.RealEstateRecord
        :return: The formatted dictionary for rendering.
        :rtype: dict
        """
        real_estate_dict = {
            'Type': real_estate.type,
            'Canton': real_estate.canton,
            'Municipality': real_estate.municipality,
            'FosNr': real_estate.fosnr,
            'LandRegistryArea': real_estate.land_registry_area
        }

        if self._params_.get('geometry'):
            real_estate_dict['Limit'] = self.format_geometry(real_estate.limit)

        if real_estate.number:
            real_estate_dict['Number'] = real_estate.number
        if real_estate.identdn:
            real_estate_dict['IdentDN'] = real_estate.identdn
        if real_estate.egrid:
            real_estate_dict['EGRID'] = real_estate.egrid
        if real_estate.subunit_of_land_register:
            real_estate_dict['SubunitOfLandRegister'] = real_estate.subunit_of_land_register
        if real_estate.metadata_of_geographical_base_data:
            real_estate_dict['MetadataOfGeographicalBaseData'] = \
                real_estate.metadata_of_geographical_base_data

        if isinstance(real_estate.public_law_restrictions, list) \
                and len(real_estate.public_law_restrictions) > 0:
            real_estate_dict['RestrictionOnLandownership'] = \
                self.format_plr(real_estate.public_law_restrictions)

        return real_estate_dict

    def format_plr(self, plrs):
        """
        Formats a public law restriction record for rendering according to the federal specification.

        :param plrs: The public law restriction records to be formatted.
        :type plrs: list of pyramid_oereb.lib.records.plr.PlrRecord
        :return: The formatted dictionaries for rendering.
        :rtype: list of dict
        """
        plr_list = list()

        for plr in plrs:

            plr_dict = {
                'Information': self.get_localized_text(plr.content),
                'Theme': plr.topic,
                'Lawstatus': plr.legal_state,
                'Area': plr.area,
                'Symbol': plr.symbol
            }

            if plr.subtopic:
                plr_dict['SubTheme'] = plr.subtopic
            if plr.additional_topic:
                plr_dict['OtherTheme'] = plr.additional_topic
            if plr.type_code:
                plr_dict['TypeCode'] = plr.type_code
            if plr.type_code_list:
                plr_dict['TypeCodelist'] = plr.type_code_list
            if plr.part_in_percent:
                plr_dict['PartInPercent'] = plr.part_in_percent

            plr_list.append(plr_dict)

        return plr_list

    def format_office(self, office):
        """
        Formats an office record for rendering according to the federal specification.

        :param office: The office record to be formatted.
        :type office: pyramid_oereb.lib.records.office.OfficeRecord
        :return: The formatted dictionary for rendering.
        :rtype: dict
        """
        office_dict = {
            'Name': self.get_localized_text(office.name)
        }
        if office.office_at_web:
            office_dict['OfficeAtWeb'] = office.office_at_web
        if office.uid:
            office_dict['UID'] = office.uid
        if office.line1:
            office_dict['Line1'] = office.line1
        if office.line2:
            office_dict['Line2'] = office.line2
        if office.street:
            office_dict['Street'] = office.street
        if office.number:
            office_dict['Number'] = office.number
        if office.postal_code:
            office_dict['PostalCode'] = office.postal_code
        if office.city:
            office_dict['City'] = office.city
        return office_dict

    def format_geometry(self, geom):
        """
        Formats shapely geometry for rendering according to the federal specification.

        :param geom: The geometry object to be formatted.
        :type geom: shapely.geometry.base.BaseGeometry
        :return: The formatted geometry.
        :rtype: dict
        """
        geom_dict = {
            'coordinates': mapping(geom)['coordinates'],
            'crs': 'EPSG:{srid}'.format(srid=srid)
            # isosqlmmwkb only used for curved geometries (not supported by shapely)
            # 'isosqlmmwkb': base64.b64encode(geom.wkb)
        }
        return geom_dict

    def get_localized_text(self, values):
        """
        Returns the set language of a multilingual text element.
        TODO: Fix implementation when multilingual values are available by respecting self.language.

        :param values: The multilingual values encoded as JSON.
        :type values: str
        :return: List of dictionaries containing the multilingual representation.
        :rtype: list of dict
        """
        return [
            {
                'Language': 'de',
                'Text': values
            }
        ]
