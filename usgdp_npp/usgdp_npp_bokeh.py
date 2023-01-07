'''
This module downloads the U.S. real GDP seasonally adjusted (GDPC1, billions
of chained 2012 dollars, at annual rate) quarterly time series from the St.
Louis Federal Reserve's FRED system
(https://fred.stlouisfed.org/series/GDPC1) or loads it from this directory and
organizes it into 15 series, one for each of the last 15 recessions--from the
current 2020 Coronavirus recession to the Great Depression of 1929. It then
creates a normalized peak plot of the GDPC1 data for each of the last 15
recessions using the Bokeh plotting library.

This module defines the following function(s):
    get_usgdp_data()
    usgdp_npp()
'''
# Import packages
import numpy as np
import pandas as pd
import pandas_datareader as pddr
import datetime as dt
import os
from bokeh.io import output_file
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, Title, Legend, HoverTool

# from bokeh.models import Label
from bokeh.palettes import Category20

'''
Define functions
'''


def get_usgdp_data(frwd_qtrs_max, bkwd_qtrs_max, end_date_str,
                   download_from_internet=True):
    '''
    This function either downloads or reads in the U.S. real GDP seasonally
    adjusted quarterly data series (GDPC1) and adds variables qtrs_frm_peak and
    gdp_dv_pk for each of the last 15 recessions.

    Args:
        frwd_qtrs_max (int): maximum number of quarters forward from the peak
            quarter to plot
        bckwd_qtrs_max (int): maximum number of quarters backward from the peak
            quarter to plot
        end_date_str (str): end date of GDPC1 time series in 'YYYY-mm-dd'
            format
        download_from_internet (bool): =True if download data from
            fred.stlouisfed.org, otherwise read data in from local directory

    Other functions and files called by this function:
        usgdp_[yyyy-mm-dd].csv

    Files created by this function:
        usgdp_[yyyy-mm-dd].csv
        usgdp_pk_[yyyy-mm-dd].csv

    Returns:
        usgdp_pk (DataFrame): N x 46 DataFrame of qtrs_frm_peak, Date{i},
            Close{i}, and close_dv_pk{i} for each of the 15 recessions for the
            periods specified by bkwd_qtrs_max and frwd_qtrs_max
        end_date_str2 (str): actual end date of GDPC1 time series in
            'YYYY-mm-dd' format. Can differ from the end_date input to this
            function if the final data for that day have not come out yet
            (usually 2 hours after markets close, 6:30pm EST), or if the
            end_date is one on which markets are closed (e.g. weekends and
            holidays). In this latter case, the pandas_datareader library
            chooses the most recent date for which we have DJIA data.
        peak_vals (list): list of peak DJIA value at the beginning of each of
            the last 15 recessions
        peak_dates (list): list of string date (YYYY-mm-dd) of peak DJIA value
            at the beginning of each of the last 15 recessions
        rec_label_yr_lst (list): list of string start year and end year of each
            of the last 15 recessions
        rec_label_yrmth_lst (list): list of string start year and month and end
            year and month of each of the last 15 recessions
        rec_beg_yrmth_lst (list): list of string start year and month of each
            of the last 15 recessions
        maxdate_rng_lst (list): list of tuples with start string date and end
            string date within which range we define the peak DJIA value at the
            beginning of each of the last 15 recessions
    '''
    end_date = dt.datetime.strptime(end_date_str, '%Y-%m-%d')

    # Name the current directory and make sure it has a data folder
    cur_path = os.path.split(os.path.abspath(__file__))[0]
    data_fldr = 'data'
    data_dir = os.path.join(cur_path, data_fldr)
    if not os.access(data_dir, os.F_OK):
        os.makedirs(data_dir)

    filename_basic = ('data/usgdp_' + end_date_str + '.csv')
    filename_full = ('data/usgdp_pk_' + end_date_str + '.csv')

    if download_from_internet:
        # Download the employment data directly from fred.stlouisfed.org
        # (requires internet connection)
        start_date = dt.datetime(1947, 1, 1)
        usgdp_df = pddr.fred.FredReader(symbols='GDPC1', start=start_date,
                                        end=end_date).read()
        usgdp_df = pd.DataFrame(usgdp_df).sort_index()  # Sort old to new
        usgdp_df = usgdp_df.reset_index(level=['DATE'])
        usgdp_df = usgdp_df.rename(columns={'DATE': 'Date'})
        end_date_str2 = usgdp_df['Date'].iloc[-1].strftime('%Y-%m-%d')
        end_date = dt.datetime.strptime(end_date_str2, '%Y-%m-%d')
        filename_basic = ('data/usgdp_' + end_date_str2 + '.csv')
        filename_full = ('data/usgdp_pk_' + end_date_str2 + '.csv')
        usgdp_df.to_csv(filename_basic, index=False)
        # Merge in U.S. annual real GDP (GDPCA, not seasonally adjusted,
        # billions of 2012 chained dollars, annual rate) 1929-1946. Earliest
        # year from FRED for this series is 1929, so cannot do pre-recession.
        # Date values for annual data are set to July 1 of that year.
        filename_annual = ('data/usgdp_annual_1929-1946.csv')
        ann_data_file_path = os.path.join(cur_path, filename_annual)
        usgdp_ann_df = \
            pd.read_csv(ann_data_file_path, names=['Date', 'GDPC1'],
                        parse_dates=['Date'], skiprows=1,
                        na_values=['.', 'na', 'NaN'])
        usgdp_df = usgdp_df.append(usgdp_ann_df, ignore_index=True)
        usgdp_df = usgdp_df.sort_values(by='Date')
        usgdp_df = usgdp_df.reset_index(drop=True)
        # Add other months to annual data 1919-01-01 to 1938-12-01 and fill in
        # artificial employment data by cubic spline interpolation
        quarters_df = \
            pd.DataFrame(pd.date_range('1929-07-01', '1946-10-01', freq='QS'),
                         columns=['Date'])
        usgdp_df = pd.merge(usgdp_df, quarters_df, left_on='Date',
                            right_on='Date', how='outer')
        usgdp_df = usgdp_df.sort_values(by='Date')
        usgdp_df = usgdp_df.reset_index(drop=True)
        usgdp_df['GDPC1'].iloc[:71] = \
            usgdp_df['GDPC1'].iloc[:71].interpolate(method='cubic')
        usgdp_df.to_csv(filename_basic, index=False)
    else:
        # Import the data as pandas DataFrame
        end_date_str2 = end_date_str
        data_file_path = os.path.join(cur_path, filename_basic)
        usgdp_df = pd.read_csv(data_file_path, names=['Date', 'GDPC1'],
                                parse_dates=['Date'], skiprows=1,
                                na_values=['.', 'na', 'NaN'])
        usgdp_df = usgdp_df.dropna()

    print('End date of U.S. real GDP series is',
          end_date.strftime('%Y-%m-%d'))

    # Set recession-specific parameters
    rec_label_yr_lst = \
        ['1929-1933',  # (Aug 1929 - Mar 1933) Great Depression
         '1937-1938',  # (May 1937 - Jun 1938)
         '1945',       # (Feb 1945 - Oct 1945)
         '1948-1949',  # (Nov 1948 - Oct 1949)
         '1953-1954',  # (Jul 1953 - May 1954)
         '1957-1958',  # (Aug 1957 - Apr 1958)
         '1960-1961',  # (Apr 1960 - Feb 1961)
         '1969-1970',  # (Dec 1969 - Nov 1970)
         '1973-1975',  # (Nov 1973 - Mar 1975)
         '1980',       # (Jan 1980 - Jul 1980)
         '1981-1982',  # (Jul 1981 - Nov 1982)
         '1990-1991',  # (Jul 1990 - Mar 1991)
         '2001',       # (Mar 2001 - Nov 2001)
         '2007-2009',  # (Dec 2007 - Jun 2009) Great Recession
         '2020-2020']  # (Feb 2020 - Apr 2020) Coronavirus recession

    rec_label_yrmth_lst = ['Aug 1929 - Mar 1933',  # Great Depression
                           'May 1937 - Jun 1938',
                           'Feb 1945 - Oct 1945',
                           'Nov 1948 - Oct 1949',
                           'Jul 1953 - May 1954',
                           'Aug 1957 - Apr 1958',
                           'Apr 1960 - Feb 1961',
                           'Dec 1969 - Nov 1970',
                           'Nov 1973 - Mar 1975',
                           'Jan 1980 - Jul 1980',
                           'Jul 1981 - Nov 1982',
                           'Jul 1990 - Mar 1991',
                           'Mar 2001 - Nov 2001',
                           'Dec 2007 - Jun 2009',  # Great Recession
                           'Feb 2020 - Apr 2020']  # Coronavirus recess'n

    rec_beg_yrmth_lst = ['Aug 1929', 'May 1937', 'Feb 1945', 'Nov 1948',
                         'Jul 1953', 'Aug 1957', 'Apr 1960', 'Dec 1969',
                         'Nov 1973', 'Jan 1980', 'Jul 1981', 'Jul 1990',
                         'Mar 2001', 'Dec 2007', 'Feb 2020']

    maxdate_rng_lst = [('1929-7-1', '1929-10-1'),
                       ('1937-4-1', '1937-10-1'),
                       ('1945-1-1', '1945-4-1'),
                       ('1948-7-1', '1949-1-1'),
                       ('1953-4-1', '1953-7-1'),
                       ('1957-7-1', '1957-10-1'),
                       ('1960-1-1', '1960-4-1'),
                       ('1969-7-1', '1970-1-1'),
                       ('1973-10-1', '1974-1-1'),
                       ('1979-10-1', '1980-4-1'),
                       ('1981-4-1', '1981-10-1'),
                       ('1990-4-1', '1991-10-1'),
                       ('2001-1-1', '2001-7-1'),
                       ('2007-7-1', '2008-1-1'),
                       ('2019-10-1', '2020-3-1')]

    # Create normalized peak series for each recession
    usgdp_pk = \
        pd.DataFrame(np.arange(-bkwd_qtrs_max, frwd_qtrs_max + 1, dtype=int),
                     columns=['qtrs_frm_peak'])
    usgdp_pk_long = usgdp_df.copy()
    peak_vals = []
    peak_dates = []
    for i, maxdate_rng in enumerate(maxdate_rng_lst):
        # Identify peak real GDP value within one quarter of beginning moth of
        # the recession
        peak_val = \
            usgdp_df['GDPC1'][(usgdp_df['Date'] >= maxdate_rng[0]) &
                                (usgdp_df['Date'] <= maxdate_rng[1])].max()
        peak_vals.append(peak_val)
        usgdp_dv_pk_name = 'usgdp_dv_pk' + str(i)
        usgdp_pk_long[usgdp_dv_pk_name] = usgdp_pk_long['GDPC1'] / peak_val
        # Identify date of peak real GDP value within one quarter of the
        # beginning month of the recession
        peak_date = \
            usgdp_df['Date'][(usgdp_df['Date'] >= maxdate_rng[0]) &
                              (usgdp_df['Date'] <= maxdate_rng[1]) &
                              (usgdp_df['GDPC1'] == peak_val)].max()
        peak_dates.append(peak_date.strftime('%Y-%m-%d'))
        qtrs_frm_pk_name = 'qtrs_frm_pk' + str(i)
        usgdp_pk_long[qtrs_frm_pk_name] = \
            ((usgdp_pk_long['Date'].dt.year - peak_date.year) * 4 +
             ((usgdp_pk_long['Date'].dt.month - peak_date.month) / 3))
        # usempl_pk_long[mths_frm_pk_name] = (usempl_pk_long['Date'] -
        #                                     peak_date).dt.years
        print('peak_val ' + str(i) + ' is', peak_val, 'on quarter',
              peak_date.strftime('%Y-%m-%d'), '(Beg. rec. month:',
              rec_beg_yrmth_lst[i], ')')
        # I need to merge the data into this new usgdp_pk DataFrame so that
        # qtrs_frm_peak variable is shared across the dataframe
        usgdp_pk = \
            pd.merge(usgdp_pk,
                     usgdp_pk_long[[qtrs_frm_pk_name, 'Date', 'GDPC1',
                                    usgdp_dv_pk_name]],
                     left_on='qtrs_frm_peak', right_on=qtrs_frm_pk_name,
                     how='left')
        usgdp_pk.drop(columns=[qtrs_frm_pk_name], inplace=True)
        usgdp_pk.rename(
            columns={'Date': f'Date{i}', 'GDPC1': f'GDPC1{i}'}, inplace=True)

    usgdp_pk.to_csv(filename_full, index=False)

    return (usgdp_pk, end_date_str2, peak_vals, peak_dates, rec_label_yr_lst,
            rec_label_yrmth_lst, rec_beg_yrmth_lst, maxdate_rng_lst)


