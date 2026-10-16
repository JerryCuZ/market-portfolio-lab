import unittest
import numpy as np
import pandas as pd
from test_portfolio import frame
from controls import scale_schedule
from signals import trend_filter_schedule

class ControlTests(unittest.TestCase):
    def base(self):
        return pd.DataFrame({'A':[.3,.4], 'B':[.7,.6],
            'decision_date':pd.to_datetime(['2020-01-31','2020-02-28'])},
            index=pd.to_datetime(['2020-02-03','2020-03-02']))

    def test_scalar_zero_and_proportions(self):
        b=self.base(); original=b.copy()
        s=scale_schedule(b,['A','B'],.7)
        np.testing.assert_allclose(s[['A','B']],[[.21,.49],[.28,.42]])
        np.testing.assert_allclose(scale_schedule(b,['A','B'],0)[['A','B']],0)
        pd.testing.assert_frame_equal(b,original)
        np.testing.assert_allclose(scale_schedule(b,['A','B'],1+2e-16)[['A','B']],b[['A','B']])

    def test_alignment_and_invalid_inputs_rejected(self):
        b=self.base()
        for value in [-.1,1.1,np.nan,pd.Series([.5,.5],index=b.index[::-1])]:
            with self.assertRaises(ValueError): scale_schedule(b,['A','B'],value)
        b['decision_date']=b.index
        with self.assertRaises(ValueError): scale_schedule(b,['A','B'],.7)

    def test_dynamic_total_and_future_data_invariance(self):
        dates=pd.bdate_range('2020-01-01',periods=8)
        p=pd.DataFrame({'A':[10,10,12,8,7,15,16,17],'B':[10]*8},index=dates)
        b=pd.DataFrame({'A':[.3,.4],'B':[.7,.6], 'decision_date':dates[[2,6]]},index=dates[[3,7]])
        t,_=trend_filter_schedule(p,b,2)
        s=scale_schedule(b,['A','B'],t[['A','B']].sum(axis=1))
        np.testing.assert_allclose(s[['A','B']].sum(axis=1),t[['A','B']].sum(axis=1))
        changed=p.copy();changed.loc[dates[3]:,'A']*=10
        t2,_=trend_filter_schedule(changed,b,2)
        s2=scale_schedule(b,['A','B'],t2[['A','B']].sum(axis=1))
        pd.testing.assert_series_equal(s.iloc[0],s2.iloc[0])
