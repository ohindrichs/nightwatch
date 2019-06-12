import numpy as np
import jinja2
import bokeh
import desimodel.io

from bokeh.embed import components
from bokeh.layouts import layout

import bokeh.plotting as bk
from bokeh.models import ColumnDataSource
from astropy.table import Table, join

from ..plots.fiber import plot_fibers
from ..plots.camfiber import plot_per_camfiber


def write_camfiber_html(outfile, data, header):
    '''TODO: document'''

    night = header['NIGHT']
    expid = header['EXPID']
    flavor = header['FLAVOR'].rstrip()
    if "PROGRAM" not in header :
        program = "no program in header!"
    else :
        program = header['PROGRAM'].rstrip()
    exptime = header['EXPTIME']

    env = jinja2.Environment(
        loader=jinja2.PackageLoader('qqa.webpages', 'templates')
    )
    template = env.get_template('camfiber.html')

    html_components = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, zexpid='{:08d}'.format(expid),
        flavor=flavor, program=program, qatype = 'camfiber',
    )

    #- List of attributes to plot per camfiber with default arguments
    ATTRIBUTES = ['INTEG_RAW_FLUX', 'MEDIAN_RAW_FLUX', 'MEDIAN_RAW_SNR', 'INTEG_CALIB_FLUX',
                 'MEDIAN_CALIB_FLUX', 'MEDIAN_CALIB_SNR']

    #- Default cameras and percentile ranges for camfiber plots
    CAMERAS = ['B', 'R', 'Z']
    PERCENTILES = {'B':(0, 95), 'R':(0, 95), 'Z':(0, 98)}
    TITLES = {'INTEG_RAW_FLUX':'Integrated Raw Counts', 'MEDIAN_RAW_FLUX':'Median Raw Counts',
              'MEDIAN_RAW_SNR':'Median S/N', 'INTEG_CALIB_FLUX':'Integrated Calibration Flux',
              'MEDIAN_CALIB_FLUX':'Median Calibration Flux', 'MEDIAN_CALIB_SNR':
              'Median Calibration S/N'}
    TITLESPERCAM = {'B':TITLES}
    TOOLS = 'box_select,reset'


    #- Gets a shared ColumnDataSource of DATA
    cds = create_cds(data, ATTRIBUTES)

    #- Gets the gridplots for each metric in ATTRIBUTES
    gridlist = []
    for attr in ATTRIBUTES:
        metric_grid = plot_per_camfiber(cds, attr, CAMERAS, html_components, percentiles=PERCENTILES,
            titles=TITLESPERCAM, tools=TOOLS)
        gridlist.append(metric_grid)

    #- Organizes the layout of the plots
    camfiber_layout = layout(children=gridlist)

    #- Gets the html components of the camfiber plots
    script, div = components(camfiber_layout)
    html_components['METRIC_PLOTS'] = dict(script=script, div=div)

    #- Combine template + components -> HTML
    html = template.render(**html_components)

    #- Write HTML text to the output file
    with open(outfile, 'w') as fx:
        fx.write(html)

    return html_components


def create_cds(data, attributes):
    '''
    Creates a ColumnDataSource object from DATA
    Args:
        data : a fits file of camfib data collected
        attributes : a list of metrics

    Returns a bokeh ColumnDataSource object
    '''
    #- Get the positions of the fibers on the focal plane
    fiberpos = Table(desimodel.io.load_fiberpos())
    fiberpos.remove_column('SPECTRO')

    #- Join the metrics data with the corresponding fibers
    #- TODO: use input fibermap instead
    data = Table(data)
    if len(data) > 0:
        data = join(data, fiberpos, keys='FIBER')

        #- bytes vs. strings
        for colname in data.colnames:
            if data[colname].dtype.kind == 'S':
                data[colname] = data[colname].astype(str)

    data_dict = dict({})
    for colname in data.dtype.names:
        if colname in attributes:
            data_dict[colname] = data[colname].astype(np.float32)
        else:
            data_dict[colname] = data[colname]
    cds = ColumnDataSource(data=data_dict)

    return cds
