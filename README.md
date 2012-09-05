### RouteAdder
'Making sure car rides always end at a public place. For privacy!'

Experiments using python and open street maps data that aims to
heuristically reroute trips so that they do not end up on a sensitive place
like a hospital.

#### Dependencies: `cairo, numpy, scipy`

###### On OSX:
1.  Install cairo: `brew install py2cairo`
2.  Set `PYTHONPATH=/usr/local/lib/python2.7/site-packages:$PYTHONPATH`
3.  Install scipy superpack: 
    `git clone https://github.com/fonnesbeck/ScipySuperpack && install_superpack.sh`
