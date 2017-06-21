# -*- coding: utf-8 -*-

import pytest
from pyramid_oereb.lib.processor import Processor
from pyramid_oereb.lib.records.extract import ExtractRecord
from pyramid_oereb.tests.conftest import MockRequest
from pyramid_oereb import ExtractReader
from pyramid_oereb import MunicipalityReader
from pyramid_oereb import ExclusionOfLiabilityReader
from pyramid_oereb import GlossaryReader
from pyramid_oereb import RealEstateReader
from pyramid_oereb.views.webservice import PlrWebservice


request_matchdict = {
    'flavour': 'reduced',
    'format': 'json',
    'param1': 'TEST'
}


def test_missing_params():
    with pytest.raises(TypeError):
        Processor()


def test_properties():
    request = MockRequest()
    request.matchdict.update(request_matchdict)
    processor = request.pyramid_oereb_processor
    assert isinstance(processor.extract_reader, ExtractReader)
    assert isinstance(processor.municipality_reader, MunicipalityReader)
    assert isinstance(processor.exclusion_of_liability_reader, ExclusionOfLiabilityReader)
    assert isinstance(processor.glossary_reader, GlossaryReader)
    assert isinstance(processor.plr_sources, list)
    assert isinstance(processor.real_estate_reader, RealEstateReader)


def test_process(connection):
    assert connection.closed
    request = MockRequest()
    request.matchdict.update(request_matchdict)
    processor = request.pyramid_oereb_processor
    real_estate = processor.real_estate_reader.read(egrid=u'TEST')
    webservice = PlrWebservice(request)
    params = webservice.__validate_extract_params__()
    extract = processor.process(real_estate[0], params)
    assert isinstance(extract, ExtractRecord)


def test_process_geometry_testing(connection):
    assert connection.closed
    request = MockRequest()
    request.matchdict.update(request_matchdict)
    processor = request.pyramid_oereb_processor
    real_estate = processor.real_estate_reader.read(egrid=u'TEST')
    webservice = PlrWebservice(request)
    params = webservice.__validate_extract_params__()
    extract = processor.process(real_estate[0], params)
    for plr in extract.real_estate.public_law_restrictions:
        for g in plr.geometries:
            assert g._test_passed


def test_filter_published_documents(connection):
    assert connection.closed
    request = MockRequest()
    request.matchdict.update(request_matchdict)
    processor = request.pyramid_oereb_processor
    real_estate = processor.real_estate_reader.read(egrid=u'TEST')
    webservice = PlrWebservice(request)
    params = webservice.__validate_extract_params__()
    extract = processor.process(real_estate[0], params)
    for plr in extract.real_estate.public_law_restrictions:
        if plr.theme.code == u'MotorwaysBuildingLines':
            assert len(plr.documents) == 1
            assert len(plr.documents[0].references) == 1


def test_processor_with_images(connection):
    assert connection.closed
    request = MockRequest()
    request.matchdict.update(request_matchdict)
    request.params.update({
        'WITHIMAGES': '',
        'LANG': 'de'
    })
    processor = request.pyramid_oereb_processor
    real_estate = processor.real_estate_reader.read(egrid=u'TEST')
    webservice = PlrWebservice(request)
    params = webservice.__validate_extract_params__()
    extract = processor.process(real_estate[0], params)
    # TODO: uncomment this when issue GSOREB-194 is solved.
    # assert extract.real_estate.plan_for_land_register.image is not None
    for plr in extract.real_estate.public_law_restrictions:
        assert plr.view_service.image is not None


def test_processor_without_images(connection):
    assert connection.closed
    request = MockRequest()
    request.matchdict.update(request_matchdict)
    request.params.update({
        'LANG': 'de'
    })
    processor = request.pyramid_oereb_processor
    real_estate = processor.real_estate_reader.read(egrid=u'TEST')
    webservice = PlrWebservice(request)
    params = webservice.__validate_extract_params__()
    extract = processor.process(real_estate[0], params)
    # TODO: uncomment this when issue GSOREB-194 is solved.
    # assert extract.real_estate.plan_for_land_register.image is None
    for plr in extract.real_estate.public_law_restrictions:
        assert plr.view_service.image is None