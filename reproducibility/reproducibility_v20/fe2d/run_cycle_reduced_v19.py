"""Resume the identical full-geometry cycle using certified QP reduction."""
import argparse
import cycle_contact_v19 as base
from reduced_cycle_contact_v19 import ReducedOperator
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--step',type=float,default=.02);p.add_argument('--h',type=float,default=.35);a=p.parse_args()
    base.Operator=ReducedOperator;base.campaign(a.step,a.h)
