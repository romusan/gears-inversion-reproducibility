"""Plots of verified interface and material-removal records."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=Path(__file__).resolve().parent;ROOT=BASE.parent;AUD=ROOT/'revision_12_2026-10-23'
def main():
    interface=json.loads((AUD/'interface24_summary.json').read_text());physical=json.loads((AUD/'physical_geometry_summary.json').read_text())
    plt.rcParams.update({'font.size':18})
    fig,axes=plt.subplots(1,2,figsize=(12.5,4.6))
    for r in interface['rows']:axes[0].plot(interface['phases'],r['isolated_signal_um'],'.-',label=f"Pressure step {r['step_mm']:.2f} mm")
    for r in physical['rows']:
        if r['depth_mm']==.05:axes[1].plot(physical['phases'],r['centered_differences_um'],'o-',label=f"Bulk h={r['h_mm']:.2f} mm")
    axes[0].set(title='Fixed-body interface control',ylabel='Dedendum TE (µm)',ylim=(-.06,.4))
    axes[1].set(title='Physical removal of 50 µm',ylabel='TE difference (µm)',ylim=(-.0035,.007))
    for a in axes:a.set_xlabel('Mesh-cycle fraction');a.legend(fontsize=16,loc='upper right');a.grid(alpha=.2)
    fig.tight_layout();fig.savefig(BASE/'assets/fig_controls_v12.png',dpi=210)
if __name__=='__main__':main()
