import numpy as np
import fitsio
import os, fnmatch
import jinja2
from jinja2 import select_autoescape
import bokeh
import desimodel.io

from bokeh.embed import components
from bokeh.layouts import gridplot, layout

import bokeh.plotting as bk
from bokeh.models import ColumnDataSource
from bokeh.models import Panel, Tabs, Div
from astropy.table import Table, join, vstack, hstack

from ..plots.camfiber import plot_camfib_focalplane, plot_per_fibernum, plot_camfib_fot, plot_camfib_posacc
from .placeholder import handle_failed_plot


def write_camfiber_html(outfile, data, header):
    '''
    Args:
        outfile : output directory for generated html file
        data : fits file of per_camfiber data
        header : fits file header

    Writes the default generated fibernum camfiber plots to OUTFILE
    Also generates and writes an alternate view of focalplane camfiber plots
    Returns a components dictionary of summary camfiber plots
    '''
    #- Default plot options
    ATTRIBUTES = ['INTEG_RAW_FLUX', 'MEDIAN_RAW_FLUX', 'MEDIAN_RAW_SNR', 'INTEG_CALIB_FLUX',
                 'MEDIAN_CALIB_FLUX', 'MEDIAN_CALIB_SNR']
    CAMERAS = ['B', 'R', 'Z']
    PERCENTILES = {'B':(2.5, 97.5), 'R':(2.5, 97.5), 'Z':(2.5, 97.5)}
    TITLES = {'INTEG_RAW_FLUX':'Integrated Raw Counts', 'MEDIAN_RAW_FLUX':'Median Raw Counts',
              'MEDIAN_RAW_SNR':'Median Raw S/N', 'INTEG_CALIB_FLUX':'Integrated Calibrated Flux',
              'MEDIAN_CALIB_FLUX':'Median Calibrated Flux', 'MEDIAN_CALIB_SNR':'Median Calibrated S/N',
              'ON_TARGET': 'Fibers With Median (S/N) > 1 (Blue)'}
    TITLESPERCAM = {'B':TITLES}
    TOOLS = 'pan,box_zoom,tap,reset'

    
    #- Sets environment to get get templates
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('nightwatch.webpages', 'templates'),
        autoescape=select_autoescape(disabled_extensions=('txt',),
                                     default_for_string=True, 
                                     default=True)
    )

    #- FIBERNUM PLOTS (default camfiber page)
    fn_template = env.get_template('fibernum.html')
    try:
        write_fibernum_plots(data, fn_template, outfile, header, ATTRIBUTES, CAMERAS, TITLESPERCAM, TOOLS)
    except Exception as err:
        handle_failed_plot(outfile, header, 'PER_CAMFIBER')

    #- FOCALPLANE PLOTS
    index_fp_file = outfile.index('.html')
    fp_outfile = outfile[:index_fp_file] + '-focalplane_plots.html'
    fp_template = env.get_template('focalplane.html')
    try:
        write_focalplane_plots(data, fp_template, fp_outfile, header, ATTRIBUTES, CAMERAS, PERCENTILES, TITLESPERCAM, TOOLS)
    except Exception as err:
        handle_failed_plot(fp_outfile, header, 'PER_CAMFIBER')

    #- POSITIONER ACCURACY PLOTS
    index_pa_file = outfile.index('.html')
    pa_outfile = outfile[:index_pa_file] + '-posacc_plots.html'
    pa_template = env.get_template('posacc.html')
    try:
        write_posacc_plots(data, pa_template, pa_outfile, header, ATTRIBUTES, CAMERAS, PERCENTILES, TITLESPERCAM, TOOLS)
    except Exception as err:
        handle_failed_plot(pa_outfile, header, 'PER_CAMFIBER')

    return dict({})


def write_fibernum_plots(data, template, outfile, header, ATTRIBUTES, CAMERAS,
        TITLESPERCAM, TOOLS='pan,box_select,reset'):
    '''
    Args:
        data : fits file of per_camfiber data
        template : html template
        outfile : output directory for generated html file
        header : fits file header
        ATTRIBUTES : list of attributes to plot
        CAMERAS : list of camera filters to plot
        TITLESPERCAM : titles for plots
        TOOLS : supported features
        
    Writes the fibernum plots to OUTFILE
    '''
    #- Gets a shared ColumnDataSource of DATA
    cds = get_cds(data, ATTRIBUTES, CAMERAS)

    #- Gets the plot list for each metric in ATTRIBUTES
    fibernum_gridlist = []
    for attr, title in zip(ATTRIBUTES, TITLESPERCAM['B']):
        if attr in list(cds.data.keys()):
            figs_list = layout(plot_per_fibernum(cds, attr, CAMERAS, titles=TITLESPERCAM, tools=TOOLS, width=800, height=150))
            plot_title = title.replace('_', ' ').title().replace('Snr', 'SNR')
            tab = Panel(child=figs_list, title=plot_title)
            fibernum_gridlist.append(tab)

    #- Organizes the layout of the plots
    fn_camfiber_layout = Tabs(tabs=fibernum_gridlist)

    #- Writes the htmlfile
    write_file = write_htmlfile(fn_camfiber_layout, template, outfile, header)


