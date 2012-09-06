import collections
import math
import pickle

import numpy as np
import scipy.stats

from pyroute import route
from places import *
from draw import *


class RouteAdder:
    def __init__(self):
        pass

    def init(self, fileName='data/westwood.osm'):
        print 'Loading roads...'
        self.roads = route.LoadOsm(fileName)
        print 'Loading places...'
        self.places = PlacesLoader(self.roads).init(fileName)
        print 'Initializing router...'
        self.router = route.Router(self.roads)
        print 'Done.'
        self.setSensitive()

    def setSensitive(self, cats=['hospital', 'place_of_worship']):
        self.sensitiveCats = cats
        self.sensitivePlaces = \
            set([k for (k, p) in self.places.items() if p.cat in cats])
        self.attr = collections.defaultdict(collections.Counter)
        for place in self.places.values():
            self.attr[place.node].update((place.cat,))

    def drawSensitivePlaces(self, s):
        for node in self.attr.keys():
            num_sen = sum([x for (k, x) in self.attr[node].items()
                           if k in self.sensitiveCats])
            num_places = sum([x for (k, x) in self.attr[node].items()])

            if num_places == 0:
                ratio = 0
            else:
                ratio = float(num_sen) / num_places

            drawProp = (ratio, 1.0 - ratio, 0.0, 1.0, 3.0)
            s.markNode(self.roads.nodes[node], drawProp)

    def analyze(self, (origNode, sensNode, destNode)):
        print 'Performing analysis (%d, %d, %d)' % (origNode, sensNode, destNode)
        # Get a list of nearby safe places.
        nearbyPlaces = \
            [p for p in self.places.values()
             if self.distanceBetween(sensNode, p.node) < 0.03
             and p.id not in self.sensitivePlaces]

        # Compute a distribution over safe places.
        safePlaceProb = \
            [self.getToPlaceWeight(origNode, sensNode, destNode, p.node)
             for p in nearbyPlaces]

        # Sample a place from distribution.
        cdf = np.cumsum(safePlaceProb)
        cdf = cdf / cdf[-1]
        rand = np.random.uniform()
        reroutePlace = (p for (p, pr) in zip(nearbyPlaces, cdf)
                        if pr > rand).next()

        ind = np.argmax(safePlaceProb)
        reroutePlace = nearbyPlaces[ind]



        print 'Found alternate node:'
        print reroutePlace

        # Draw analysis
        print 'Drawing out to png...'
        s = MapSurface()
        loc = self.roads.nodes[sensNode]
        s.setup(loc, scale=2000, pixels=1000)

        # Draw roads.
        drawProp = (0.0, 0.0, 1.0, 0.3, 2.0)
        s.markNodes(self.roads.nodes.values(), drawProp)
        self.drawSensitivePlaces(s)

        # Draw paths.
        path = self.getPath(origNode, sensNode)
        drawProp = (0.0, 1.0, 0.0, 0.5, 5.0)
        s.markPath([self.roads.nodes[x] for x in path], drawProp)

        path = self.getPath(sensNode, destNode)
        drawProp = (0.0, 1.0, 0.0, 0.5, 5.0)
        s.markPath([self.roads.nodes[x] for x in path], drawProp)

        path = self.getPath(origNode, reroutePlace.node)
        drawProp = (1.0, 0.0, 1.0, 0.5, 5.0)
        s.markPath([self.roads.nodes[x] for x in path], drawProp)

        path = self.getPath(reroutePlace.node, destNode)
        drawProp = (1.0, 0.0, 1.0, 0.5, 5.0)
        s.markPath([self.roads.nodes[x] for x in path], drawProp)

        # Draw nodes.
        drawProp = (0.0, 1.0, 0.0, 1.0, 5.0)
        s.markNode(self.roads.nodes[reroutePlace.node], drawProp)

        drawProp = (1.0, 0.0, 0.0, 1.0, 5.0)
        s.markNode(self.roads.nodes[sensNode], drawProp)

        return reroutePlace, s

    def distanceBetween(self, n1, n2):
        return self.router.distance(n1, n2)

    def getPath(self, n1, n2):
        key = (n1, n2)
        cacheFile = 'cached/%s' % str(key)
        status, path = None, None
        try:
            f = open(cacheFile, 'rb')
            status, path = pickle.load(f)
            f.close()
        except IOError:
            pass
        if not status:
            print 'Cache miss %s' % str(key)
        status, path = self.router.doRoute(n1, n2, 'car')
        f = open(cacheFile, 'wb')
        pickle.dump((status, path), f)
        f.close()
        return path

    def getPathDistance(self, path):
        pairs = zip(path[:-1], path[1:])
        return sum([self.distanceBetween(x, y) for x, y in pairs])

    def getToPlaceWeight(self, orig, sens, dest, altr):
        orig_sens = self.getPath(orig, sens)
        sens_dest = self.getPath(sens, dest)
        orig_altr = self.getPath(orig, altr)
        altr_dest = self.getPath(altr, dest)

        # How similar is the path?
        sim = \
            (self.getPathDistance(orig_sens) + \
             self.getPathDistance(sens_dest)) - \
            (self.getPathDistance(orig_altr) + \
             self.getPathDistance(altr_dest))
        rv = scipy.stats.norm(loc=0.0, scale=0.01)

        funcOverlap = lambda A,B: 2.0 * len(A.intersection(B)) / (len(A) + len(B))
        from_orig_overlap = funcOverlap(set(orig_sens), set(orig_altr))
        to_dest_overlap = funcOverlap(set(sens_dest), set(altr_dest))
        print rv.pdf(sim) / 100.0, from_orig_overlap, to_dest_overlap

        return rv.pdf(sim) / 100.0 + from_orig_overlap + to_dest_overlap

if __name__ == '__main__':
    startPlace = 358793909L  # seeds school
    endPlace = 358819756L  # hospital in santa monica
    endPlace2 = 358783700L  # emerson middle school

    ra = RouteAdder()
    ra.init()
    startNode = ra.places[startPlace].node
    endNode = ra.places[endPlace].node
    reroutePlace, s = ra.analyze([ra.places[p].node for p in [358793909L, 358819756L, 358783700L]])
    s.writePng('data/routeAdderOutput.png')
