import sys
import math
#import site
#site.addsitedir('/usr/local/lib/python2.7/site-packages/')

import cairo


class MapSurface:
    def __init__(self):
        self.minLon = 180
        self.minLat = 90
        self.maxLon = -180
        self.maxLat = -90

    def setup(self, loc, scale, pixels):
        """
        Sets up surface.

        loc -- (lat, lon) of the center point.
        scale -- the bigger this is, the more the map zooms-in.
        pixels -- the map image is pixels^2 size.
        """
        self.w = pixels
        self.h = pixels
        lat, lon = loc
        self.clat = lat
        self.clon = lon
        self.dlat = -(self.maxLat - self.minLat) / float(scale)
        self.dlon = -(self.maxLon - self.minLon) / float(scale)

        self.surface = \
            cairo.ImageSurface(cairo.FORMAT_RGB24, self.w, self.h)
        self.ctx = cairo.Context(self.surface)

    def project(self, (lat, lon)):
        """Convert from lat/long to image coordinates"""
        x = self.w * (0.5 + 0.5 * (lon - self.clon) / (0.5 * self.dlon))
        y = self.h * (0.5 - 0.5 * (lat - self.clat) / (0.5 * self.dlat))
        return (x, y)

    def markNode(self, n, prop):
        """Mark a node on the map."""
        self.markNodes((n,), prop)

    def markNodes(self, nodes, (r, g, b, a, size)):
        """Mark a node on the map."""
        self.ctx.set_line_width(size)
        self.ctx.set_source_rgba(r, g, b, a)
        for ll in nodes:
            x, y = self.project(ll)
            self.ctx.arc(x, y, size, 0, (size * math.pi))
            self.ctx.fill()

    def writText(self, (x, y), text, (r, g, b, a, size)):
        self.ctx.set_source_rgba(r, g, b, a)
        self.ctx.set_font_size(size)
        self.ctx.select_font_face(
            "Menlo", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        self.ctx.move_to(x, y)
        self.ctx.show_text(text)

    def markPath(self, path, (r, g, b, a, width)):
        self.ctx.set_source_rgba(r, g, b, a)
        self.ctx.set_line_width(width)
        pairs = zip(path[:-1], path[1:])
        for (n1, n2) in pairs:
            x, y = self.project(n1)
            self.ctx.move_to(x, y)
            x, y = self.project(n2)
            self.ctx.line_to(x, y)
            self.ctx.stroke()

    def markLine(self, n1, n2, prop):
        """Draw a line on the map between two nodes"""
        markPath((n1, n2), prop)

    def writePng(self, fileName):
        self.surface.write_to_png(fileName)

    def dumpOsm(fout, nodes):
        fout.write("<?xml version='1.0' encoding='UTF-8'?>")
        fout.write("<osm version='0.5' generator='route.py'>")
        for node in nodes:
            fout.write("<node id='%d' lat='%f' lon='%f'>\n</node>\n" % (
                node.id, node.lat, node.lon))
            fout.write("<way id='1'>\n")
        for node in nodes:
            fout.write("<nd ref='%d' lat='%f' lon='%f' />\n" % (
                node.id, node.lat, node.lon))
            fout.write("</way>\n")
        fout.write("</osm>")
        fout.close()