def write_focalplane_plots(data, template, outfile, header,
        ATTRIBUTES, CAMERAS, PERCENTILES, TITLESPERCAM,
        TOOLS='pan,box_select,reset'):
    '''
    Args:
        data : fits file of per_camfiber data
        template : html template
        outfile : output directory for generated html file
        header : fits file header
        ATTRIBUTES : list of attributes to plot
        CAMERAS : list of camera filters to plot
        PERCENTILES : list of percentiles to clip histogram data per camera
        TITLESPERCAM : titles for plots
        TOOLS : supported features
        
    Writes the focalplane plots to OUTFILE
    '''
    #- Gets a shared ColumnDataSource of DATA
    cds = get_cds(data, ATTRIBUTES, CAMERAS)

    #- Gets the plot list for each metric in ATTRIBUTES
    focalplane_gridlist = []
    for attr, title in zip(ATTRIBUTES, TITLESPERCAM['B']):
        if attr in list(cds.data.keys()):
            figs_list, hfigs_list = plot_camfib_focalplane(cds, attr, CAMERAS, percentiles=PERCENTILES, titles=TITLESPERCAM, tools=TOOLS)
            plot_title = title.replace('_', ' ').title().replace('Snr', 'SNR')

            gp = gridplot([figs_list, hfigs_list], toolbar_location='right')
            tab = Panel(child=gp, title=plot_title)
            focalplane_gridlist.append(tab)

    #- Organizes the layout of the plots
    fp_camfiber_layout = Tabs(tabs=focalplane_gridlist)

    #- Writes the htmlfile
    write_file = write_htmlfile(fp_camfiber_layout, template, outfile, header)


def write_posacc_plots(data, template, outfile, header,
        ATTRIBUTES, CAMERAS, PERCENTILES, TITLESPERCAM,
        TOOLS='pan,box_select,reset',pos_acc=True):
    '''
    Args:
        data : fits file of per_camfiber data
        template : html template
        outfile : output directory for generated html file
        header : fits file header
        ATTRIBUTES : list of attributes to plot
        CAMERAS : list of camera filters to plot
        PERCENTILES : list of percentiles to clip histogram data per camera
        TITLESPERCAM : titles for plots
        TOOLS : supported features
        pos_acc : Option to not include the POsitioner Accuracy plots

    Writes the focalplane plots to OUTFILE
    '''
    focalplane_gridlist = []

    #- Gets a shared ColumnDataSource of for just our ON-TARGET attribute 
    cds = get_cds(data,['ON_TARGET'], CAMERAS)

    figs_list = plot_camfib_fot(cds, 'ON_TARGET', CAMERAS, percentiles=PERCENTILES,
                                     titles=TITLESPERCAM, tools=TOOLS)
    focalplane_gridlist.extend([figs_list])

    #- Positioner Accuracy Plots
    pa_camfiber_layout = None

    if pos_acc:
        pcd = get_posacc_cd(header)
        if pcd is not None:
            posplots = []
            for attr, plot_title in zip(['BLIND','FINAL_MOVE'], ['Blind Move', 'Final Move']):
                figs_list,hfigs_list = plot_camfib_posacc(pcd, attr, percentiles=PERCENTILES, tools=TOOLS)
                gp = gridplot([figs_list, hfigs_list], toolbar_location='right')
                tab = Panel(child=gp, title=plot_title)
                posplots.append(tab)

            #- Put positioner accuracy moves into tabs.
            posacc_camfiber_layout = Tabs(tabs=posplots)

            #- Add text to explain the positioner moves.
            div = Div(text="""
                <p>Select <strong>Blind</strong> or <strong>Final</strong> Move
                tabs to view positioner accuracy.<br />
                Note turbulence or large (>5 um RMS) final moves.</p>
                """, width=400, height=65)

            #- Organize the layout of the plots
            pa_camfiber_layout = layout([
                gridplot(focalplane_gridlist, toolbar_location='right'),
                div,
                posacc_camfiber_layout])

    #- Fall-through case (no positioner plots available):
    #- organize the layout of fiber-on-target plots
    if pa_camfiber_layout is None:
        pa_camfiber_layout = gridplot(focalplane_gridlist, toolbar_location='right')

    #- Write the htmlfile
    write_file = write_htmlfile(pa_camfiber_layout, template, outfile, header)


