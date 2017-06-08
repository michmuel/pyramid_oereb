# -*- coding: utf-8 -*-
import logging
import urllib2

from pyramid_oereb.lib.records.logo import LogoRecord
from pyramid_oereb.lib.url import add_url_params
from pyramid_oereb.lib.url import uri_validator
from pyramid_oereb.lib.config import Config


log = logging.getLogger('pyramid_oereb')


class LegendEntryRecord(object):

    def __init__(self, symbol, legend_text, type_code, type_code_list, theme, sub_theme=None,
                 additional_theme=None):
        """
        Represents a legend entry with it's text as well as it's image.

        Args:
            symbol (binary): The binary file content of the legend image.
            legend_text (str): The description text for the legend entry.
            type_code (str): The class of the legend entry corresponding to the plrs classes.
            type_code_list (str): An URL to the type code list.
            theme (pyramid_oereb.lib.records.theme.ThemeRecord): The theme to which the legend
                entry belongs to.
            sub_theme (str): Theme sub category.
            additional_theme (str): Additional theme linked to this theme.
        """
        self.symbol = symbol
        self.legend_text = legend_text
        self.type_code = type_code
        self.type_code_list = type_code_list
        self.theme = theme
        self.sub_theme = sub_theme
        self.additional_theme = additional_theme

    @classmethod
    def get_fields(cls):
        """
        Returns a list of available field names.

        Returns:
            list of str: List of available field names.
        """
        return [
            'symbol',
            'legend_text',
            'type_code',
            'type_code_list',
            'theme',
            'sub_theme',
            'additional_theme'
        ]

    def to_extract(self):
        """
        Returns a dictionary with all available values needed for the extract.

        Returns:
            dict: Dictionary with values for the extract.
        """
        extract = dict()
        for key in [
            'symbol',
            'legend_text',
            'type_code',
            'type_code_list',
            'sub_theme',
            'additional_theme'
        ]:
            value = getattr(self, key)
            if value:
                extract[key] = value
        key = 'theme'
        theme_record = getattr(self, key)
        extract['theme'] = theme_record.to_extract()
        return extract


class ViewServiceRecord(object):
    # Attributes defined while processing
    image = None    # map image resulting from calling the wms link - binary

    def __init__(self, link_wms, legend_web, legends=None):
        """

        Args:
            link_wms (str): The link URL to the actual service (WMS)
            legend_web (str): The link URL to the actual legend service (WMS get legend)
            legends (list of LegendEntry): A list of all relevant legend entries.
        """
        self.link_wms = link_wms
        self.legend_web = legend_web
        if legends is None:
            self.legends = []
        else:
            self.legends = legends

    @classmethod
    def get_fields(cls):
        """
        Returns a list of available field names.

        Returns:
            list of str: List of available field names.
        """
        return [
            'link_wms',
            'legend_web',
            'legends'
        ]

    def to_extract(self, type_code=None):
        """
        Returns a dictionary with all available values needed for the extract.

        Args:
            type_code (str): Filter referenced legend entries by the specified type code.

        Returns:
            dict: Dictionary with values for the extract.
        """
        extract = dict()
        for key in ['link_wms', 'legend_web']:
            value = getattr(self, key)
            if value:
                extract[key] = value
        key = 'legends'
        legends = getattr(self, key)
        if legends and len(legends) > 0:
            if type_code:
                filtered = list()
                for legend in legends:
                    if legend.type_code == type_code:
                        filtered.append(legend.to_extract())
                extract[key] = filtered
            else:
                extract[key] = [legend.to_extract() for legend in legends]
        return extract

    @staticmethod
    def _get_bbox(geometry, map_size, print_buffer):
        width_buffer = (geometry.bounds[2] - geometry.bounds[0]) * print_buffer / 100
        height_buffer = (geometry.bounds[3] - geometry.bounds[1]) * print_buffer / 100
        print_bounds = [
            geometry.bounds[0] - width_buffer,
            geometry.bounds[1] - height_buffer,
            geometry.bounds[2] + width_buffer,
            geometry.bounds[3] + height_buffer,
        ]
        width = print_bounds[2] - print_bounds[0]
        height = print_bounds[3] - print_bounds[1]
        obj_ration = width / height
        print_ration = map_size[0] / map_size[1]
        if obj_ration > print_ration:
            to_add = (width / print_ration - height) / 2
            print_bounds[0] -= to_add
            print_bounds[2] += to_add
        else:
            to_add = (height * print_ration - width) / 2
            print_bounds[1] -= to_add
            print_bounds[3] += to_add
        return print_bounds

    def get_full_wms_url(self, real_estate):
        """
        Returns the WMS URL to get the image.

        Args:
            real_estate (pyramid_oereb.lob.records.real_estate.RealEstateRecord): The Real
                Estate record.

        Returns:
            str: The url used to query the WMS server.
        """

        assert real_estate.limit is not None

        print_conf = Config.get_object_path('print', required=['map_size', 'buffer'])
        map_size = print_conf['map_size']
        bbox = self._get_bbox(real_estate.limit, map_size, print_conf['buffer'])
        return add_url_params(self.link_wms, {
            "BBOX": ",".join([str(e) for e in bbox])
        })

    def download_wms_content(self):
        """
        Simply downloads the image found behind the URL stored in the instance attribute "link_wms".
        :raises: LookupError if the response is not code 200
        :raises: AttributeError if the URL itself isn't valid at all.
        """
        # TODO: Check better for a image as response than only code 200...
        main_msg = "Image for WMS couldn't be retrieved."
        if uri_validator(self.link_wms):
            print self.link_wms
            response = urllib2.urlopen(self.link_wms)
            if response.getcode() == 200:
                self.image = LogoRecord(response.read())
            else:
                dedicated_msg = "The image could not be downloaded. URL was: {url}, Response was " \
                                "{response}".format(url=self.link_wms, response=response.read())
                log.error(main_msg)
                log.error(dedicated_msg)
                raise LookupError(dedicated_msg)
        else:
            dedicated_msg = "URL seems to be not valid. URL was: {url}".format(url=self.link_wms)
            log.error(main_msg)
            log.error(dedicated_msg)
            raise AttributeError(dedicated_msg)
