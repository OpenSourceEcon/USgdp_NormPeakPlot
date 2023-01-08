"""
Tests of usgdp_npp_bokeh.py module

Three main tests:
* make sure that running the module as a script python usgdp_npp_bokeh.py
  results in a saved html file and two csv data files in the correct
  directories
* data files are created with both download_from_internet==True and
  download_from_internet==False.
"""

import pytest
import datetime as dt
from usgdp_npp import usgdp_npp_bokeh as usgdp


# Create function to validate datetime text
def validate(date_text):
    try:
        if date_text != dt.datetime.strptime(date_text, "%Y-%m-%d").strftime(
            "%Y-%m-%d"
        ):
            raise ValueError
        return True
    except ValueError:
        return False


# Test that get_usgdp_data() delivers the right structures and can download
# the data from the internet
def test_get_usgdp_data(end_date_str="2022-11-15", save_data=False):
    data_tuple = usgdp.get_usgdp_data(end_date_str=end_date_str)
    assert len(data_tuple) == 8
    (
        usgdp_pk,
        end_date_str2,
        peak_vals,
        peak_dates,
        rec_label_yr_lst,
        rec_label_yrmth_lst,
        rec_beg_yrmth_lst,
        maxdate_rng_lst,
    ) = data_tuple
    assert usgdp_pk.to_numpy().shape == (53, 46)
    assert end_date_str2 == "2022-07-01"
    assert len(peak_vals) == 15
    assert len(peak_dates) == 15
    assert len(rec_label_yr_lst) == 15
    assert len(rec_label_yrmth_lst) == 15
    assert len(rec_beg_yrmth_lst) == 15
    assert len(maxdate_rng_lst) == 15


# Test that usempl_npp() function returns html figure and valid string and
# saves html figure file and two csv files.
@pytest.mark.parametrize("frwd_qtrs_main", [9])
@pytest.mark.parametrize("bkwd_qtrs_main", [2])
@pytest.mark.parametrize("frwd_qtrs_max", [40])
@pytest.mark.parametrize("bkwd_qtrs_max", [12])
@pytest.mark.parametrize("usgdp_end_date", ["today", "2020-04-01"])
@pytest.mark.parametrize("download_from_internet", [True])
@pytest.mark.parametrize("save_data", [False])
@pytest.mark.parametrize("html_show", [False])
def test_html_fig(
    frwd_qtrs_main,
    bkwd_qtrs_main,
    frwd_qtrs_max,
    bkwd_qtrs_max,
    usgdp_end_date,
    download_from_internet,
    save_data,
    html_show,
):
    # The case when usgdp_end_date == 'today' and download_from_internet ==
    # False must be skipped because we don't have the data saved for every date
    fig, end_date_str = usgdp.usgdp_npp(
        frwd_qtrs_main=frwd_qtrs_main,
        bkwd_qtrs_main=bkwd_qtrs_main,
        frwd_qtrs_max=frwd_qtrs_max,
        bkwd_qtrs_max=bkwd_qtrs_max,
        usgdp_end_date=usgdp_end_date,
        download_from_internet=download_from_internet,
        save_data=save_data,
        html_show=html_show,
    )
    assert fig
    assert validate(end_date_str)
