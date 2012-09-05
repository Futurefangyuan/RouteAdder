import os

from xml.sax import make_parser, handler
from xml.sax._exceptions import SAXParseException


class Place:
    """Holds details about a place of interest"""

    def __init__(self, id, loc, cat, name, node):
        self.id = id      # OSM node id
        self.loc = loc    # (lat, lon)
        self.cat = cat    # The amenity category: e.g. place_of_worship
        self.name = name
        self.node = node  # OSM node id of the nearest road.

    def __repr__(self):
        return str(self.__dict__)


class PlacesLoader(handler.ContentHandler):
    """Loads dictionary of places (by node id) from osm file"""

    def __init__(self, roads):
        self.roads = roads

    def init(self, filename):
        """ Parses filename (osm file) and returns dict of places. """
        self._places = {}
        if not os.path.exists(filename):
            raise Exception("Can't load %s" % filename)

        elif not os.path.getsize(filename):
            raise Exception("File is empty: %s" % filename)

        self.inNode = False
        parser = make_parser()
        parser.setContentHandler(self)
        parser.parse(filename)
        return self._places

    def startElement(self, name, attrs):
        if name == "node":
            self.currentNode = {
                'id': long(attrs.get('id')),
                'lat': float(attrs.get('lat')),
                'lon': float(attrs.get('lon'))
            }
            self.inNode = True
        if name == "tag" and self.inNode:
            self.currentNode[attrs.get('k')] = attrs.get('v')

    def endElement(self, name):
        if(name == "node"):
            self.storeNode(self.currentNode)
            self.inNode = False

    def storeNode(self, n):
        if 'amenity' not in n:
            return
        node = self.roads.findNode(n['lat'], n['lon'], 'car')
        place = Place(n['id'], (n['lat'], n['lon']),
                      n.get('amenity', '?'), n.get('name', '?'), node)
        self._places[n['id']] = place
