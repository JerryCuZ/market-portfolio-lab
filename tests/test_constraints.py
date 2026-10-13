"""Analytical cap redistribution and decision-time threshold tests."""
import unittest
import numpy as np
import pandas as pd
from test_portfolio import frame
from portfolio import simulate, reconcile
from risk_models import cap_weights


class ConstraintTests(unittest.TestCase):
    def test_cap_redistribution_and_invariants(self):
        w = pd.Series({'A': .7, 'B': .2, 'C': .1})
        out = cap_weights(w, .5)
        np.testing.assert_allclose(out, [.5, 1/3, 1/6])
        np.testing.assert_allclose(cap_weights(out, .5), out)
        np.testing.assert_allclose(cap_weights(w.iloc[::-1], .5).reindex(w.index), out)
        np.testing.assert_allclose(cap_weights(w, 1/3), [1/3]*3)
        with self.assertRaises(ValueError):
            cap_weights(w, .3)

    def fixture(self):
        dates = ['2020-01-30', '2020-01-31', '2020-02-03', '2020-03-02']
        frames = {'A': frame(dates, [100, 110, 300, 300]),
                  'B': frame(dates, [100, 100, 100, 100])}
        schedule = pd.DataFrame({'A': [.5]*3, 'B': [.5]*3,
            'decision_date': pd.to_datetime(['2020-01-29','2020-01-31','2020-02-03'])},
            index=pd.to_datetime([dates[0], dates[2], dates[3]]))
        return frames, schedule

    def test_threshold_prior_close_not_execution_open(self):
        frames, schedule = self.fixture()
        r = simulate(frames, {'A':.5,'B':.5}, cost_bps=0,
                     target_schedule=schedule, rebalance_threshold=.03)
        self.assertFalse(r.daily.rebalance.iloc[2])  # prior gap .02381, opening gap .25
        self.assertTrue(r.daily.rebalance.iloc[3])
        self.assertAlmostEqual(r.daily.decision_weight_gap.iloc[2], 11/21-.5)
        reconcile(r)
        changed = {s:f.copy() for s,f in frames.items()}
        changed['A'].loc[pd.Timestamp('2020-02-03'), ['Open','Close']] = 900
        other = simulate(changed, {'A':.5,'B':.5}, target_schedule=schedule, rebalance_threshold=.03)
        self.assertFalse(other.daily.rebalance.iloc[2])

    def test_zero_threshold_matches_when_gaps_nonzero_and_rejects_stale(self):
        frames, schedule = self.fixture()
        a = simulate(frames, {'A':.5,'B':.5}, target_schedule=schedule)
        b = simulate(frames, {'A':.5,'B':.5}, target_schedule=schedule, rebalance_threshold=0)
        pd.testing.assert_frame_equal(a.trades, b.trades)
        schedule.iloc[1, schedule.columns.get_loc('decision_date')] = pd.Timestamp('2020-01-30')
        with self.assertRaises(ValueError):
            simulate(frames, {'A':.5,'B':.5}, target_schedule=schedule, rebalance_threshold=.03)