def usgdp_npp(frwd_qtrs_main=11, bkwd_qtrs_main=3, frwd_qtrs_max=40,
              bkwd_qtrs_max=12, usgdp_end_date='today',
               download_from_internet=True, html_show=True):
    '''
    This function creates the HTML and JavaScript code for the dynamic
    visualization of the normalized peak plot of the last 15 recessions in the
    United States, from the Great Depression (Aug. 1929 - Mar. 1933) to the
    most recent COVID-19 recession (Feb. 2020 - present).

    Args:
        frwd_qtrs_main (int): number of quarterss forward from the peak to plot
            in the default main window of the visualization
        bkwd_qtrs_maim (int): number of quarters backward from the peak to plot
            in the default main window of the visualization
        frwd_qtrs_max (int): maximum number of quarters forward from the peak
            to allow for the plot, to be seen by zooming out
        bkwd_qtrs_max (int): maximum number of quarters backward from the peak
            to allow for the plot, to be seen by zooming out
        usgdp_end_date (str): either 'today' or the end date of GDPC1 time
            series in 'YYYY-mm-dd' format
        download_from_internet (bool): =True if download data from St. Louis
            Federal Reserve's FRED system
            (https://fred.stlouisfed.org/series/GDPC1), otherwise read data in
            from local directory
        html_show (bool): =True if open dynamic visualization in browser once
            created

    Other functions and files called by this function:
        get_usgdp_data()

    Files created by this function:
       images/usgdp_[yyyy-mm-dd].html

    Returns: fig, end_date_str
    '''
    # Create directory if images directory does not already exist
    cur_path = os.path.split(os.path.abspath(__file__))[0]
    image_fldr = 'images'
    image_dir = os.path.join(cur_path, image_fldr)
    if not os.access(image_dir, os.F_OK):
        os.makedirs(image_dir)

    if usgdp_end_date == 'today':
        end_date = dt.date.today()  # Go through today
    else:
        end_date = dt.datetime.strptime(usgdp_end_date, '%Y-%m-%d')

    end_date_str = end_date.strftime('%Y-%m-%d')

    # Set main window and total data limits for monthly plot
    frwd_qtrs_main = int(frwd_qtrs_main)
    bkwd_qtrs_main = int(bkwd_qtrs_main)
    frwd_qtrs_max = int(frwd_qtrs_max)
    bkwd_qtrs_max = int(bkwd_qtrs_max)

    (usgdp_pk, end_date_str2, peak_vals, peak_dates, rec_label_yr_lst,
        rec_label_yrmth_lst, rec_beg_yrmth_lst, maxdate_rng_lst) = \
        get_usgdp_data(frwd_qtrs_max, bkwd_qtrs_max, end_date_str,
                       download_from_internet)
    if end_date_str2 != end_date_str:
        print('GDPC1 data downloaded on ' + end_date_str + ' has most ' +
              'recent GDPC1 data quarter of ' + end_date_str2 + '.')
    end_date2 = dt.datetime.strptime(end_date_str2, '%Y-%m-%d')

    rec_cds_list = []
    min_main_val_lst = []
    max_main_val_lst = []
    for i in range(15):
        usgdp_pk_rec = \
            usgdp_pk[['qtrs_frm_peak', f'Date{i}', f'GDPC1{i}',
                      f'usgdp_dv_pk{i}']].dropna()
        usgdp_pk_rec.rename(
            columns={f'Date{i}': 'Date', f'GDPC1{i}': 'GDPC1',
                     f'usgdp_dv_pk{i}': 'usgdp_dv_pk'}, inplace=True)
        rec_cds_list.append(ColumnDataSource(usgdp_pk_rec))
        # Find minimum and maximum usgdp_dv_pk values as inputs to main plot
        # frame size
        min_main_val_lst.append(
            usgdp_pk_rec['usgdp_dv_pk'][
                (usgdp_pk_rec['qtrs_frm_peak'] >= -bkwd_qtrs_main) &
                (usgdp_pk_rec['qtrs_frm_peak'] <= frwd_qtrs_main)].min())
        max_main_val_lst.append(
            usgdp_pk_rec['usgdp_dv_pk'][
                (usgdp_pk_rec['qtrs_frm_peak'] >= -bkwd_qtrs_main) &
                (usgdp_pk_rec['qtrs_frm_peak'] <= frwd_qtrs_main)].max())

    # Create Bokeh plot of GDPC1 normalized peak plot figure
    fig_title = 'Progression of GCPC1 in last 15 recessions'
    filename = ('images/usgdp_npp_' + end_date_str2 + '.html')
    output_file(filename, title=fig_title)

    # Format the tooltip
    tooltips = [('Date', '@Date{%F}'),
                ('Quarters from peak', '$x{0.}'),
                ('Real GDP', '$@GDPC1{0,0.}B'),
                ('Fraction of peak', '@usgdp_dv_pk{0.0 %}')]

    # Solve for minimum and maximum GDPC1/Peak values in quarterly main display
    # window in order to set the appropriate xrange and yrange
    min_main_val = min(min_main_val_lst)
    max_main_val = max(max_main_val_lst)

    datarange_main_vals = max_main_val - min_main_val
    datarange_main_qtrs = int(frwd_qtrs_main + bkwd_qtrs_main)
    fig_buffer_pct = 0.10
    fig = figure(plot_height=500,
                 plot_width=800,
                 x_axis_label='Quarters from Peak',
                 y_axis_label='Real GDP as fraction of Peak',
                 y_range=(min_main_val - fig_buffer_pct * datarange_main_vals,
                          max_main_val + fig_buffer_pct * datarange_main_vals),
                 x_range=((-bkwd_qtrs_main -
                           fig_buffer_pct * datarange_main_qtrs),
                          (frwd_qtrs_main +
                           fig_buffer_pct * datarange_main_qtrs)),
                 tools=['save', 'zoom_in', 'zoom_out', 'box_zoom',
                        'pan', 'undo', 'redo', 'reset', 'hover', 'help'],
                 toolbar_location='left')
    fig.title.text_font_size = '18pt'
    fig.toolbar.logo = None
    l0 = fig.line(x='qtrs_frm_peak', y='usgdp_dv_pk', source=rec_cds_list[0],
                  color='blue', line_width=5, alpha=0.7, muted_alpha=0.15)
    l1 = fig.line(x='qtrs_frm_peak', y='usgdp_dv_pk', source=rec_cds_list[1],
                  color=Category20[13][0], line_width=2, alpha=0.7,
                  muted_alpha=0.15)
    l2 = fig.line(x='qtrs_frm_peak', y='usgdp_dv_pk', source=rec_cds_list[2],
                  color=Category20[13][1], line_width=2, alpha=0.7,
                  muted_alpha=0.15)
    l3 = fig.line(x='qtrs_frm_peak', y='usgdp_dv_pk', source=rec_cds_list[3],
                  color=Category20[13][2], line_width=2,
                  alpha=0.7, muted_alpha=0.15)
    l4 = fig.line(x='qtrs_frm_peak', y='usgdp_dv_pk', source=rec_cds_list[4],
                  color=Category20[13][3], line_width=2, alpha=0.7,
                  muted_alpha=0.15)
    l5 = fig.line(x='qtrs_frm_peak', y='usgdp_dv_pk', source=rec_cds_list[5],
                  color=Category20[13][4], line_width=2, alpha=0.7,
                  muted_alpha=0.15)
    l6 = fig.line(x='qtrs_frm_peak', y='usgdp_dv_pk', source=rec_cds_list[6],
                  color=Category20[13][5], line_width=2, alpha=0.7,
                  muted_alpha=0.15)
    l7 = fig.line(x='qtrs_frm_peak', y='usgdp_dv_pk', source=rec_cds_list[7],
                  color=Category20[13][6], line_width=2, alpha=0.7,
                  muted_alpha=0.15)
    l8 = fig.line(x='qtrs_frm_peak', y='usgdp_dv_pk', source=rec_cds_list[8],
                  color=Category20[13][7], line_width=2, alpha=0.7,
                  muted_alpha=0.15)
    l9 = fig.line(x='qtrs_frm_peak', y='usgdp_dv_pk', source=rec_cds_list[9],
                  color=Category20[13][8], line_width=2, alpha=0.7,
                  muted_alpha=0.15)
    l10 = fig.line(x='qtrs_frm_peak', y='usgdp_dv_pk',
                   source=rec_cds_list[10], color=Category20[13][9],
                   line_width=2, alpha=0.7, muted_alpha=0.15)
    l11 = fig.line(x='qtrs_frm_peak', y='usgdp_dv_pk',
                   source=rec_cds_list[11], color=Category20[13][10],
                   line_width=2, alpha=0.7, muted_alpha=0.15)
    l12 = fig.line(x='qtrs_frm_peak', y='usgdp_dv_pk',
                   source=rec_cds_list[12], color=Category20[13][11],
                   line_width=2, alpha=0.7, muted_alpha=0.15)
    l13 = fig.line(x='qtrs_frm_peak', y='usgdp_dv_pk',
                   source=rec_cds_list[13], color=Category20[13][12],
                   line_width=2, alpha=0.7, muted_alpha=0.15)
    l14 = fig.line(x='qtrs_frm_peak', y='usgdp_dv_pk',
                   source=rec_cds_list[14], color='black', line_width=5,
                   alpha=0.7, muted_alpha=0.15)

    # Dashed vertical line at the peak PAYEMS value period
    fig.line(x=[0.0, 0.0], y=[-0.5, 2.4], color='black', line_width=2,
             line_dash='dashed', alpha=0.5)

    # Dashed horizontal line at PAYEMS as fraction of peak equals 1
    fig.line(x=[-bkwd_qtrs_max, frwd_qtrs_max], y=[1.0, 1.0],
             color='black', line_width=2, line_dash='dashed', alpha=0.5)

    # # Create the tick marks for the x-axis and set x-axis labels
    # major_tick_labels = []
    # major_tick_list = []
    # for i in range(-bkwd_mths_max, frwd_mths_max + 1):
    #     if i % 2 == 0:  # indicates even integer
    #         major_tick_list.append(int(i))
    #         if i < 0:
    #             major_tick_labels.append(str(i) + 'mth')
    #         elif i == 0:
    #             major_tick_labels.append('peak')
    #         elif i > 0:
    #             major_tick_labels.append('+' + str(i) + 'mth')

    # # minor_tick_list = [item for item in range(-bkwd_mths_max,
    # #                                           frwd_mths_max + 1)]
    # major_tick_dict = dict(zip(major_tick_list, major_tick_labels))
    # fig.xaxis.ticker = major_tick_list
    # fig.xaxis.major_label_overrides = major_tick_dict

    # Add legend
    legend = Legend(items=[(rec_label_yrmth_lst[0], [l0]),
                           (rec_label_yrmth_lst[1], [l1]),
                           (rec_label_yrmth_lst[2], [l2]),
                           (rec_label_yrmth_lst[3], [l3]),
                           (rec_label_yrmth_lst[4], [l4]),
                           (rec_label_yrmth_lst[5], [l5]),
                           (rec_label_yrmth_lst[6], [l6]),
                           (rec_label_yrmth_lst[7], [l7]),
                           (rec_label_yrmth_lst[8], [l8]),
                           (rec_label_yrmth_lst[9], [l9]),
                           (rec_label_yrmth_lst[10], [l10]),
                           (rec_label_yrmth_lst[11], [l11]),
                           (rec_label_yrmth_lst[12], [l12]),
                           (rec_label_yrmth_lst[13], [l13]),
                           (rec_label_yrmth_lst[14], [l14])],
                    location='center')
    fig.add_layout(legend, 'right')

    # # Add label to current recession low point
    # fig.text(x=[12, 12, 12, 12], y=[0.63, 0.60, 0.57, 0.54],
    #          text=['2020-03-23', 'DJIA: 18,591.93', '63.3% of peak',
    #                '39 days from peak'],
    #          text_font_size='8pt', angle=0)

    # label_text = ('Recent low \n 2020-03-23 \n DJIA: 18,591.93 \n '
    #               '63\% of peak \n 39 days from peak')
    # fig.add_layout(Label(x=10, y=0.65, x_units='screen', text=label_text,
    #                      render_mode='css', border_line_color='black',
    #                      border_line_alpha=1.0,
    #                      background_fill_color='white',
    #                      background_fill_alpha=1.0))

    # Add title and subtitle to the plot
    fig_title2 = 'Progression of U.S. Real GDP in last 15 recessions'
    fig_title3 = '(GDPC1, seasonally adjusted, $B 2012 chained)'
    fig.add_layout(Title(text=fig_title3, text_font_style='bold',
                         text_font_size='16pt', align='center'), 'above')
    fig.add_layout(Title(text=fig_title2, text_font_style='bold',
                         text_font_size='16pt', align='center'), 'above')

    # Add source text below figure
    updated_date_str = (
        end_date.strftime("%B")
        + " "
        + end_date.strftime("%d").lstrip("0")
        + ", "
        + end_date.strftime("%Y")
    )
    fig.ad
    fig.add_layout(Title(text='Source: Richard W. Evans (@RickEcon), ' +
                              'historical GDPC1 data from FRED, ' +
                              'updated ' + updated_date_str + '.',
                         align='left',
                         text_font_size='3mm',
                         text_font_style='italic'),
                   'below')
    fig.legend.click_policy = 'mute'

    # Add the HoverTool to the figure
    fig.add_tools(HoverTool(tooltips=tooltips, toggleable=False,
                            formatters={'@Date': 'datetime'}))

    if html_show:
        show(fig)

    return fig, end_date_str


if __name__ == '__main__':
    # execute only if run as a script
    fig, end_date_str = usgdp_npp()