def get_posacc_cd(header):
    '''
    Creates column data source from coordinates.fits file
    Merges coordinate data with fiberpos data for X,Y plotting
    Args:
        header : from data file
    '''
    fiberpos = Table(desimodel.io.load_fiberpos()).to_pandas()
    fiberpos.PETAL = fiberpos.PETAL.astype(int)
    fiberpos.DEVICE = fiberpos.DEVICE.astype(int)
    fiberpos.DEVICE_TYPE = fiberpos.DEVICE_TYPE.astype(str)
    night = header['NIGHT']
    expid = header['EXPID']
    coordfile = '{}/{}/coordinates-{}.fits'.format(night, str(expid).zfill(8), str(expid).zfill(8))

    # Useful for offline tests: backup location for coordfiles at NERSC.
    if not os.path.exists(coordfile):
        if 'DESI_SPECTRO_DATA' in os.environ:
            coordfile = os.path.join(os.environ['DESI_SPECTRO_DATA'], coordfile)

    if os.path.isfile(coordfile):
        df = Table(fitsio.read(coordfile)).to_pandas()

        # delete a conflicting column name
        if 'FIBER' in df:
            del df['FIBER']

        if 'OFFSET_0' not in df:
            print(f'WARNING positioner offsets not in {coordfile}; not making positioner accuracy plots')
            return None

        final_move = np.sort(fnmatch.filter(df.columns, 'OFFSET_*'))[-1]
        df = df.merge(fiberpos, how='left',left_on=['PETAL_LOC','DEVICE_LOC'], right_on=['PETAL','DEVICE'])
        df = df[df['DEVICE_TYPE'] == "b'POS'"]
        df.reset_index(drop=True,inplace=True)
        print(len(df))
        df['DISABLED_0'] = True
        df['DISABLED_1'] = True
        for i in [0,1]:
            try:
                flag = 'FLAGS_COR_{}'.format(i)
                x = np.where(((df[flag] & 4) != 0) & (df[flag] < 65535))
                df.loc[x[0], ('DISABLED_{}').format(i)] = False
            except Exception as e:
                print('Issue setting disabled positioners: ',e)
        
        
        df['BLIND'] = df['OFFSET_0']*1000
        df['FINAL_MOVE'] = df[final_move]*1000

        mask = df['DISABLED_0'] == True
        df.loc[mask, 'BLIND'] = -1

        mask = df['DISABLED_1'] == True
        df.loc[mask, 'FINAL_MOVE'] = -1

        df['CAM'] = ''
        df = df.fillna(-1)
        return ColumnDataSource(data=df)
    else:
        return None


def get_cds(data, attributes, cameras):
    '''
    Creates a column data source from DATA
    Args:
        data : a fits file of camfib data collected
        attributes : a list of metrics
        cameras : a list of cameras
    Options:
    	agg : get an aggregated column data source
    		to plot per fiber number instead of
    		focal plane

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

    cds = create_cds(data, attributes)
    return cds


def create_cds(data, attributes, bin_size=25):
    '''
    Creates a column data source from DATA with metrics in ATTRIBUTES
    Args:
        data : an astropy table of camfib data collected
        attributes : a list of metrics
    '''
    data_dict = dict({})

    for colname in data.dtype.names:
        if colname in attributes:
            data_dict[colname] = data[colname].astype(np.float32)
        else:
            data_dict[colname] = data[colname]

    #- Create ON_TARGET attribute with SNR > 1. Prefer to use CALIB_SNR
    if 'ON_TARGET' in attributes:
        if 'MEDIAN_CALIB_SNR' in data.dtype.names:
            attr = 'MEDIAN_CALIB_SNR'
        elif 'MEDIAN_RAW_SNR' in data.dtype.names:
            attr = 'MEDIAN_RAW_SNR'
        try:
            d = np.array(data[attr])
            on_target = np.where(d>1)
            new_d = np.zeros(len(d))
            new_d[on_target] = 1
            data_dict['ON_TARGET'] = new_d
        except:
            print("Didn't add ON TARGET")


    cds = ColumnDataSource(data=data_dict)
    return cds


def write_htmlfile(layout, template, outfile, header):
    '''
    Args:
        layout : bokeh layout object of plot figures
        template : html template
        outfile : outfile directory
        header : fits file header
    
    Writes the LAYOUT of plots to OUTFILE
    '''
    night = header['NIGHT']
    expid = header['EXPID']
    if 'OBSTYPE' in header :
        obstype = header['OBSTYPE'].rstrip().upper()
    else :
        log.warning('Use FLAVOR instead of missing OBSTYPE')
        obstype = header['FLAVOR'].rstrip().upper()
    if "PROGRAM" not in header :
        program = "no program in header!"
    else :
        program = header['PROGRAM'].rstrip()
    exptime = header['EXPTIME']
    focalplane = 'focalplane_plots' in outfile
    positioning = 'posacc_plots' in outfile

    # Fill components dictionary for use in webpages.
    components_dict = dict(
        bokeh_version=bokeh.__version__, exptime='{:.1f}'.format(exptime),
        night=night, expid=expid, zexpid='{:08d}'.format(expid),
        obstype=obstype, program=program, qatype='camfiber',
        focalplane=focalplane, positioning=positioning, num_dirs=2,
    )

    # Add sky coordinates if they are present in header.
    if obstype == 'SCIENCE':
        if 'TILEID' in header and 'SKYRA' in header and 'SKYDEC' in header:
            components_dict['TILEID'] = header['TILEID']
            components_dict['SKYRA'] = header['SKYRA']
            components_dict['SKYDEC'] = header['SKYDEC']

    script, div = components(layout)
    components_dict['CAMFIBER_PLOTS'] = dict(script=script, div=div)
    html_camfib = template.render(**components_dict)

    #- Write HTML text to the output files
    with open(outfile, 'w') as fx:
        fx.write(html_camfib)
